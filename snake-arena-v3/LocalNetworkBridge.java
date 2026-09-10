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
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.net.ConnectException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.InterfaceAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public class LocalNetworkBridge {
    public static final int BLUETOOTH_PERMISSION_REQUEST = 4242;
    private static final int WIFI_PORT = 45875;
    private static final int DISCOVERY_PORT = 45876;
    private static final String DISCOVER_MAGIC = "SNAKE_ARENA_DISCOVER_V41";
    private static final String HOST_MAGIC = "SNAKE_ARENA_HOST_V41";
    private static final UUID BT_UUID = UUID.fromString("b721dffc-f4af-4d9b-bdc1-0db12dfed441");
    private static final String BT_SERVICE = "SnakeArenaLocal";

    private final Activity activity;
    private final WebView webView;
    private final ExecutorService io = Executors.newCachedThreadPool();
    private final Object transportLock = new Object();
    private final Object sendLock = new Object();
    private final AtomicInteger generation = new AtomicInteger(0);

    private volatile ServerSocket wifiServer;
    private volatile Socket wifiSocket;
    private volatile BluetoothServerSocket bluetoothServer;
    private volatile BluetoothSocket bluetoothSocket;
    private volatile DatagramSocket discoveryResponder;
    private volatile BufferedReader reader;
    private volatile BufferedWriter writer;

    private String pendingBluetoothAction = null;
    private String pendingBluetoothAddress = null;

    public LocalNetworkBridge(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
    }

    @JavascriptInterface
    public String getWifiAddress() {
        List<String> addresses = getLocalIpv4Candidates();
        return addresses.isEmpty() ? "Unavailable" : addresses.get(0);
    }

    @JavascriptInterface
    public String getWifiAddresses() {
        try {
            JSONArray array = new JSONArray();
            for (String address : getLocalIpv4Candidates()) array.put(address);
            return array.toString();
        } catch (Exception e) {
            return "[]";
        }
    }

    @JavascriptInterface
    public void discoverWifiHost() {
        io.execute(this::discoverWifiHostInternal);
    }

    @JavascriptInterface
    public void hostWifi() {
        final int gen = generation.incrementAndGet();
        io.execute(() -> startWifiHost(gen));
    }

    @JavascriptInterface
    public void joinWifi(String host) {
        String cleanHost = host == null ? "" : host.trim();
        if (cleanHost.startsWith("http://")) cleanHost = cleanHost.substring(7);
        if (cleanHost.startsWith("https://")) cleanHost = cleanHost.substring(8);
        int slash = cleanHost.indexOf('/');
        if (slash >= 0) cleanHost = cleanHost.substring(0, slash);
        int colon = cleanHost.lastIndexOf(':');
        if (colon > 0 && cleanHost.indexOf(':') == colon) cleanHost = cleanHost.substring(0, colon);
        final String target = cleanHost.trim();
        if (target.isEmpty() || target.length() > 80) {
            emitStatus("wifi", "error", null, "Enter the host phone IP address.");
            return;
        }
        final int gen = generation.incrementAndGet();
        io.execute(() -> startWifiJoin(gen, target));
    }

    @JavascriptInterface
    public String getPairedBluetoothDevices() {
        if (!ensureBluetoothPermission("list", null)) return "PERMISSION_REQUIRED";
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) return "UNSUPPORTED";
            if (!adapter.isEnabled()) return "DISABLED";
            List<BluetoothDevice> devices = new ArrayList<>(adapter.getBondedDevices());
            Collections.sort(devices, (a, b) -> safeDeviceName(a).compareToIgnoreCase(safeDeviceName(b)));
            JSONArray array = new JSONArray();
            for (BluetoothDevice device : devices) {
                JSONObject item = new JSONObject();
                item.put("name", safeDeviceName(device));
                item.put("address", device.getAddress());
                array.put(item);
            }
            return array.toString();
        } catch (SecurityException e) {
            return "PERMISSION_REQUIRED";
        } catch (Exception e) {
            return "ERROR";
        }
    }

    @JavascriptInterface
    public void hostBluetooth() {
        if (!ensureBluetoothPermission("host", null)) return;
        final int gen = generation.incrementAndGet();
        io.execute(() -> startBluetoothHost(gen));
    }

    @JavascriptInterface
    public void joinBluetooth(String address) {
        final String clean = address == null ? "" : address.trim();
        if (clean.isEmpty()) {
            emitStatus("bluetooth", "error", null, "Choose a paired phone first.");
            return;
        }
        if (!ensureBluetoothPermission("join", clean)) return;
        final int gen = generation.incrementAndGet();
        io.execute(() -> startBluetoothJoin(gen, clean));
    }

    @JavascriptInterface
    public void send(String message) {
        if (message == null || message.length() > 65536) return;
        final int gen = generation.get();
        io.execute(() -> {
            BufferedWriter current;
            synchronized (transportLock) {
                if (gen != generation.get()) return;
                current = writer;
            }
            if (current == null) return;
            try {
                synchronized (sendLock) {
                    current.write(message);
                    current.write('\n');
                    current.flush();
                }
            } catch (Exception e) {
                if (gen == generation.get()) {
                    emitStatusIfCurrent(gen, "local", "disconnected", null, "Connection lost while sending data.");
                    closeCurrentGeneration(gen);
                }
            }
        });
    }

    @JavascriptInterface
    public void disconnect() {
        final int gen = generation.incrementAndGet();
        io.execute(() -> {
            synchronized (transportLock) {
                if (gen != generation.get()) return;
                closeTransportLocked();
            }
            emitStatusIfCurrent(gen, "local", "closed", null, null);
        });
    }

    public void onPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode != BLUETOOTH_PERMISSION_REQUEST) return;
        boolean granted = grantResults != null && grantResults.length > 0;
        if (grantResults != null) {
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    granted = false;
                    break;
                }
            }
        }
        final String action = pendingBluetoothAction;
        final String address = pendingBluetoothAddress;
        pendingBluetoothAction = null;
        pendingBluetoothAddress = null;
        if (!granted) {
            emitStatus("bluetooth", "permission_denied", null, "Bluetooth permission was not granted.");
            return;
        }
        emitStatus("bluetooth", "permission_granted", null, null);
        if ("host".equals(action)) {
            final int gen = generation.incrementAndGet();
            io.execute(() -> startBluetoothHost(gen));
        } else if ("join".equals(action) && address != null) {
            final int gen = generation.incrementAndGet();
            io.execute(() -> startBluetoothJoin(gen, address));
        }
    }

    public void shutdown() {
        generation.incrementAndGet();
        synchronized (transportLock) {
            closeTransportLocked();
        }
        io.shutdownNow();
    }

    private boolean ensureBluetoothPermission(String action, String address) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return true;
        if (activity.checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED) return true;
        pendingBluetoothAction = action;
        pendingBluetoothAddress = address;
        activity.runOnUiThread(() -> activity.requestPermissions(
            new String[]{Manifest.permission.BLUETOOTH_CONNECT},
            BLUETOOTH_PERMISSION_REQUEST
        ));
        emitStatus("bluetooth", "permission_requested", null, null);
        return false;
    }

    private void startWifiHost(int gen) {
        ServerSocket localServer = null;
        try {
            if (!prepareGeneration(gen)) return;
            localServer = new ServerSocket();
            localServer.setReuseAddress(true);
            localServer.bind(new InetSocketAddress("0.0.0.0", WIFI_PORT));
            synchronized (transportLock) {
                if (gen != generation.get()) {
                    safeClose(localServer);
                    return;
                }
                wifiServer = localServer;
            }
            startDiscoveryResponder(gen);
            emitStatusIfCurrent(gen, "wifi", "hosting", getWifiAddress(), "Port " + WIFI_PORT + " ready.");
            Socket accepted = localServer.accept();
            if (gen != generation.get()) {
                safeClose(accepted);
                return;
            }
            accepted.setTcpNoDelay(true);
            accepted.setKeepAlive(true);
            accepted.setSoTimeout(10000);
            synchronized (transportLock) {
                if (gen != generation.get()) {
                    safeClose(accepted);
                    return;
                }
                wifiSocket = accepted;
                if (wifiServer == localServer) wifiServer = null;
                safeClose(localServer);
                stopDiscoveryResponderLocked();
            }
            activateConnection(gen, "wifi", accepted.getInputStream(), accepted.getOutputStream(),
                () -> safeClose(accepted), accepted.getInetAddress().getHostAddress());
        } catch (Exception e) {
            if (gen == generation.get()) emitStatusIfCurrent(gen, "wifi", "error", null, friendlyWifiError(e));
        } finally {
            safeClose(localServer);
            synchronized (transportLock) {
                if (wifiServer == localServer) wifiServer = null;
            }
        }
    }

    private void startWifiJoin(int gen, String host) {
        Socket socket = new Socket();
        try {
            if (!prepareGeneration(gen)) return;
            emitStatusIfCurrent(gen, "wifi", "connecting", host, "Connecting to host…");
            socket.connect(new InetSocketAddress(host, WIFI_PORT), 6500);
            if (gen != generation.get()) {
                safeClose(socket);
                return;
            }
            socket.setTcpNoDelay(true);
            socket.setKeepAlive(true);
            socket.setSoTimeout(10000);
            synchronized (transportLock) {
                if (gen != generation.get()) {
                    safeClose(socket);
                    return;
                }
                wifiSocket = socket;
            }
            activateConnection(gen, "wifi", socket.getInputStream(), socket.getOutputStream(),
                () -> safeClose(socket), host);
        } catch (Exception e) {
            safeClose(socket);
            if (gen == generation.get()) emitStatusIfCurrent(gen, "wifi", "error", host, friendlyWifiError(e));
        }
    }

    private void startBluetoothHost(int gen) {
        BluetoothServerSocket localServer = null;
        try {
            if (!prepareGeneration(gen)) return;
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) {
                emitStatusIfCurrent(gen, "bluetooth", "error", null, "Bluetooth is not supported on this phone.");
                return;
            }
            if (!adapter.isEnabled()) {
                emitStatusIfCurrent(gen, "bluetooth", "error", null, "Turn on Bluetooth first.");
                return;
            }
            localServer = adapter.listenUsingInsecureRfcommWithServiceRecord(BT_SERVICE, BT_UUID);
            synchronized (transportLock) {
                if (gen != generation.get()) {
                    safeClose(localServer);
                    return;
                }
                bluetoothServer = localServer;
            }
            emitStatusIfCurrent(gen, "bluetooth", "hosting", null, "Bluetooth host ready. Waiting for the selected paired phone…");
            BluetoothSocket accepted = localServer.accept();
            if (gen != generation.get()) {
                safeClose(accepted);
                return;
            }
            synchronized (transportLock) {
                if (gen != generation.get()) {
                    safeClose(accepted);
                    return;
                }
                bluetoothSocket = accepted;
                if (bluetoothServer == localServer) bluetoothServer = null;
                safeClose(localServer);
            }
            String remote = safeDeviceName(accepted.getRemoteDevice());
            activateConnection(gen, "bluetooth", accepted.getInputStream(), accepted.getOutputStream(),
                () -> safeClose(accepted), remote);
        } catch (SecurityException e) {
            if (gen == generation.get()) emitStatusIfCurrent(gen, "bluetooth", "error", null, "Bluetooth permission is required.");
        } catch (Exception e) {
            if (gen == generation.get()) emitStatusIfCurrent(gen, "bluetooth", "error", null, friendlyBluetoothError(e));
        } finally {
            safeClose(localServer);
            synchronized (transportLock) {
                if (bluetoothServer == localServer) bluetoothServer = null;
            }
        }
    }

    private void startBluetoothJoin(int gen, String address) {
        BluetoothSocket socket = null;
        try {
            if (!prepareGeneration(gen)) return;
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) {
                emitStatusIfCurrent(gen, "bluetooth", "error", null, "Bluetooth is not supported on this phone.");
                return;
            }
            if (!adapter.isEnabled()) {
                emitStatusIfCurrent(gen, "bluetooth", "error", null, "Turn on Bluetooth first.");
                return;
            }
            BluetoothDevice device = adapter.getRemoteDevice(address);
            emitStatusIfCurrent(gen, "bluetooth", "connecting", safeDeviceName(device), "Connecting to paired phone…");
            socket = device.createInsecureRfcommSocketToServiceRecord(BT_UUID);
            final BluetoothSocket current = socket;
            synchronized (transportLock) {
                if (gen != generation.get()) {
                    safeClose(current);
                    return;
                }
                bluetoothSocket = current;
            }
            current.connect();
            if (gen != generation.get()) {
                safeClose(current);
                return;
            }
            activateConnection(gen, "bluetooth", current.getInputStream(), current.getOutputStream(),
                () -> safeClose(current), safeDeviceName(device));
        } catch (SecurityException e) {
            safeClose(socket);
            if (gen == generation.get()) emitStatusIfCurrent(gen, "bluetooth", "error", null, "Bluetooth permission is required.");
        } catch (Exception e) {
            safeClose(socket);
            if (gen == generation.get()) emitStatusIfCurrent(gen, "bluetooth", "error", null, friendlyBluetoothError(e));
        }
    }

    private boolean prepareGeneration(int gen) {
        synchronized (transportLock) {
            if (gen != generation.get()) return false;
            closeTransportLocked();
            return gen == generation.get();
        }
    }

    private void activateConnection(
        int gen,
        String transport,
        InputStream input,
        OutputStream output,
        Runnable closeSocket,
        String remoteLabel
    ) throws Exception {
        final BufferedReader localReader = new BufferedReader(new InputStreamReader(input, StandardCharsets.UTF_8));
        final BufferedWriter localWriter = new BufferedWriter(new OutputStreamWriter(output, StandardCharsets.UTF_8));
        synchronized (transportLock) {
            if (gen != generation.get()) {
                closeSocket.run();
                return;
            }
            reader = localReader;
            writer = localWriter;
        }
        emitStatusIfCurrent(gen, transport, "connected", remoteLabel, "Connected. Exchanging player data…");
        readLoop(gen, transport, localReader, localWriter, closeSocket);
    }

    private void readLoop(
        int gen,
        String transport,
        BufferedReader localReader,
        BufferedWriter localWriter,
        Runnable closeSocket
    ) {
        String disconnectMessage = "Other player disconnected.";
        try {
            String line;
            while (gen == generation.get() && (line = localReader.readLine()) != null) {
                if (line.length() <= 65536) emitMessageIfCurrent(gen, transport, line);
            }
        } catch (SocketTimeoutException e) {
            disconnectMessage = "Connection timed out. Keep both phones awake and nearby.";
        } catch (Exception e) {
            disconnectMessage = friendlyError(e);
        } finally {
            closeSocket.run();
            boolean current;
            synchronized (transportLock) {
                current = gen == generation.get();
                if (current) {
                    if (reader == localReader) reader = null;
                    if (writer == localWriter) writer = null;
                    if ("wifi".equals(transport)) wifiSocket = null;
                    if ("bluetooth".equals(transport)) bluetoothSocket = null;
                }
            }
            if (current) emitStatusIfCurrent(gen, transport, "disconnected", null, disconnectMessage);
        }
    }

    private void discoverWifiHostInternal() {
        emitStatus("wifi", "discovering", null, "Searching for a Snake Arena host on this Wi-Fi/hotspot…");
        DatagramSocket socket = null;
        try {
            socket = new DatagramSocket();
            socket.setBroadcast(true);
            socket.setSoTimeout(800);
            byte[] request = DISCOVER_MAGIC.getBytes(StandardCharsets.UTF_8);
            Set<String> sent = new HashSet<>();
            sendDiscovery(socket, request, InetAddress.getByName("255.255.255.255"), sent);
            for (NetworkInterface network : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!network.isUp() || network.isLoopback()) continue;
                for (InterfaceAddress interfaceAddress : network.getInterfaceAddresses()) {
                    InetAddress broadcast = interfaceAddress.getBroadcast();
                    if (broadcast != null) sendDiscovery(socket, request, broadcast, sent);
                }
            }
            long deadline = System.currentTimeMillis() + 3200;
            byte[] buf = new byte[128];
            while (System.currentTimeMillis() < deadline) {
                try {
                    DatagramPacket response = new DatagramPacket(buf, buf.length);
                    socket.receive(response);
                    String message = new String(response.getData(), response.getOffset(), response.getLength(), StandardCharsets.UTF_8);
                    if (message.startsWith(HOST_MAGIC)) {
                        emitStatus("wifi", "discovered", response.getAddress().getHostAddress(), "Host found automatically.");
                        return;
                    }
                } catch (SocketTimeoutException ignored) {
                }
            }
            emitStatus("wifi", "discovery_failed", null, "No host found automatically. You can still enter the host IP manually.");
        } catch (Exception e) {
            emitStatus("wifi", "discovery_failed", null, friendlyWifiError(e));
        } finally {
            if (socket != null) socket.close();
        }
    }

    private void sendDiscovery(DatagramSocket socket, byte[] request, InetAddress address, Set<String> sent) {
        try {
            String key = address.getHostAddress();
            if (!sent.add(key)) return;
            DatagramPacket packet = new DatagramPacket(request, request.length, address, DISCOVERY_PORT);
            socket.send(packet);
        } catch (Exception ignored) {
        }
    }

    private void startDiscoveryResponder(final int gen) {
        io.execute(() -> {
            DatagramSocket socket = null;
            try {
                socket = new DatagramSocket(null);
                socket.setReuseAddress(true);
                socket.bind(new InetSocketAddress("0.0.0.0", DISCOVERY_PORT));
                socket.setSoTimeout(900);
                synchronized (transportLock) {
                    if (gen != generation.get()) {
                        socket.close();
                        return;
                    }
                    discoveryResponder = socket;
                }
                byte[] buf = new byte[128];
                while (gen == generation.get() && !socket.isClosed()) {
                    try {
                        DatagramPacket request = new DatagramPacket(buf, buf.length);
                        socket.receive(request);
                        String message = new String(request.getData(), request.getOffset(), request.getLength(), StandardCharsets.UTF_8);
                        if (DISCOVER_MAGIC.equals(message)) {
                            byte[] response = HOST_MAGIC.getBytes(StandardCharsets.UTF_8);
                            DatagramPacket reply = new DatagramPacket(response, response.length, request.getAddress(), request.getPort());
                            socket.send(reply);
                        }
                    } catch (SocketTimeoutException ignored) {
                    }
                }
            } catch (Exception ignored) {
            } finally {
                if (socket != null) socket.close();
                synchronized (transportLock) {
                    if (discoveryResponder == socket) discoveryResponder = null;
                }
            }
        });
    }

    private void closeCurrentGeneration(int gen) {
        synchronized (transportLock) {
            if (gen != generation.get()) return;
            closeTransportLocked();
        }
    }

    private void closeTransportLocked() {
        reader = null;
        writer = null;
        safeClose(wifiSocket);
        safeClose(wifiServer);
        safeClose(bluetoothSocket);
        safeClose(bluetoothServer);
        stopDiscoveryResponderLocked();
        wifiSocket = null;
        wifiServer = null;
        bluetoothSocket = null;
        bluetoothServer = null;
    }

    private void stopDiscoveryResponderLocked() {
        if (discoveryResponder != null) {
            discoveryResponder.close();
            discoveryResponder = null;
        }
    }

    private void emitMessageIfCurrent(int gen, String transport, String message) {
        if (gen != generation.get()) return;
        try {
            JSONObject event = new JSONObject();
            event.put("type", "message");
            event.put("transport", transport);
            event.put("generation", gen);
            event.put("data", message);
            emit(event.toString());
        } catch (Exception ignored) {
        }
    }

    private void emitStatusIfCurrent(int gen, String transport, String state, String address, String message) {
        if (gen != generation.get()) return;
        emitStatusWithGeneration(gen, transport, state, address, message);
    }

    private void emitStatus(String transport, String state, String address, String message) {
        emitStatusWithGeneration(generation.get(), transport, state, address, message);
    }

    private void emitStatusWithGeneration(int gen, String transport, String state, String address, String message) {
        try {
            JSONObject event = new JSONObject();
            event.put("type", "status");
            event.put("transport", transport);
            event.put("state", state);
            event.put("generation", gen);
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

    private List<String> getLocalIpv4Candidates() {
        List<String[]> candidates = new ArrayList<>();
        try {
            for (NetworkInterface network : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!network.isUp() || network.isLoopback()) continue;
                String name = network.getName() == null ? "" : network.getName().toLowerCase(Locale.US);
                int score = interfaceScore(name);
                for (InetAddress address : Collections.list(network.getInetAddresses())) {
                    if (!(address instanceof Inet4Address) || address.isLoopbackAddress() || !address.isSiteLocalAddress()) continue;
                    candidates.add(new String[]{String.valueOf(score), address.getHostAddress()});
                }
            }
        } catch (Exception ignored) {
        }
        Collections.sort(candidates, (a, b) -> Integer.compare(Integer.parseInt(b[0]), Integer.parseInt(a[0])));
        List<String> out = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        for (String[] candidate : candidates) if (seen.add(candidate[1])) out.add(candidate[1]);
        return out;
    }

    private int interfaceScore(String name) {
        if (name.startsWith("wlan") || name.contains("wifi") || name.startsWith("ap") || name.startsWith("swlan")) return 100;
        if (name.startsWith("eth")) return 80;
        if (name.startsWith("tun") || name.contains("vpn")) return 5;
        if (name.startsWith("rmnet") || name.startsWith("pdp") || name.contains("cell")) return 1;
        return 40;
    }

    private String safeDeviceName(BluetoothDevice device) {
        try {
            String name = device == null ? null : device.getName();
            return name == null || name.trim().isEmpty() ? "Paired Android device" : name;
        } catch (Exception e) {
            return "Paired Android device";
        }
    }

    private String friendlyWifiError(Exception e) {
        if (e instanceof ConnectException) return "Host not reachable. Keep HOST GAME open and make sure both phones are on the same Wi-Fi/hotspot.";
        if (e instanceof SocketTimeoutException) return "Wi-Fi connection timed out. Check the host IP and keep both phones on the same network.";
        return friendlyError(e);
    }

    private String friendlyBluetoothError(Exception e) {
        String raw = e.getMessage();
        if (raw != null && raw.toLowerCase(Locale.US).contains("read failed")) {
            return "Bluetooth connection failed. Pair both phones in Android Settings, then host first and join from the paired list.";
        }
        return "Bluetooth connection failed. " + friendlyError(e);
    }

    private String friendlyError(Exception e) {
        String message = e == null ? null : e.getMessage();
        if (message == null || message.trim().isEmpty()) return "Local connection failed.";
        if (message.length() > 140) message = message.substring(0, 140);
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
