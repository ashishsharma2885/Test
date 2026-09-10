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

# renderMpHome is itself JavaScript source building HTML strings, so the onclick quotes
# are escaped in the generated source. Validate the actual representation instead.
s=s.replace('    "selectMultiplayerTransport(\'online\')",', '    "selectMultiplayerTransport(\\\'online\\\')",', 1)

p.write_text(s,encoding='utf-8')
print('v4.7 patch driver repaired')
