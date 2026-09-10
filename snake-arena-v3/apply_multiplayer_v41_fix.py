from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f'v4.1 patch target missing: {label}')
    html = html.replace(old, new, 1)

# Remove the asynchronous disconnect-before-connect race. The native bridge now
# owns transport replacement atomically using a connection generation ID.
for fn in ['hostWifiGame', 'joinWifiGame', 'hostBluetoothGame', 'joinBluetoothGame']:
    marker = f'function {fn}()' if fn != 'joinWifiGame' else 'function joinWifiGame()'
    start = html.find(marker)
    if start < 0:
        raise SystemExit(f'Function missing: {fn}')
    end = html.find('\n}', start)
    if end < 0:
        raise SystemExit(f'Function end missing: {fn}')
    block = html[start:end+2]
    block2 = block.replace(" try{LocalNet.disconnect()}catch(e){}\n", '')
    if block == block2:
        raise SystemExit(f'Legacy disconnect line missing in {fn}')
    html = html[:start] + block2 + html[end+2:]

# Improve Wi-Fi controls with automatic LAN/hotspot discovery.
rep(
    '<div class="mpRow"><button class="primary" style="font-size:16px;padding:9px" onclick="hostWifiGame()">HOST GAME</button></div>',
    '<div class="mpRow"><button class="primary" style="font-size:16px;padding:9px" onclick="hostWifiGame()">HOST GAME</button><button class="secondary" onclick="autoFindWifiHost()">AUTO FIND HOST</button></div>',
    'wifi auto find button'
)

# Show all useful local IPv4 candidates so hotspot devices are easier to connect.
rep(
    " let ip='Unavailable';try{ip=String(LocalNet.getWifiAddress())}catch(e){}\n $('wifiLocalAddress').textContent='IP: '+ip;",
    " let ip='Unavailable',ips=[];try{ip=String(LocalNet.getWifiAddress());if(LocalNet.getWifiAddresses){ips=JSON.parse(String(LocalNet.getWifiAddresses())||'[]')}}catch(e){}\n $('wifiLocalAddress').textContent=ips.length?'Host IP: '+ips.join('  /  '):'Host IP: '+ip;",
    'wifi address display'
)

# Insert automatic discovery function and clearer host state.
rep(
    "function joinWifiGame(){\n if(!nativeLocalNet())return;",
    "function autoFindWifiHost(){\n if(!nativeLocalNet())return;\n resetMultiplayerConnectionState();multiplayer.role='guest';multiplayer.transport='wifi';\n setMpStatus('Searching this Wi-Fi / hotspot for a host…','wait');\n try{LocalNet.discoverWifiHost()}catch(e){setMpStatus('Automatic search is unavailable on this phone. Enter the host IP manually.','error')}\n}\nfunction joinWifiGame(){\n if(!nativeLocalNet())return;",
    'auto discovery function'
)

# Retry the tiny hello handshake in case the UI bridge was still settling just
# after the native socket connected.
rep(
    "  multiplayer.connected=true;multiplayer.transport=evt.transport==='bluetooth'?'bluetooth':'wifi';setMpStatus('Connected. Starting local match…','ok');sendLocalPacket({t:'hello',profile:localProfile()});return;",
    "  multiplayer.connected=true;multiplayer.transport=evt.transport==='bluetooth'?'bluetooth':'wifi';setMpStatus('Connected. Exchanging player data…','ok');sendLocalPacket({t:'hello',profile:localProfile()});setTimeout(function(){if(multiplayer.connected&&!multiplayer.active)sendLocalPacket({t:'hello',profile:localProfile()})},450);setTimeout(function(){if(multiplayer.connected&&!multiplayer.active)sendLocalPacket({t:'hello',profile:localProfile()})},1100);return;",
    'hello retry'
)

# Handle the richer native status states.
rep(
    " if(state==='permission_requested'){setMpStatus('Allow the Bluetooth permission requested by Android.','wait');return}",
    " if(state==='connecting'){setMpStatus(evt.message||'Connecting…','wait');return}\n if(state==='discovering'){setMpStatus(evt.message||'Searching for host…','wait');return}\n if(state==='discovered'){const host=String(evt.address||'').trim();if(host){$('wifiJoinIp').value=host;setMpStatus('Host found at '+host+'. Connecting…','ok');multiplayer.role='guest';multiplayer.transport='wifi';LocalNet.joinWifi(host)}return}\n if(state==='discovery_failed'){setMpStatus(evt.message||'No host found automatically. Enter the host IP manually.','error');return}\n if(state==='permission_requested'){setMpStatus('Allow the Bluetooth permission requested by Android.','wait');return}",
    'native richer statuses'
)

rep(
    " if(state==='permission_granted'){setMpStatus('Bluetooth permission allowed.','ok');return}",
    " if(state==='permission_granted'){setMpStatus('Bluetooth permission allowed. Refreshing paired phones…','ok');setTimeout(function(){try{refreshBluetoothList()}catch(e){}},150);return}",
    'bluetooth permission refresh'
)

# Make connection errors more actionable and do not wipe the selected role just
# because a stale native operation reports a late status.
rep(
    " if(state==='error'||state==='permission_denied'){setMpStatus(evt.message||'Local connection failed.','error');return}",
    " if(state==='error'||state==='permission_denied'){multiplayer.connected=false;setMpStatus(evt.message||'Local connection failed.','error');return}",
    'error state'
)

# Export the new helper.
rep(
    'window.openLocalMultiplayer=openLocalMultiplayer;window.closeMultiplayerModal=closeMultiplayerModal;window.hostWifiGame=hostWifiGame;window.joinWifiGame=joinWifiGame;',
    'window.openLocalMultiplayer=openLocalMultiplayer;window.closeMultiplayerModal=closeMultiplayerModal;window.hostWifiGame=hostWifiGame;window.autoFindWifiHost=autoFindWifiHost;window.joinWifiGame=joinWifiGame;',
    'export auto discovery'
)

p.write_text(html, encoding='utf-8')
print('Applied Snake Arena local multiplayer v4.1 connection fixes')
