package com.snakearena.game;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothServerSocket;
import android.bluetooth.BluetoothSocket;
import android.content.pm.PackageManager;
import android.os.Build;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class LocalNetworkBridge {
    public static final int BLUETOOTH_PERMISSION_REQUEST = 4242;
    private static final int WIFI_PORT = 45875;
    private static final UUID BT_UUID = UUID.fromString("b721dffc-f4af-4d9b-bdc1-0db12dfed441");
    private static final String BT_SERVICE = "SnakeArenaLocal";

    private final Activity activity;
    private final WebView webView;
    private final ExecutorService io = Executors.newCachedThreadPool();
    private final Object sendLock = new Object();

    private volatile ServerSocket wifiServer;
    private volatile Socket wifiSocket;
    private volatile BluetoothServerSocket bluetoothServer;
    private volatile BluetoothSocket bluetoothSocket;
    private volatile BufferedReader reader;
    private volatile BufferedWriter writer;
    private volatile boolean closing = false;

    private String pendingBluetoothAction = null;
    private String pendingBluetoothAddress = null;

    public LocalNetworkBridge(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
    }

    @JavascriptInterface
    public String getWifiAddress() {
        return findLocalIpv4();
    }

    @JavascriptInterface
    public void hostWifi() {
        io.execute(() -> {
            closeTransport(false);
            closing = false;
            try {
                wifiServer = new ServerSocket();
                wifiServer.setReuseAddress(true);
                wifiServer.bind(new InetSocketAddress(WIFI_PORT));
                emitStatus("wifi", "hosting", findLocalIpv4(), null);
                Socket accepted = wifiServer.accept();
                if (closing) {
                    safeClose(accepted);
                    return;
                }
                wifiSocket = accepted;
                wifiSocket.setTcpNoDelay(true);
                wifiSocket.setKeepAlive(true);
                setupStreams(wifiSocket);
                emitStatus("wifi", "connected", accepted.getInetAddress().getHostAddress(), null);
                readLoop("wifi");
            } catch (Exception e) {
                if (!closing) emitStatus("wifi", "error", null, friendlyError(e));
            } finally {
                safeClose(wifiServer);
                wifiServer = null;
            }
        });
    }

    @JavascriptInterface
    public void joinWifi(String host) {
        final String cleanHost = host == null ? "" : host.trim();
        if (cleanHost.isEmpty() || cleanHost.length() > 80) {
            emitStatus("wifi", "error", null, "Enter the host phone IP address.");
            return;
        }
        io.execute(() -> {
            closeTransport(false);
            closing = false;
            try {
                Socket socket = new Socket();
                socket.connect(new InetSocketAddress(cleanHost, WIFI_PORT), 7000);
                socket.setTcpNoDelay(true);
                socket.setKeepAlive(true);
                wifiSocket = socket;
                setupStreams(socket);
                emitStatus("wifi", "connected", cleanHost, null);
                readLoop("wifi");
            } catch (Exception e) {
                if (!closing) emitStatus("wifi", "error", null, friendlyError(e));
            }
        });
    }

    @JavascriptInterface
    public String getPairedBluetoothDevices() {
        if (!ensureBluetoothPermission("list", null)) return "PERMISSION_REQUIRED";
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) return "UNSUPPORTED";
            if (!adapter.isEnabled()) return "DISABLED";
            JSONArray array = new JSONArray();
            Set<BluetoothDevice> bonded = adapter.getBondedDevices();
            for (BluetoothDevice device : bonded) {
                JSONObject item = new JSONObject();
                item.put("name", safeDeviceName(device));
                item.put("address", device.getAddress());
                array.put(item);
            }
            return array.toString();
        } catch (Exception e) {
            return "ERROR";
        }
    }

    @JavascriptInterface
    public void hostBluetooth() {
        if (!ensureBluetoothPermission("host", null)) return;
        startBluetoothHost();
    }

    @JavascriptInterface
    public void joinBluetooth(String address) {
        String clean = address == null ? "" : address.trim();
        if (clean.isEmpty()) {
            emitStatus("bluetooth", "error", null, "Choose a paired phone first.");
            return;
        }
        if (!ensureBluetoothPermission("join", clean)) return;
        startBluetoothJoin(clean);
    }

    @JavascriptInterface
    public void send(String message) {
        if (message == null || message.length() > 65536) return;
        io.execute(() -> {
            try {
                BufferedWriter current = writer;
                if (current == null) return;
                synchronized (sendLock) {
                    current.write(message);
                    current.write('\n');
                    current.flush();
                }
            } catch (Exception e) {
                if (!closing) emitStatus("local", "disconnected", null, "Connection lost.");
                closeTransport(false);
            }
        });
    }

    @JavascriptInterface
    public void disconnect() {
        io.execute(() -> closeTransport(true));
    }

    public void onPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode != BLUETOOTH_PERMISSION_REQUEST) return;
        boolean granted = true;
        for (int result : grantResults) {
            if (result != PackageManager.PERMISSION_GRANTED) {
                granted = false;
                break;
            }
        }
        if (!granted) {
            pendingBluetoothAction = null;
            pendingBluetoothAddress = null;
            emitStatus("bluetooth", "permission_denied", null, "Bluetooth permission was not granted.");
            return;
        }
        final String action = pendingBluetoothAction;
        final String address = pendingBluetoothAddress;
        pendingBluetoothAction = null;
        pendingBluetoothAddress = null;
        emitStatus("bluetooth", "permission_granted", null, null);
        if ("host".equals(action)) startBluetoothHost();
        else if ("join".equals(action) && address != null) startBluetoothJoin(address);
    }

    public void shutdown() {
        closeTransport(false);
        io.shutdownNow();
    }

    private boolean ensureBluetoothPermission(String action, String address) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true;
        if (activity.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED) {
            return true;
        }
        pendingBluetoothAction = action;
        pendingBluetoothAddress = address;
        activity.runOnUiThread(() -> activity.requestPermissions(
            new String[]{Manifest.permission.BLUETOOTH_CONNECT},
            BLUETOOTH_PERMISSION_REQUEST
        ));
        emitStatus("bluetooth", "permission_requested", null, null);
        return false;
    }

    private void startBluetoothHost() {
        io.execute(() -> {
            closeTransport(false);
            closing = false;
            try {
                BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
                if (adapter == null) {
                    emitStatus("bluetooth", "error", null, "Bluetooth is not supported on this phone.");
                    return;
                }
                if (!adapter.isEnabled()) {
                    emitStatus("bluetooth", "error", null, "Turn on Bluetooth first.");
                    return;
                }
                bluetoothServer = adapter.listenUsingRfcommWithServiceRecord(BT_SERVICE, BT_UUID);
                emitStatus("bluetooth", "hosting", null, "Waiting for a paired phone…");
                BluetoothSocket accepted = bluetoothServer.accept();
                if (closing) {
                    safeClose(accepted);
                    return;
                }
                bluetoothSocket = accepted;
                setupStreams(accepted);
                emitStatus("bluetooth", "connected", safeDeviceName(accepted.getRemoteDevice()), null);
                readLoop("bluetooth");
            } catch (Exception e) {
                if (!closing) emitStatus("bluetooth", "error", null, friendlyError(e));
            } finally {
                safeClose(bluetoothServer);
                bluetoothServer = null;
            }
        });
    }

    private void startBluetoothJoin(String address) {
        io.execute(() -> {
            closeTransport(false);
            closing = false;
            try {
                BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
                if (adapter == null) {
                    emitStatus("bluetooth", "error", null, "Bluetooth is not supported on this phone.");
                    return;
                }
                if (!adapter.isEnabled()) {
                    emitStatus("bluetooth", "error", null, "Turn on Bluetooth first.");
                    return;
                }
                BluetoothDevice device = adapter.getRemoteDevice(address);
                BluetoothSocket socket = device.createRfcommSocketToServiceRecord(BT_UUID);
                socket.connect();
                bluetoothSocket = socket;
                setupStreams(socket);
                emitStatus("bluetooth", "connected", safeDeviceName(device), null);
                readLoop("bluetooth");
            } catch (Exception e) {
                if (!closing) emitStatus("bluetooth", "error", null, friendlyError(e));
            }
        });
    }

    private void setupStreams(Socket socket) throws IOException {
        reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
        writer = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));
    }

    private void setupStreams(BluetoothSocket socket) throws IOException {
        reader = new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
        writer = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));
    }

    private void readLoop(String transport) {
        try {
            String line;
            while (!closing && reader != null && (line = reader.readLine()) != null) {
                if (line.length() <= 65536) emitMessage(transport, line);
            }
            if (!closing) emitStatus(transport, "disconnected", null, "Other player disconnected.");
        } catch (Exception e) {
            if (!closing) emitStatus(transport, "disconnected", null, friendlyError(e));
        } finally {
            closeTransport(false);
        }
    }

    private void closeTransport(boolean notify) {
        closing = true;
        reader = null;
        writer = null;
        safeClose(wifiSocket);
        safeClose(wifiServer);
        safeClose(bluetoothSocket);
        safeClose(bluetoothServer);
        wifiSocket = null;
        wifiServer = null;
        bluetoothSocket = null;
        bluetoothServer = null;
        if (notify) emitStatus("local", "closed", null, null);
    }

    private void emitMessage(String transport, String message) {
        try {
            JSONObject event = new JSONObject();
            event.put("type", "message");
            event.put("transport", transport);
            event.put("data", message);
            emit(event.toString());
        } catch (Exception ignored) {
        }
    }

    private void emitStatus(String transport, String state, String address, String message) {
        try {
            JSONObject event = new JSONObject();
            event.put("type", "status");
            event.put("transport", transport);
            event.put("state", state);
            if (address != null) event.put("address", address);
            if (message != null) event.put("message", message);
            emit(event.toString());
        } catch (Exception ignored) {
        }
    }

    private void emit(String json) {
        final String quoted = JSONObject.quote(json);
        activity.runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript("window.onLocalNetEvent&&window.onLocalNetEvent(" + quoted + ")", null);
            }
        });
    }

    private String findLocalIpv4() {
        try {
            for (NetworkInterface network : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!network.isUp() || network.isLoopback()) continue;
                for (InetAddress address : Collections.list(network.getInetAddresses())) {
                    if (address instanceof Inet4Address && !address.isLoopbackAddress() && address.isSiteLocalAddress()) {
                        return address.getHostAddress();
                    }
                }
            }
        } catch (Exception ignored) {
        }
        return "Unavailable";
    }

    private String safeDeviceName(BluetoothDevice device) {
        try {
            String name = device == null ? null : device.getName();
            return name == null || name.trim().isEmpty() ? "Paired Android device" : name;
        } catch (Exception e) {
            return "Paired Android device";
        }
    }

    private String friendlyError(Exception e) {
        String message = e.getMessage();
        if (message == null || message.trim().isEmpty()) return "Local connection failed.";
        if (message.length() > 120) message = message.substring(0, 120);
        return message;
    }

    private void safeClose(Socket socket) {
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
    }

    private void safeClose(ServerSocket socket) {
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
    }

    private void safeClose(BluetoothSocket socket) {
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
    }

    private void safeClose(BluetoothServerSocket socket) {
        try { if (socket != null) socket.close(); } catch (Exception ignored) {}
    }
}
