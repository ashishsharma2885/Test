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
import java.io.Closeable;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public class LocalNetworkBridge {
    public static final int BLUETOOTH_PERMISSION_REQUEST = 4242;
    private static final int WIFI_PORT = 45875;
    private static final int MAX_REMOTE_PLAYERS = 3;
    private static final UUID BT_UUID = UUID.fromString("b721dffc-f4af-4d9b-bdc1-0db12dfed441");
    private static final String BT_SERVICE = "SnakeArenaLocalRoom";

    private final Activity activity;
    private final WebView webView;
    private final ExecutorService io = Executors.newCachedThreadPool();
    private final Object lifecycleLock = new Object();
    private final Object sendLock = new Object();
    private final AtomicInteger generation = new AtomicInteger(0);
    private final AtomicInteger peerSequence = new AtomicInteger(0);
    private final ConcurrentHashMap<String, Peer> hostPeers = new ConcurrentHashMap<>();

    private volatile ServerSocket wifiServer;
    private volatile BluetoothServerSocket bluetoothServer;
    private volatile Peer upstream;
    private volatile boolean hostMode = false;
    private volatile String activeTransport = null;
    private volatile boolean destroyed = false;

    private String pendingBluetoothAction = null;
    private String pendingBluetoothAddress = null;

    private static class Peer {
        final String id;
        final String label;
        final String transport;
        final Closeable socket;
        final BufferedReader reader;
        final BufferedWriter writer;
        volatile boolean closed = false;

        Peer(String id, String label, String transport, Closeable socket, BufferedReader reader, BufferedWriter writer) {
            this.id = id;
            this.label = label;
            this.transport = transport;
            this.socket = socket;
            this.reader = reader;
            this.writer = writer;
        }
    }

    public LocalNetworkBridge(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
    }

    @JavascriptInterface
    public String getWifiAddress() {
        return findBestLocalIpv4();
    }

    @JavascriptInterface
    public int getConnectedPeerCount() {
        if (hostMode) return hostPeers.size();
        Peer p = upstream;
        return p != null && !p.closed ? 1 : 0;
    }

    @JavascriptInterface
    public void hostWifi() {
        final int gen = beginTransport("wifi", true);
        io.execute(() -> runWifiHost(gen));
    }

    @JavascriptInterface
    public void joinWifi(String host) {
        final String cleanHost = host == null ? "" : host.trim();
        if (!isValidHost(cleanHost)) {
            emitStatus("wifi", "error", null, "Enter a valid host IP address.", null, null);
            return;
        }
        final int gen = beginTransport("wifi", false);
        io.execute(() -> runWifiJoin(gen, cleanHost));
    }

    @JavascriptInterface
    public String getPairedBluetoothDevices() {
        if (!ensureBluetoothPermission("list", null)) return "PERMISSION_REQUIRED";
        return pairedBluetoothJson();
    }

    @JavascriptInterface
    public void hostBluetooth() {
        if (!ensureBluetoothPermission("host", null)) return;
        startBluetoothHostAfterPermission();
    }

    @JavascriptInterface
    public void joinBluetooth(String address) {
        final String clean = address == null ? "" : address.trim();
        if (clean.isEmpty()) {
            emitStatus("bluetooth", "error", null, "Choose a paired host phone first.", null, null);
            return;
        }
        if (!ensureBluetoothPermission("join", clean)) return;
        startBluetoothJoinAfterPermission(clean);
    }

    @JavascriptInterface
    public void send(String message) {
        if (message == null || message.length() > 65536 || destroyed) return;
        final int gen = generation.get();
        io.execute(() -> {
            if (gen != generation.get()) return;
            if (hostMode) {
                for (Peer peer : new ArrayList<>(hostPeers.values())) writePeer(peer, message, gen);
            } else {
                writePeer(upstream, message, gen);
            }
        });
    }

    @JavascriptInterface
    public void sendTo(String peerId, String message) {
        if (peerId == null || message == null || message.length() > 65536 || destroyed) return;
        final int gen = generation.get();
        io.execute(() -> {
            if (gen != generation.get()) return;
            if (hostMode) writePeer(hostPeers.get(peerId), message, gen);
            else writePeer(upstream, message, gen);
        });
    }

    @JavascriptInterface
    public void disconnectPeer(String peerId) {
        if (!hostMode || peerId == null) return;
        Peer peer = hostPeers.remove(peerId);
        if (peer != null) {
            closePeer(peer);
            emitStatus(peer.transport, "peer_disconnected", null, "Player removed from room.", peer.id, peer.label);
        }
    }

    @JavascriptInterface
    public void disconnect() {
        generation.incrementAndGet();
        closeAll(true);
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
        if (!granted) {
            pendingBluetoothAction = null;
            pendingBluetoothAddress = null;
            emitStatus("bluetooth", "permission_denied", null, "Bluetooth/Nearby devices permission was not granted.", null, null);
            return;
        }

        final String action = pendingBluetoothAction;
        final String address = pendingBluetoothAddress;
        pendingBluetoothAction = null;
        pendingBluetoothAddress = null;
        emitStatus("bluetooth", "permission_granted", null, "Bluetooth permission allowed.", null, null);
        if ("host".equals(action)) startBluetoothHostAfterPermission();
        else if ("join".equals(action) && address != null) startBluetoothJoinAfterPermission(address);
        else if ("list".equals(action)) emitStatus("bluetooth", "paired_ready", null, pairedBluetoothJson(), null, null);
    }

    public void shutdown() {
        destroyed = true;
        generation.incrementAndGet();
        closeAll(false);
        io.shutdownNow();
    }

    private int beginTransport(String transport, boolean asHost) {
        final int gen = generation.incrementAndGet();
        closeAll(false);
        synchronized (lifecycleLock) {
            hostMode = asHost;
            activeTransport = transport;
            peerSequence.set(0);
        }
        return gen;
    }

    private void runWifiHost(int gen) {
        ServerSocket server = null;
        try {
            server = new ServerSocket();
            server.setReuseAddress(true);
            server.bind(new InetSocketAddress(WIFI_PORT));
            synchronized (lifecycleLock) {
                if (!isCurrent(gen, "wifi", true)) {
                    safeClose(server);
                    return;
                }
                wifiServer = server;
            }
            String ip = findBestLocalIpv4();
            emitStatus("wifi", "hosting", ip, "Room is open. Players can join this IP.", null, null);

            while (isCurrent(gen, "wifi", true) && !server.isClosed()) {
                Socket socket = server.accept();
                if (!isCurrent(gen, "wifi", true)) {
                    safeClose(socket);
                    break;
                }
                if (hostPeers.size() >= MAX_REMOTE_PLAYERS) {
                    rejectWifiSocket(socket, "ROOM_FULL");
                    emitStatus("wifi", "room_full", null, "Room is full (4 players maximum).", null, null);
                    continue;
                }
                socket.setTcpNoDelay(true);
                socket.setKeepAlive(true);
                socket.setSoTimeout(0);
                Peer peer = createWifiPeer(socket, nextPeerId(), socket.getInetAddress().getHostAddress());
                hostPeers.put(peer.id, peer);
                emitStatus("wifi", "peer_connected", socket.getInetAddress().getHostAddress(), "Player connection accepted.", peer.id, peer.label);
                io.execute(() -> readHostPeer(peer, gen));
            }
        } catch (Exception e) {
            if (isCurrent(gen, "wifi", true)) emitStatus("wifi", "error", null, friendlyError(e), null, null);
        } finally {
            safeClose(server);
            synchronized (lifecycleLock) {
                if (wifiServer == server) wifiServer = null;
            }
        }
    }

    private void runWifiJoin(int gen, String host) {
        Socket socket = null;
        try {
            emitStatus("wifi", "connecting", host, "Connecting to host room…", null, null);
            socket = new Socket();
            socket.connect(new InetSocketAddress(host, WIFI_PORT), 9000);
            if (!isCurrent(gen, "wifi", false)) {
                safeClose(socket);
                return;
            }
            socket.setTcpNoDelay(true);
            socket.setKeepAlive(true);
            Peer peer = createWifiPeer(socket, "HOST", host);
            upstream = peer;
            emitStatus("wifi", "connected", host, "Connected to host. Joining room…", null, host);
            readGuestPeer(peer, gen);
        } catch (Exception e) {
            safeClose(socket);
            if (isCurrent(gen, "wifi", false)) emitStatus("wifi", "error", host, friendlyError(e), null, null);
        }
    }

    private void startBluetoothHostAfterPermission() {
        final int gen = beginTransport("bluetooth", true);
        io.execute(() -> runBluetoothHost(gen));
    }

    private void startBluetoothJoinAfterPermission(String address) {
        final int gen = beginTransport("bluetooth", false);
        io.execute(() -> runBluetoothJoin(gen, address));
    }

    private void runBluetoothHost(int gen) {
        BluetoothServerSocket server = null;
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) throw new IllegalStateException("Bluetooth is not supported on this phone.");
            if (!adapter.isEnabled()) throw new IllegalStateException("Turn on Bluetooth first.");

            try {
                server = adapter.listenUsingInsecureRfcommWithServiceRecord(BT_SERVICE, BT_UUID);
            } catch (Exception insecureFailure) {
                server = adapter.listenUsingRfcommWithServiceRecord(BT_SERVICE, BT_UUID);
            }
            synchronized (lifecycleLock) {
                if (!isCurrent(gen, "bluetooth", true)) {
                    safeClose(server);
                    return;
                }
                bluetoothServer = server;
            }
            emitStatus("bluetooth", "hosting", null, "Bluetooth room is open. Joined phones must already be paired.", null, null);

            while (isCurrent(gen, "bluetooth", true)) {
                BluetoothSocket socket = server.accept();
                if (!isCurrent(gen, "bluetooth", true)) {
                    safeClose(socket);
                    break;
                }
                if (hostPeers.size() >= MAX_REMOTE_PLAYERS) {
                    rejectBluetoothSocket(socket, "ROOM_FULL");
                    emitStatus("bluetooth", "room_full", null, "Room is full (4 players maximum).", null, null);
                    continue;
                }
                String label = safeDeviceName(socket.getRemoteDevice());
                Peer peer = createBluetoothPeer(socket, nextPeerId(), label);
                hostPeers.put(peer.id, peer);
                emitStatus("bluetooth", "peer_connected", null, "Player connection accepted.", peer.id, label);
                io.execute(() -> readHostPeer(peer, gen));
            }
        } catch (Exception e) {
            if (isCurrent(gen, "bluetooth", true)) emitStatus("bluetooth", "error", null, friendlyError(e), null, null);
        } finally {
            safeClose(server);
            synchronized (lifecycleLock) {
                if (bluetoothServer == server) bluetoothServer = null;
            }
        }
    }

    private void runBluetoothJoin(int gen, String address) {
        BluetoothSocket socket = null;
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) throw new IllegalStateException("Bluetooth is not supported on this phone.");
            if (!adapter.isEnabled()) throw new IllegalStateException("Turn on Bluetooth first.");
            BluetoothDevice device = adapter.getRemoteDevice(address);
            emitStatus("bluetooth", "connecting", null, "Connecting to " + safeDeviceName(device) + "…", null, null);

            try {
                socket = device.createInsecureRfcommSocketToServiceRecord(BT_UUID);
                socket.connect();
            } catch (Exception firstFailure) {
                safeClose(socket);
                socket = device.createRfcommSocketToServiceRecord(BT_UUID);
                socket.connect();
            }

            if (!isCurrent(gen, "bluetooth", false)) {
                safeClose(socket);
                return;
            }
            Peer peer = createBluetoothPeer(socket, "HOST", safeDeviceName(device));
            upstream = peer;
            emitStatus("bluetooth", "connected", null, "Connected to host. Joining room…", null, peer.label);
            readGuestPeer(peer, gen);
        } catch (Exception e) {
            safeClose(socket);
            if (isCurrent(gen, "bluetooth", false)) emitStatus("bluetooth", "error", null, friendlyError(e), null, null);
        }
    }

    private void readHostPeer(Peer peer, int gen) {
        try {
            String line;
            while (isCurrent(gen, peer.transport, true) && !peer.closed && (line = peer.reader.readLine()) != null) {
                if (line.length() <= 65536) emitMessage(peer.transport, peer.id, line);
            }
        } catch (Exception ignored) {
        } finally {
            if (hostPeers.remove(peer.id, peer)) {
                closePeer(peer);
                if (isCurrent(gen, peer.transport, true)) emitStatus(peer.transport, "peer_disconnected", null, "A player left the room.", peer.id, peer.label);
            }
        }
    }

    private void readGuestPeer(Peer peer, int gen) {
        try {
            String line;
            while (isCurrent(gen, peer.transport, false) && !peer.closed && (line = peer.reader.readLine()) != null) {
                if (line.length() <= 65536) emitMessage(peer.transport, null, line);
            }
            if (isCurrent(gen, peer.transport, false)) emitStatus(peer.transport, "disconnected", null, "Host disconnected.", null, peer.label);
        } catch (Exception e) {
            if (isCurrent(gen, peer.transport, false)) emitStatus(peer.transport, "disconnected", null, friendlyError(e), null, peer.label);
        } finally {
            if (upstream == peer) upstream = null;
            closePeer(peer);
        }
    }

    private void writePeer(Peer peer, String message, int gen) {
        if (peer == null || peer.closed || gen != generation.get()) return;
        try {
            synchronized (sendLock) {
                peer.writer.write(message);
                peer.writer.write('\n');
                peer.writer.flush();
            }
        } catch (Exception e) {
            closePeer(peer);
            if (hostMode) {
                if (hostPeers.remove(peer.id, peer)) emitStatus(peer.transport, "peer_disconnected", null, "A player connection was lost.", peer.id, peer.label);
            } else if (upstream == peer) {
                upstream = null;
                emitStatus(peer.transport, "disconnected", null, "Connection to host was lost.", null, peer.label);
            }
        }
    }

    private Peer createWifiPeer(Socket socket, String id, String label) throws Exception {
        return new Peer(
            id, label, "wifi", socket,
            new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8)),
            new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8))
        );
    }

    private Peer createBluetoothPeer(BluetoothSocket socket, String id, String label) throws Exception {
        return new Peer(
            id, label, "bluetooth", socket,
            new BufferedReader(new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8)),
            new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8))
        );
    }

    private void rejectWifiSocket(Socket socket, String reason) {
        try {
            BufferedWriter w = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));
            w.write("{\"t\":\"room_error\",\"message\":\"" + reason + "\"}\n");
            w.flush();
        } catch (Exception ignored) {
        } finally {
            safeClose(socket);
        }
    }

    private void rejectBluetoothSocket(BluetoothSocket socket, String reason) {
        try {
            BufferedWriter w = new BufferedWriter(new OutputStreamWriter(socket.getOutputStream(), StandardCharsets.UTF_8));
            w.write("{\"t\":\"room_error\",\"message\":\"" + reason + "\"}\n");
            w.flush();
        } catch (Exception ignored) {
        } finally {
            safeClose(socket);
        }
    }

    private boolean isCurrent(int gen, String transport, boolean expectedHost) {
        return !destroyed && gen == generation.get() && expectedHost == hostMode && transport != null && transport.equals(activeTransport);
    }

    private String nextPeerId() {
        return "P" + peerSequence.incrementAndGet();
    }

    private void closeAll(boolean notify) {
        synchronized (lifecycleLock) {
            safeClose(wifiServer);
            wifiServer = null;
            safeClose(bluetoothServer);
            bluetoothServer = null;
            Peer current = upstream;
            upstream = null;
            closePeer(current);
            for (Peer peer : new ArrayList<>(hostPeers.values())) closePeer(peer);
            hostPeers.clear();
            hostMode = false;
            activeTransport = null;
        }
        if (notify) emitStatus("local", "closed", null, "Local multiplayer closed.", null, null);
    }

    private void closePeer(Peer peer) {
        if (peer == null || peer.closed) return;
        peer.closed = true;
        try { peer.reader.close(); } catch (Exception ignored) {}
        try { peer.writer.close(); } catch (Exception ignored) {}
        safeClose(peer.socket);
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
        emitStatus("bluetooth", "permission_requested", null, "Allow Nearby devices / Bluetooth permission.", null, null);
        return false;
    }

    private String pairedBluetoothJson() {
        try {
            BluetoothAdapter adapter = BluetoothAdapter.getDefaultAdapter();
            if (adapter == null) return "UNSUPPORTED";
            if (!adapter.isEnabled()) return "DISABLED";
            JSONArray array = new JSONArray();
            Set<BluetoothDevice> bonded = adapter.getBondedDevices();
            List<BluetoothDevice> devices = new ArrayList<>(bonded);
            Collections.sort(devices, Comparator.comparing(this::safeDeviceName, String.CASE_INSENSITIVE_ORDER));
            for (BluetoothDevice device : devices) {
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

    private String findBestLocalIpv4() {
        try {
            List<Candidate> candidates = new ArrayList<>();
            for (NetworkInterface network : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                if (!network.isUp() || network.isLoopback()) continue;
                String name = network.getName() == null ? "" : network.getName().toLowerCase();
                int priority = name.startsWith("wlan") || name.startsWith("wifi") || name.startsWith("ap") ? 0
                    : name.startsWith("eth") ? 1
                    : name.startsWith("rmnet") || name.startsWith("ccmni") || name.startsWith("tun") || name.startsWith("ppp") ? 9
                    : 4;
                for (InetAddress address : Collections.list(network.getInetAddresses())) {
                    if (address instanceof Inet4Address && !address.isLoopbackAddress() && address.isSiteLocalAddress()) {
                        candidates.add(new Candidate(priority, address.getHostAddress()));
                    }
                }
            }
            if (!candidates.isEmpty()) {
                Collections.sort(candidates, Comparator.comparingInt(a -> a.priority));
                return candidates.get(0).address;
            }
        } catch (Exception ignored) {
        }
        return "Unavailable";
    }

    private static class Candidate {
        final int priority;
        final String address;
        Candidate(int priority, String address) { this.priority = priority; this.address = address; }
    }

    private boolean isValidHost(String host) {
        if (host == null || host.length() < 3 || host.length() > 80) return false;
        return host.matches("^[0-9A-Za-z.:-]+$");
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
        String raw = e == null ? "" : String.valueOf(e.getMessage());
        String lower = raw.toLowerCase();
        if (lower.contains("connection refused")) return "Host room was not found. Check the host IP and keep HOST ROOM open.";
        if (lower.contains("timed out") || lower.contains("timeout")) return "Connection timed out. Check that both phones are on the same Wi-Fi/hotspot.";
        if (lower.contains("host is unreachable") || lower.contains("no route")) return "Host is unreachable. Connect both phones to the same Wi-Fi/hotspot.";
        if (lower.contains("read failed") || lower.contains("socket might closed")) return "Bluetooth connection failed. Pair both phones first, keep the host room open, then try again.";
        if (raw.trim().isEmpty()) return "Local connection failed.";
        return raw.length() > 150 ? raw.substring(0, 150) : raw;
    }

    private void emitMessage(String transport, String peerId, String message) {
        try {
            JSONObject event = new JSONObject();
            event.put("type", "message");
            event.put("transport", transport);
            if (peerId != null) event.put("peerId", peerId);
            event.put("data", message);
            emit(event.toString());
        } catch (Exception ignored) {
        }
    }

    private void emitStatus(String transport, String state, String address, String message, String peerId, String label) {
        try {
            JSONObject event = new JSONObject();
            event.put("type", "status");
            event.put("transport", transport);
            event.put("state", state);
            if (address != null) event.put("address", address);
            if (message != null) event.put("message", message);
            if (peerId != null) event.put("peerId", peerId);
            if (label != null) event.put("label", label);
            emit(event.toString());
        } catch (Exception ignored) {
        }
    }

    private void emit(String json) {
        final String quoted = JSONObject.quote(json);
        activity.runOnUiThread(() -> {
            if (!destroyed && webView != null) {
                webView.evaluateJavascript("window.onLocalNetEvent&&window.onLocalNetEvent(" + quoted + ")", null);
            }
        });
    }

    private void safeClose(Closeable closeable) {
        try { if (closeable != null) closeable.close(); } catch (Exception ignored) {}
    }
}
