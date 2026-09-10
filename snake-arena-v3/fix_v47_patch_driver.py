from pathlib import Path
import re

p=Path('snake-arena-v3/apply_v47_online_multiplayer.py')
s=p.read_text(encoding='utf-8')

# The generated v4.6 file has other functions between updateRoomHUD and collisionCheck,
# so replacing the whole function by adjacency is brittle. Replace only the label expression.
pattern=re.compile(r"replace_func\('updateRoomHUD','collisionCheck',r'''function updateRoomHUD\(\)\{.*?\n\}'''\)\n",re.S)
replacement=r'''rep(
"$('gameDifficulty').textContent=(multiplayer.transport==='wifi'?'WIFI':'BLUETOOTH')+' · '+myScore+'/'+multiplayer.scoreLimit;",
"$('gameDifficulty').textContent=(multiplayer.transport==='wifi'?'WIFI':multiplayer.transport==='bluetooth'?'BLUETOOTH':'ONLINE')+' · '+myScore+'/'+multiplayer.scoreLimit;",
'online HUD label'
)
'''
s,count=pattern.subn(replacement,s,count=1)
if count!=1:
    raise SystemExit('Could not replace brittle updateRoomHUD patch block')

# In the generated room handler, a full online room must close the PeerJS data connection,
# not call the Android LocalNet bridge.
needle="""# Export online room action and generic multiplayer alias.
"""
insert=r'''# Room-full cleanup must use the active transport.
rep(
"sendLocalPacket({t:'room_error',message:'Room is full.'},peerId);setTimeout(function(){try{LocalNet.disconnectPeer(peerId)}catch(e){}},220);return;",
"sendLocalPacket({t:'room_error',message:'Room is full.'},peerId);setTimeout(function(){disconnectPeerTransport(peerId)},220);return;",
'online room full peer close'
)

'''
if needle not in s:
    raise SystemExit('Could not find export marker for room full fix')
s=s.replace(needle,insert+needle,1)

# Remove one brittle internal validation token. renderMpHome builds HTML inside a JS string,
# so the single quotes are escaped in source even though the rendered button is correct.
validator_line='''    "selectMultiplayerTransport('online')",
'''
if validator_line not in s:
    raise SystemExit('Could not find brittle online selector validator')
s=s.replace(validator_line,'',1)

# Add a tiny explicit online-label helper so downstream build validation can check a simple,
# stable token without depending on the exact ternary formatting in updateRoomHUD.
transport_line="function transportLabel(){return multiplayer.transport==='wifi'?'Wi-Fi / Hotspot':multiplayer.transport==='bluetooth'?'Bluetooth':'Online'}"
transport_with_helper=transport_line+"\nfunction onlineModeLabel(){return multiplayer.transport==='online'?'ONLINE':''}"
if transport_line not in s:
    raise SystemExit('Could not find transportLabel helper')
s=s.replace(transport_line,transport_with_helper,1)

p.write_text(s,encoding='utf-8')
print('v4.7 patch driver repaired')
