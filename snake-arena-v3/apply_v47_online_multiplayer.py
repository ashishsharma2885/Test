from pathlib import Path
import re

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')


def rep(old,new,label):
    global html
    if old not in html:
        raise SystemExit(f'v4.7 target missing: {label}')
    html=html.replace(old,new,1)


def replace_func(name,next_name,new_text):
    global html
    pattern=re.compile(r'function '+re.escape(name)+r'\([^\)]*\)\{.*?\n\}(?=\nfunction '+re.escape(next_name)+r'\()',re.S)
    html,count=pattern.subn(new_text,html,count=1)
    if count!=1:
        raise SystemExit(f'v4.7 function replacement failed: {name}')

# Bundle PeerJS as a local Android asset. The build workflow supplies peerjs.min.js.
rep('<script>','<script src="peerjs.min.js"></script>\n<script>','peerjs asset script')

# Multiplayer home now has three transports.
rep(
'.mpTransportGrid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:18px 0}',
'.mpTransportGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:18px 0}',
'3 transport grid'
)
rep(
'@media(max-width:760px){.mpTransportGrid,.mpRoleGrid{grid-template-columns:1fr 1fr;gap:8px}',
'@media(max-width:760px){.mpTransportGrid{grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.mpRoleGrid{grid-template-columns:1fr 1fr;gap:8px}',
'responsive transport grid'
)
rep(
'<button class="sideBtn" onclick="openLocalMultiplayer()">👥 Local Multiplayer</button>',
'<button class="sideBtn" onclick="openLocalMultiplayer()">👥 Multiplayer</button>',
'lobby multiplayer label'
)
rep(
'<h2 id="mpTitle" class="yellow" style="margin:0">👥 Local Multiplayer</h2>',
'<h2 id="mpTitle" class="yellow" style="margin:0">👥 Multiplayer</h2>',
'modal multiplayer label'
)

# Online/WebRTC transport runtime. One host is authoritative; up to three guests connect directly.
rep(
'function nativeLocalNet(){return typeof window.LocalNet!==\'undefined\'&&window.LocalNet}',
r'''const ONLINE_ROOM_PREFIX='snakearena-v47-';
const ONLINE_ROOM_CHARS='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
let onlinePeer=null,onlineHostConnection=null,onlinePeerGeneration=0,onlineOpenTimer=null;
let onlineConnections=new Map();

function nativeLocalNet(){return typeof window.LocalNet!=='undefined'&&window.LocalNet}
function onlinePeerAvailable(){return typeof window.Peer==='function'}
function transportLabel(){return multiplayer.transport==='wifi'?'Wi-Fi / Hotspot':multiplayer.transport==='bluetooth'?'Bluetooth':'Online'}
function makeOnlineRoomCode(){let out='';for(let i=0;i<6;i++)out+=ONLINE_ROOM_CHARS[Math.floor(Math.random()*ONLINE_ROOM_CHARS.length)];return out}
function normalizeOnlineRoomCode(v){return String(v||'').toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,8)}
function onlinePeerIdForRoom(code){return ONLINE_ROOM_PREFIX+normalizeOnlineRoomCode(code).toLowerCase()}
function onlinePeerOptions(){
 return {debug:0,config:{iceServers:[{urls:'stun:stun.l.google.com:19302'},{urls:'stun:stun.cloudflare.com:3478'}],sdpSemantics:'unified-plan'}};
}
function onlineErrorMessage(err){
 const type=String(err&&err.type||'');
 if(type==='peer-unavailable')return 'Room not found. Check the room code and make sure the host is still online.';
 if(type==='unavailable-id')return 'That room code is already being used. Create a new room.';
 if(type==='browser-incompatible')return 'This Android WebView does not support the required WebRTC features.';
 if(type==='network'||type==='server-error'||type==='socket-error'||type==='socket-closed')return 'Could not reach the online signaling service. Check internet connection and try again.';
 if(type==='webrtc')return 'The phones could not create a direct WebRTC connection. Try another network.';
 return String(err&&err.message||'Online connection failed.');
}
function closeOnlineTransport(){
 onlinePeerGeneration++;
 if(onlineOpenTimer){clearTimeout(onlineOpenTimer);onlineOpenTimer=null}
 const conns=Array.from(onlineConnections.values());onlineConnections.clear();
 for(const conn of conns){try{conn.close()}catch(e){}}
 if(onlineHostConnection){try{onlineHostConnection.close()}catch(e){}onlineHostConnection=null}
 if(onlinePeer){try{onlinePeer.destroy()}catch(e){}onlinePeer=null}
}
function attachOnlineConnection(conn,isHost,generation){
 if(!conn)return;
 const peerId=String(conn.peer||'');
 conn.on('open',function(){
  if(generation!==onlinePeerGeneration){try{conn.close()}catch(e){}return}
  if(isHost){onlineConnections.set(peerId,conn);multiplayer.connected=true;setMpStatus('Player connected. Adding them to the room…','wait')}
  else{onlineHostConnection=conn;multiplayer.connected=true;setMpStatus('Connected. Joining online room…','ok');setTimeout(sendJoinRequest,80)}
 });
 conn.on('data',function(data){
  if(generation!==onlinePeerGeneration)return;
  let packet=data;try{if(typeof data==='string')packet=JSON.parse(data)}catch(e){return}
  handleLocalPacket(packet,peerId||null);
 });
 conn.on('close',function(){
  if(generation!==onlinePeerGeneration)return;
  if(isHost){onlineConnections.delete(peerId);removeRoomPlayerByPeer(peerId)}
  else if(multiplayer.role==='guest'&&(multiplayer.phase==='connecting'||multiplayer.phase==='room'||multiplayer.phase==='playing')){toast('Online host disconnected.');leaveRoomToLobby(false)}
 });
 conn.on('error',function(err){if(generation===onlinePeerGeneration)setMpStatus(onlineErrorMessage(err),'error')});
}
function startOnlineHostTransport(){
 if(!onlinePeerAvailable()){setMpStatus('Online module could not load. Check internet and reopen the app.','error');return}
 closeOnlineTransport();const generation=onlinePeerGeneration;
 const id=onlinePeerIdForRoom(multiplayer.roomId);
 try{onlinePeer=new Peer(id,onlinePeerOptions())}catch(e){setMpStatus(onlineErrorMessage(e),'error');return}
 onlineOpenTimer=setTimeout(function(){if(generation===onlinePeerGeneration&&!multiplayer.connected)setMpStatus('Online room is taking too long to open. Check internet and try again.','error')},12000);
 onlinePeer.on('open',function(){
  if(generation!==onlinePeerGeneration)return;if(onlineOpenTimer){clearTimeout(onlineOpenTimer);onlineOpenTimer=null}
  multiplayer.connected=true;multiplayer.phase='room';renderRoomLobby();setMpStatus('Online room is live. Share the room code with your friends.','wait');
 });
 onlinePeer.on('connection',function(conn){if(generation===onlinePeerGeneration)attachOnlineConnection(conn,true,generation);else try{conn.close()}catch(e){}});
 onlinePeer.on('disconnected',function(){if(generation===onlinePeerGeneration&&multiplayer.phase==='room')setMpStatus('Signaling disconnected. Existing players may stay connected; new players cannot join until it reconnects.','wait')});
 onlinePeer.on('error',function(err){if(generation!==onlinePeerGeneration)return;setMpStatus(onlineErrorMessage(err),'error')});
}
function joinOnlineRoom(){
 const input=$('onlineRoomCode'),code=normalizeOnlineRoomCode(input&&input.value);if(code.length<4){toast('Enter the host room code.');return}
 if(!onlinePeerAvailable()){setMpStatus('Online module could not load. Check internet and reopen the app.','error');return}
 multiplayer.roomId=code;multiplayer.role='guest';multiplayer.phase='connecting';multiplayer.connected=false;renderGuestConnecting();setMpStatus('Finding online room '+code+'…','wait');
 closeOnlineTransport();const generation=onlinePeerGeneration;
 try{onlinePeer=new Peer(undefined,onlinePeerOptions())}catch(e){setMpStatus(onlineErrorMessage(e),'error');return}
 onlineOpenTimer=setTimeout(function(){if(generation===onlinePeerGeneration&&!multiplayer.connected)setMpStatus('Could not join in time. Check the room code and internet connection.','error')},15000);
 onlinePeer.on('open',function(){
  if(generation!==onlinePeerGeneration)return;
  let conn;try{conn=onlinePeer.connect(onlinePeerIdForRoom(code),{reliable:true,serialization:'json'})}catch(e){setMpStatus(onlineErrorMessage(e),'error');return}
  attachOnlineConnection(conn,false,generation);
 });
 onlinePeer.on('error',function(err){if(generation!==onlinePeerGeneration)return;if(onlineOpenTimer){clearTimeout(onlineOpenTimer);onlineOpenTimer=null}setMpStatus(onlineErrorMessage(err),'error')});
}
function sendOnlinePacket(packet,peerId){
 const raw=JSON.stringify(packet);
 try{
  if(multiplayer.role==='host'){
   if(peerId){const conn=onlineConnections.get(String(peerId));if(conn&&conn.open)conn.send(raw);return}
   onlineConnections.forEach(function(conn){if(conn&&conn.open)conn.send(raw)});return;
  }
  if(onlineHostConnection&&onlineHostConnection.open)onlineHostConnection.send(raw);
 }catch(e){}
}
function disconnectPeerTransport(peerId){
 if(multiplayer.transport==='online'){
  const conn=onlineConnections.get(String(peerId));if(conn){onlineConnections.delete(String(peerId));try{conn.close()}catch(e){}}return;
 }
 try{if(nativeLocalNet()&&LocalNet.disconnectPeer)LocalNet.disconnectPeer(peerId)}catch(e){}
}
function disconnectCurrentTransport(){
 if(multiplayer.transport==='online'){closeOnlineTransport();return}
 try{if(nativeLocalNet())LocalNet.disconnect()}catch(e){}
}''',
'online transport runtime'
)

replace_func('openLocalMultiplayer','closeMultiplayerModal',r'''function openLocalMultiplayer(){
 if(multiplayer.role||multiplayer.connected){renderRoomLobby()}
 else renderMpHome();
 $('multiplayerModal').classList.add('show');
}''')

replace_func('renderMpHome','selectMultiplayerTransport',r'''function renderMpHome(){
 multiplayer.transport=null;multiplayer.role=null;multiplayer.phase='idle';
 $('mpTitle').textContent='👥 Multiplayer';
 $('mpBody').innerHTML='<p class="muted">Choose how you want to play with friends. Local modes work nearby; Online works over the internet using a room code.</p><div class="mpTransportGrid">'+
 '<div class="mpBigChoice card" onclick="selectMultiplayerTransport(\'wifi\')"><div class="mpIcon">📶</div><h2>Wi-Fi</h2><p>Same Wi-Fi or phone hotspot. Lowest local latency.</p></div>'+
 '<div class="mpBigChoice card" onclick="selectMultiplayerTransport(\'bluetooth\')"><div class="mpIcon">🟦</div><h2>Bluetooth</h2><p>Nearby paired Android phones.</p></div>'+
 '<div class="mpBigChoice card" onclick="selectMultiplayerTransport(\'online\')"><div class="mpIcon">🌐</div><h2>Online</h2><p>Play from different places using a room code and internet.</p></div></div>';
 setMpStatus('Select Wi-Fi, Bluetooth or Online.','');
}''')

replace_func('selectMultiplayerTransport','renderMpRole',r'''function selectMultiplayerTransport(type){
 if(type!=='wifi'&&type!=='bluetooth'&&type!=='online')return;
 if((type==='wifi'||type==='bluetooth')&&!nativeLocalNet()){setMpStatus('Wi-Fi/Bluetooth local multiplayer is available in the Android APK.','error');return}
 multiplayer.transport=type;renderMpRole();
}''')

replace_func('renderMpRole','chooseMultiplayerRole',r'''function renderMpRole(){
 const label=transportLabel();
 $('mpTitle').textContent='👥 '+label;
 $('mpBody').innerHTML='<div style="margin-top:12px">'+mpButton('← CONNECTION TYPE','renderMpHome()','secondary mpBack')+'</div><div class="mpRoleGrid">'+
 '<div class="mpRoleCard card" onclick="chooseMultiplayerRole(\'host\')"><div style="font-size:42px">👑</div><h2>HOST ROOM</h2><div class="muted">Create the room, set the score limit, see joined players and start the match.</div></div>'+
 '<div class="mpRoleCard card" onclick="chooseMultiplayerRole(\'guest\')"><div style="font-size:42px">🎮</div><h2>JOIN ROOM</h2><div class="muted">Join a host room and wait. Only the host can start the game.</div></div></div>';
 setMpStatus('Choose HOST ROOM or JOIN ROOM.','');
}''')

replace_func('renderHostSetup','safeWifiAddress',r'''function renderHostSetup(){
 multiplayer.role='host';const label=transportLabel();const ip=multiplayer.transport==='wifi'?safeWifiAddress():'';
 $('mpTitle').textContent='👑 Create '+label+' Room';
 let info='';
 if(multiplayer.transport==='wifi')info='<div class="muted">Your local IP: <b class="yellow">'+mpEsc(ip)+'</b></div>';
 else if(multiplayer.transport==='bluetooth')info='<div class="muted">The other phones must be paired with this phone first.</div>';
 else info='<div class="muted">A short room code will be created. Send it to friends anywhere with internet.</div>';
 $('mpBody').innerHTML='<div style="margin-top:12px">'+mpButton('← BACK','cancelRoomSetup()','secondary mpBack')+'</div><div class="panel" style="padding:16px;margin-top:12px"><h3 class="yellow">Match Rules</h3><label><b>Winning score limit</b></label><input id="hostScoreLimit" class="mpInput" type="number" min="5" max="100" step="5" value="'+multiplayer.scoreLimit+'"><div class="mpRuleBar"><div class="mpRule card"><strong>+1</strong>AI BOT KILL</div><div class="mpRule card"><strong>+3</strong>PLAYER KILL</div><div class="mpRule card"><strong>'+ROOM_BOTS+'</strong>AI BOTS</div></div>'+info+'<div class="mpStartWrap"><button class="primary" onclick="createHostRoom()">CREATE ROOM</button></div></div>';
 setMpStatus('Set the score limit, then create the room.','');
}''')

replace_func('createHostRoom','renderJoinSetup',r'''function createHostRoom(){
 const localMode=multiplayer.transport==='wifi'||multiplayer.transport==='bluetooth';if(localMode&&!nativeLocalNet())return;
 const input=$('hostScoreLimit');const limit=clamp(Math.round(Number(input&&input.value)||20),5,100);
 multiplayer.scoreLimit=limit;multiplayer.role='host';multiplayer.phase='room';multiplayer.roomId=multiplayer.transport==='online'?makeOnlineRoomCode():'R'+Math.floor(1000+Math.random()*9000);multiplayer.connected=false;multiplayer.scores={};multiplayer.peerToClient={};
 const me=localProfile();me.host=true;multiplayer.roster=[me];multiplayer.scores[me.id]=0;
 renderRoomLobby();setMpStatus('Opening '+transportLabel()+' room…','wait');
 if(multiplayer.transport==='online')startOnlineHostTransport();
 else if(multiplayer.transport==='wifi')LocalNet.hostWifi();
 else LocalNet.hostBluetooth();
}''')

replace_func('renderJoinSetup','cancelRoomSetup',r'''function renderJoinSetup(){
 multiplayer.role='guest';$('mpTitle').textContent='🎮 Join '+transportLabel()+' Room';
 let body='<div style="margin-top:12px">'+mpButton('← BACK','cancelRoomSetup()','secondary mpBack')+'</div><div class="panel" style="padding:16px;margin-top:12px">';
 if(multiplayer.transport==='wifi'){
  body+='<h3 class="yellow">Join Wi-Fi Host</h3><p class="muted">Connect to the same Wi-Fi/hotspot and enter the host IP.</p><input id="wifiJoinIp" class="mpInput" inputmode="decimal" maxlength="40" placeholder="Host IP, e.g. 192.168.43.1"><button class="primary" style="width:100%;font-size:20px" onclick="joinWifiRoom()">JOIN ROOM</button>';
 }else if(multiplayer.transport==='bluetooth'){
  body+='<h3 class="yellow">Join Bluetooth Host</h3><p class="muted">Pair both phones in Android settings first.</p><div style="display:flex;gap:8px"><select id="btDeviceSelect" class="mpInput" style="flex:1"><option value="">Paired host phones</option></select><button class="secondary" onclick="refreshBluetoothList()">REFRESH</button></div><button class="primary" style="width:100%;font-size:20px" onclick="joinBluetoothRoom()">JOIN ROOM</button>';
 }else{
  body+='<h3 class="yellow">Join Online Room</h3><p class="muted">Enter the room code shown on the host phone. Both phones need internet.</p><input id="onlineRoomCode" class="mpInput" inputmode="text" maxlength="8" autocomplete="off" autocapitalize="characters" placeholder="ROOM CODE" style="text-transform:uppercase;letter-spacing:.14em;text-align:center;font-size:22px"><button class="primary" style="width:100%;font-size:20px" onclick="joinOnlineRoom()">JOIN ONLINE ROOM</button>';
 }
 body+='</div>';$('mpBody').innerHTML=body;setMpStatus('Join a host room. You will wait for the host to start.','');
 if(multiplayer.transport==='bluetooth')setTimeout(refreshBluetoothList,80);
}''')

replace_func('cancelRoomSetup','joinWifiRoom',r'''function cancelRoomSetup(){
 disconnectCurrentTransport();resetMultiplayerConnectionState();renderMpHome();
}''')

replace_func('renderRoomLobby','hostChangeScoreLimit',r'''function renderRoomLobby(){
 if(!multiplayer.role)return;
 const isHost=multiplayer.role==='host',label=transportLabel();
 $('mpTitle').textContent=(isHost?'👑 Host Room':'🎮 Joined Room')+' · '+label;
 let connectInfo='';
 if(isHost&&multiplayer.transport==='wifi')connectInfo='<div class="mpRoomCode">Host IP: '+mpEsc(safeWifiAddress())+'</div><div class="muted">Give this IP to players on the same Wi-Fi/hotspot.</div>';
 else if(isHost&&multiplayer.transport==='bluetooth')connectInfo='<div class="mpRoomCode">Bluetooth Room '+mpEsc(multiplayer.roomId||'')+'</div><div class="muted">Joined phones must select this paired host phone.</div>';
 else if(isHost&&multiplayer.transport==='online')connectInfo='<div class="mpRoomCode">ROOM CODE: '+mpEsc(multiplayer.roomId||'')+'</div><div class="muted">Friends can join from another city/network using this code. Keep this host screen open.</div>';
 else connectInfo='<div class="mpRoomCode">Room '+mpEsc(multiplayer.roomId||'')+'</div><div class="muted">You are joined. Wait for the host to start.</div>';
 const count=(multiplayer.roster||[]).length;
 $('mpBody').innerHTML='<div class="mpRoomTop"><span class="pill">'+label+'</span><span class="pill">Players '+count+'/'+ROOM_MAX_PLAYERS+'</span><span class="pill">First to '+multiplayer.scoreLimit+'</span></div>'+connectInfo+'<div class="mpRuleBar"><div class="mpRule card"><strong>+1</strong>AI BOT</div><div class="mpRule card"><strong>+3</strong>PLAYER</div><div class="mpRule card"><strong>'+ROOM_BOTS+'</strong>AI BOTS</div></div><h3 class="yellow">Players in Room</h3><div class="mpPlayers">'+roomPlayerCards()+'</div>'+
 (isHost?'<div class="panel" style="padding:12px;margin-top:10px"><label><b>Score limit</b></label><input id="roomScoreLimit" class="mpInput" type="number" min="5" max="100" step="5" value="'+multiplayer.scoreLimit+'" onchange="hostChangeScoreLimit(this.value)"><div class="mpStartWrap"><button class="primary" '+(count<2?'disabled style="opacity:.55"':'')+' onclick="hostStartRoomGame()">START GAME</button></div><div class="muted" style="text-align:center;margin-top:8px">Only the host can start.</div></div>':'<div class="mpWaitingHost">⏳ WAITING FOR HOST TO START…<br><span class="muted">You do not need a Start button.</span></div>')+
 '<div style="text-align:center;margin-top:12px"><button class="secondary" onclick="leaveRoomToLobby(true)">LEAVE ROOM</button></div>';
 setMpStatus(isHost?(count<2?'Room open. Waiting for at least one player…':'Players joined. Start whenever you are ready.'):'Joined successfully. Waiting for the host…',count>=2||!isHost?'ok':'wait');
}''')

replace_func('sendLocalPacket','sendJoinRequest',r'''function sendLocalPacket(packet,peerId){
 if(multiplayer.transport==='online'){sendOnlinePacket(packet,peerId);return}
 if(!nativeLocalNet())return;const raw=JSON.stringify(packet);
 try{if(peerId&&multiplayer.role==='host'&&LocalNet.sendTo)LocalNet.sendTo(peerId,raw);else LocalNet.send(raw)}catch(e){}
}''')

# Close the correct transport when leaving, and support kicking/closing an online peer.
replace_func('leaveRoomToLobby','disconnectLocalMultiplayer',r'''function leaveRoomToLobby(sendNotice){
 if(sendNotice&&multiplayer.connected)sendLocalPacket({t:'leave_room',clientId:roomClientId});cleanupPreviousMatch(false);disconnectCurrentTransport();resetMultiplayerConnectionState();gameState=GAME_STATE.MENU;showScreen('lobby');if($('multiplayerModal'))$('multiplayerModal').classList.remove('show');
}''')

rep(
"if(packet.t==='leave_room'&&multiplayer.role==='host'&&peerId){setTimeout(function(){try{LocalNet.disconnectPeer(peerId)}catch(e){}},80);return}",
"if(packet.t==='leave_room'&&multiplayer.role==='host'&&peerId){setTimeout(function(){disconnectPeerTransport(peerId)},80);return}",
'online leave peer'
)

# Online packet rates are lower than LAN but remain smooth because remote entities interpolate.
rep(
"if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='guest'||!player)return;const interval=multiplayer.transport==='bluetooth'?85:50;",
"if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='guest'||!player)return;const interval=multiplayer.transport==='bluetooth'?85:multiplayer.transport==='online'?65:50;",
'online guest send rate'
)
rep(
"if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='host')return;const interval=multiplayer.transport==='bluetooth'?150:72;",
"if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='host')return;const interval=multiplayer.transport==='bluetooth'?150:multiplayer.transport==='online'?100:72;",
'online host snapshot rate'
)

replace_func('updateRoomHUD','collisionCheck',r'''function updateRoomHUD(){
 if(!player)return;const ordered=multiplayer.roster.slice().sort(function(a,b){return(multiplayer.scores[b.id]||0)-(multiplayer.scores[a.id]||0)}),myScore=multiplayer.scores[roomClientId]||0,myRank=Math.max(1,ordered.findIndex(function(p){return p.id===roomClientId})+1);$('score').textContent=myScore;$('length').textContent=Math.floor(player.length);$('rank').textContent=myRank+'/'+ordered.length;$('runCoins').textContent=run?run.coins:0;$('gameDifficulty').textContent=(multiplayer.transport==='wifi'?'WIFI':multiplayer.transport==='bluetooth'?'BLUETOOTH':'ONLINE')+' · '+myScore+'/'+multiplayer.scoreLimit;$('leaderList').innerHTML=ordered.map(function(p){return '<li style="'+(p.id===roomClientId?'color:#ffd45e;font-weight:900':'')+'">'+mpEsc(p.name)+' — '+(multiplayer.scores[p.id]||0)+'</li>'}).join('');if(emoteUntil>performance.now()){const q=screenPos(player.x,player.y,currentZoom());$('emoteBubble').style.display='block';$('emoteBubble').style.left=(q.x-16)+'px';$('emoteBubble').style.top=(q.y-55)+'px'}else $('emoteBubble').style.display='none';
}''')

# Export online room action and generic multiplayer alias.
rep(
'window.openLocalMultiplayer=openLocalMultiplayer;window.closeMultiplayerModal=closeMultiplayerModal;',
'window.openLocalMultiplayer=openLocalMultiplayer;window.openMultiplayer=openLocalMultiplayer;window.joinOnlineRoom=joinOnlineRoom;window.closeMultiplayerModal=closeMultiplayerModal;',
'online exports'
)

required=[
    '<script src="peerjs.min.js"></script>',
    'Online works over the internet using a room code',
    "selectMultiplayerTransport('online')",
    "const ONLINE_ROOM_PREFIX='snakearena-v47-'",
    'function startOnlineHostTransport()',
    'function joinOnlineRoom()',
    'function sendOnlinePacket(packet,peerId)',
    'function disconnectCurrentTransport()',
    "multiplayer.transport==='online'?100:72",
    "multiplayer.transport==='online'?65:50",
    'ROOM CODE:',
    'JOIN ONLINE ROOM',
    'ROOM_MAX_PLAYERS=4',
    'ROOM_BOTS=24',
    "t:'death_loot'",
    'PLAYER_START_LENGTH=3',
]
missing=[x for x in required if x not in html]
if missing:
    raise SystemExit('v4.7 online patch incomplete: '+', '.join(missing))

p.write_text(html,encoding='utf-8')
print('v4.7 online WebRTC room-code multiplayer patch applied')
