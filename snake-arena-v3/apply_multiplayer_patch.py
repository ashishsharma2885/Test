from pathlib import Path

p = Path("snake-arena-v3/game.html")
html = p.read_text(encoding="utf-8")


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f"Patch target missing: {label}")
    html = html.replace(old, new, 1)


# ---------- Multiplayer room UI styles ----------
rep(
    "</style>",
    r'''
.mpTransportGrid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:18px 0}.mpBigChoice{min-height:190px;padding:22px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;cursor:pointer}.mpBigChoice .mpIcon{font-size:54px;margin-bottom:8px}.mpBigChoice h2{margin:0;color:#fff15d}.mpBigChoice p{margin:7px 0 0;color:#d5e8fa;font-size:13px;line-height:1.4}.mpRoleGrid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0}.mpRoleCard{padding:20px;min-height:180px;cursor:pointer;text-align:center}.mpRoleCard h2{color:#fff15d;margin:5px 0}.mpRoomTop{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0 14px}.mpRoomCode{font-size:22px;color:#78f5ff;font-weight:1000;word-break:break-word}.mpPlayers{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:12px 0}.mpPlayer{padding:12px;display:flex;align-items:center;gap:10px;min-height:66px}.mpPlayerAvatar{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#102b4d;border:2px solid #77c6ff;font-size:22px}.mpPlayerInfo{min-width:0;flex:1}.mpPlayerInfo b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.mpHostBadge{font-size:9px;padding:3px 6px;border-radius:99px;background:#ffbd32;color:#482b00;font-weight:1000}.mpScoreBadge{font-size:15px;color:#fff15d;font-weight:1000}.mpStatus{padding:11px 13px;border-radius:12px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);font-weight:800;min-height:42px;margin-top:10px}.mpConnected{color:#7dff9a}.mpWaiting{color:#ffe26b}.mpError{color:#ff8993}.mpInput{width:100%;height:44px;margin:8px 0;border-radius:11px;border:2px solid #78b9ff;background:#071b34;color:#fff;padding:0 11px;font-weight:900;outline:none}.mpRuleBar{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.mpRule{padding:10px;text-align:center}.mpRule strong{display:block;color:#fff15d;font-size:18px}.mpBack{font-size:13px;padding:8px 13px}.mpStartWrap{text-align:center;margin-top:14px}.mpWaitingHost{text-align:center;padding:16px;font-weight:900;color:#ffe26b}.mpRoomFull{color:#ff8d98}.roomRespawn{position:absolute;left:50%;top:23%;transform:translateX(-50%);padding:10px 16px;border-radius:12px;background:rgba(0,0,0,.7);border:1px solid rgba(255,255,255,.18);font-weight:1000;color:#fff15d;display:none;z-index:11}.roomRespawn.show{display:block}
@media(max-width:760px){.mpTransportGrid,.mpRoleGrid{grid-template-columns:1fr 1fr;gap:8px}.mpBigChoice{min-height:140px;padding:12px}.mpBigChoice .mpIcon{font-size:38px}.mpBigChoice h2,.mpRoleCard h2{font-size:18px}.mpRoleCard{min-height:130px;padding:11px}.mpPlayers{grid-template-columns:1fr 1fr}.mpRuleBar{gap:5px}.mpRule{padding:6px;font-size:10px}}
</style>''',
    "style end"
)

# ---------- Lobby button ----------
rep(
    '<div class="quickRight">',
    '<div class="quickRight">\n      <button class="sideBtn" onclick="openLocalMultiplayer()">👥 Local Multiplayer</button>',
    "quick right"
)

# ---------- Post result title + mode-aware buttons ----------
rep(
    '<div class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>',
    '<div id="postTitle" class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>',
    "post title"
)
rep(
    '<button class="primary" onclick="startNewMatch()">PLAY AGAIN</button>\n    <button class="secondary" style="margin-left:8px" onclick="returnToMenuFromGameOver()">MAIN MENU</button>',
    '<button class="primary" onclick="postPlayAgain()">BACK TO ROOM</button>\n    <button class="secondary" style="margin-left:8px" onclick="postMainMenu()">MAIN MENU</button>',
    "post buttons"
)

# ---------- Multiplayer modal ----------
rep(
    '<div id="dailyModal" class="modal">',
    r'''<div id="multiplayerModal" class="modal">
  <div class="modalBox panel" style="width:min(860px,94vw)">
    <div style="display:flex;align-items:center;gap:10px">
      <h2 id="mpTitle" class="yellow" style="margin:0">👥 Local Multiplayer</h2>
      <span class="pill">Up to 4 Players</span>
      <button class="closeBtn" style="margin-left:auto" onclick="closeMultiplayerModal()">×</button>
    </div>
    <div id="mpBody"></div>
    <div id="mpStatus" class="mpStatus">Choose how you want to connect.</div>
  </div>
</div>

<div id="dailyModal" class="modal">''',
    "daily modal"
)

# ---------- Respawn message in gameplay ----------
rep(
    '<div id="emoteBubble"></div>',
    '<div id="emoteBubble"></div><div id="roomRespawn" class="roomRespawn">RESPAWNING…</div>',
    "respawn label"
)

# ---------- Multiplayer state + room logic ----------
rep(
    "function currentEmote(){return EMOTES.find(function(s){return s.id===data.selectedEmote})||EMOTES[0]}",
    r'''function currentEmote(){return EMOTES.find(function(s){return s.id===data.selectedEmote})||EMOTES[0]}

const ROOM_MAX_PLAYERS=4;
const ROOM_BOTS=24;
const AI_KILL_POINTS=1;
const PLAYER_KILL_POINTS=3;
const multiplayer={
 active:false,connected:false,role:null,transport:null,phase:'idle',roomId:null,matchId:null,
 scoreLimit:20,roster:[],scores:{},peerToClient:{},remoteTargets:{},btDevices:[],
 lastSend:0,lastSnapshot:0,winnerId:null
};
let remotePlayers=new Map();
let roomClientId=localStorage.getItem('snakeArenaRoomClientId')||('C'+Date.now().toString(36)+Math.random().toString(36).slice(2,8));
localStorage.setItem('snakeArenaRoomClientId',roomClientId);

function nativeLocalNet(){return typeof window.LocalNet!=='undefined'&&window.LocalNet}
function localProfile(){
 const skin=currentSkin();
 return {id:roomClientId,name:sanitizePlayerName(data.name)||'Player',body:skin.body,head:skin.head,accent:skin.accent};
}
function setMpStatus(text,kind){
 const el=$('mpStatus');if(!el)return;
 el.textContent=text||'';el.className='mpStatus '+(kind==='ok'?'mpConnected':kind==='wait'?'mpWaiting':kind==='error'?'mpError':'');
}
function mpEsc(v){return String(v||'').replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]})}
function mpButton(label,fn,cls){return '<button class="'+(cls||'secondary')+'" onclick="'+fn+'">'+label+'</button>'}
function resetMultiplayerConnectionState(){
 multiplayer.active=false;multiplayer.connected=false;multiplayer.role=null;multiplayer.transport=null;multiplayer.phase='idle';multiplayer.roomId=null;multiplayer.matchId=null;multiplayer.roster=[];multiplayer.scores={};multiplayer.peerToClient={};multiplayer.remoteTargets={};multiplayer.lastSend=0;multiplayer.lastSnapshot=0;multiplayer.winnerId=null;remotePlayers=new Map();
}
function openLocalMultiplayer(){
 if(!nativeLocalNet()){toast('Local multiplayer is available in the Android APK.');return}
 if(multiplayer.role||multiplayer.connected){renderRoomLobby();}
 else renderMpHome();
 $('multiplayerModal').classList.add('show');
}
function closeMultiplayerModal(){
 if(multiplayer.role||multiplayer.connected){toast('Leave the room first.');return}
 $('multiplayerModal').classList.remove('show');
}
function renderMpHome(){
 multiplayer.transport=null;multiplayer.role=null;multiplayer.phase='idle';
 $('mpTitle').textContent='👥 Local Multiplayer';
 $('mpBody').innerHTML='<p class="muted">Choose one connection type. Wi-Fi / hotspot is fastest; Bluetooth works between paired Android phones.</p><div class="mpTransportGrid">'+
 '<div class="mpBigChoice card" onclick="selectMultiplayerTransport(\'wifi\')"><div class="mpIcon">📶</div><h2>Wi-Fi / Hotspot</h2><p>All phones join the same Wi-Fi, or connect to the host phone hotspot.</p></div>'+
 '<div class="mpBigChoice card" onclick="selectMultiplayerTransport(\'bluetooth\')"><div class="mpIcon">🟦</div><h2>Bluetooth</h2><p>Pair the phones in Android Bluetooth settings, then create or join a room.</p></div></div>';
 setMpStatus('Select Wi-Fi or Bluetooth.','');
}
function selectMultiplayerTransport(type){
 if(type!=='wifi'&&type!=='bluetooth')return;
 multiplayer.transport=type;renderMpRole();
}
function renderMpRole(){
 const label=multiplayer.transport==='wifi'?'Wi-Fi / Hotspot':'Bluetooth';
 $('mpTitle').textContent='👥 '+label;
 $('mpBody').innerHTML='<div style="margin-top:12px">'+mpButton('← CONNECTION TYPE','renderMpHome()','secondary mpBack')+'</div><div class="mpRoleGrid">'+
 '<div class="mpRoleCard card" onclick="chooseMultiplayerRole(\'host\')"><div style="font-size:42px">👑</div><h2>HOST ROOM</h2><div class="muted">Create the room, set the score limit, see joined players and start the match.</div></div>'+
 '<div class="mpRoleCard card" onclick="chooseMultiplayerRole(\'guest\')"><div style="font-size:42px">🎮</div><h2>JOIN ROOM</h2><div class="muted">Join a host room and wait. Only the host can start the game.</div></div></div>';
 setMpStatus('Choose HOST ROOM or JOIN ROOM.','');
}
function chooseMultiplayerRole(role){
 if(role==='host')renderHostSetup();else renderJoinSetup();
}
function renderHostSetup(){
 multiplayer.role='host';
 const ip=multiplayer.transport==='wifi'?safeWifiAddress():'';
 $('mpTitle').textContent='👑 Create '+(multiplayer.transport==='wifi'?'Wi-Fi':'Bluetooth')+' Room';
 $('mpBody').innerHTML='<div style="margin-top:12px">'+mpButton('← BACK','cancelRoomSetup()','secondary mpBack')+'</div><div class="panel" style="padding:16px;margin-top:12px"><h3 class="yellow">Match Rules</h3><label><b>Winning score limit</b></label><input id="hostScoreLimit" class="mpInput" type="number" min="5" max="100" step="5" value="'+multiplayer.scoreLimit+'"><div class="mpRuleBar"><div class="mpRule card"><strong>+1</strong>AI BOT KILL</div><div class="mpRule card"><strong>+3</strong>PLAYER KILL</div><div class="mpRule card"><strong>'+ROOM_BOTS+'</strong>AI BOTS</div></div>'+(multiplayer.transport==='wifi'?'<div class="muted">Your local IP: <b class="yellow">'+mpEsc(ip)+'</b></div>':'<div class="muted">The other phones must be paired with this phone first.</div>')+'<div class="mpStartWrap"><button class="primary" onclick="createHostRoom()">CREATE ROOM</button></div></div>';
 setMpStatus('Set the score limit, then create the room.','');
}
function safeWifiAddress(){try{return String(LocalNet.getWifiAddress())}catch(e){return 'Unavailable'}}
function createHostRoom(){
 if(!nativeLocalNet())return;
 const input=$('hostScoreLimit');const limit=clamp(Math.round(Number(input&&input.value)||20),5,100);
 multiplayer.scoreLimit=limit;multiplayer.role='host';multiplayer.phase='room';multiplayer.roomId='R'+Math.floor(1000+Math.random()*9000);multiplayer.connected=false;multiplayer.scores={};multiplayer.peerToClient={};
 const me=localProfile();me.host=true;multiplayer.roster=[me];multiplayer.scores[me.id]=0;
 renderRoomLobby();setMpStatus('Opening room…','wait');
 if(multiplayer.transport==='wifi')LocalNet.hostWifi();else LocalNet.hostBluetooth();
}
function renderJoinSetup(){
 multiplayer.role='guest';
 $('mpTitle').textContent='🎮 Join '+(multiplayer.transport==='wifi'?'Wi-Fi':'Bluetooth')+' Room';
 let body='<div style="margin-top:12px">'+mpButton('← BACK','cancelRoomSetup()','secondary mpBack')+'</div><div class="panel" style="padding:16px;margin-top:12px">';
 if(multiplayer.transport==='wifi'){
  body+='<h3 class="yellow">Join Host Room</h3><p class="muted">Connect to the same Wi-Fi/hotspot. Enter the IP shown on the host phone.</p><input id="wifiJoinIp" class="mpInput" inputmode="decimal" maxlength="40" placeholder="Host IP, e.g. 192.168.43.1"><button class="primary" style="width:100%;font-size:20px" onclick="joinWifiRoom()">JOIN ROOM</button>';
 }else{
  body+='<h3 class="yellow">Join Bluetooth Room</h3><p class="muted">Pair both phones in Android settings first.</p><div style="display:flex;gap:8px"><select id="btDeviceSelect" class="mpInput" style="flex:1"><option value="">Paired host phones</option></select><button class="secondary" onclick="refreshBluetoothList()">REFRESH</button></div><button class="primary" style="width:100%;font-size:20px" onclick="joinBluetoothRoom()">JOIN ROOM</button>';
 }
 body+='</div>';$('mpBody').innerHTML=body;setMpStatus('Join a host room. You will wait for the host to start.','');
 if(multiplayer.transport==='bluetooth')setTimeout(refreshBluetoothList,80);
}
function cancelRoomSetup(){
 if(nativeLocalNet())try{LocalNet.disconnect()}catch(e){}
 resetMultiplayerConnectionState();renderMpHome();
}
function joinWifiRoom(){
 const ip=String(($('wifiJoinIp')&&$('wifiJoinIp').value)||'').trim();if(!ip){toast('Enter the host IP shown on the host phone.');return}
 multiplayer.role='guest';multiplayer.phase='connecting';multiplayer.connected=false;setMpStatus('Connecting to '+ip+'…','wait');LocalNet.joinWifi(ip);renderGuestConnecting();
}
function refreshBluetoothList(){
 if(!nativeLocalNet())return;let raw='';try{raw=String(LocalNet.getPairedBluetoothDevices())}catch(e){raw='ERROR'}
 if(raw==='PERMISSION_REQUIRED'){setMpStatus('Allow Nearby devices / Bluetooth permission, then the list will refresh.','wait');return}
 if(raw==='DISABLED'){setMpStatus('Turn on Bluetooth first.','error');return}
 if(raw==='UNSUPPORTED'){setMpStatus('Bluetooth is not supported on this phone.','error');return}
 let devices=[];try{devices=JSON.parse(raw)}catch(e){}
 multiplayer.btDevices=devices;
 const sel=$('btDeviceSelect');if(sel){sel.innerHTML='<option value="">Paired host phones</option>'+devices.map(function(d){return '<option value="'+String(d.address).replace(/[^0-9A-Fa-f:]/g,'')+'">'+mpEsc(d.name||'Android phone')+'</option>'}).join('')}
 setMpStatus(devices.length?devices.length+' paired phone(s) found.':'No paired phones found. Pair both phones in Android settings first.',devices.length?'ok':'wait');
}
function joinBluetoothRoom(){
 const sel=$('btDeviceSelect'),address=String(sel&&sel.value||'');if(!address){toast('Select the paired host phone.');return}
 multiplayer.role='guest';multiplayer.phase='connecting';multiplayer.connected=false;setMpStatus('Connecting to Bluetooth host…','wait');LocalNet.joinBluetooth(address);renderGuestConnecting();
}
function renderGuestConnecting(){
 $('mpTitle').textContent='🎮 Joining Room';
 $('mpBody').innerHTML='<div class="panel" style="padding:24px;text-align:center;margin-top:16px"><div style="font-size:50px">🔄</div><h2 class="yellow">CONNECTING…</h2><div class="muted">Waiting for the host room.</div><div style="margin-top:16px"><button class="secondary" onclick="leaveRoomToLobby(false)">CANCEL</button></div></div>';
}
function roomPlayerCards(){
 const roster=multiplayer.roster||[];
 const cards=[];
 for(let i=0;i<ROOM_MAX_PLAYERS;i++){
  const p=roster[i];
  if(p){const sc=multiplayer.scores[p.id]||0;cards.push('<div class="mpPlayer card"><div class="mpPlayerAvatar">🐍</div><div class="mpPlayerInfo"><b>'+mpEsc(p.name)+(p.host?' <span class="mpHostBadge">HOST</span>':'')+'</b><span class="muted">Player '+(i+1)+'</span></div><span class="mpScoreBadge">'+sc+'</span></div>')}
  else cards.push('<div class="mpPlayer card" style="opacity:.55"><div class="mpPlayerAvatar">＋</div><div class="mpPlayerInfo"><b>Waiting…</b><span class="muted">Open slot</span></div></div>');
 }
 return cards.join('');
}
function renderRoomLobby(){
 if(!multiplayer.role)return;
 const isHost=multiplayer.role==='host',label=multiplayer.transport==='wifi'?'Wi-Fi / Hotspot':'Bluetooth';
 $('mpTitle').textContent=(isHost?'👑 Host Room':'🎮 Joined Room')+' · '+label;
 let connectInfo='';
 if(isHost&&multiplayer.transport==='wifi')connectInfo='<div class="mpRoomCode">Host IP: '+mpEsc(safeWifiAddress())+'</div><div class="muted">Give this IP to players on the same Wi-Fi/hotspot.</div>';
 else if(isHost)connectInfo='<div class="mpRoomCode">Bluetooth Room '+mpEsc(multiplayer.roomId||'')+'</div><div class="muted">Joined phones must select this paired host phone.</div>';
 else connectInfo='<div class="mpRoomCode">Room '+mpEsc(multiplayer.roomId||'')+'</div><div class="muted">You are joined. Wait for the host to start.</div>';
 const count=(multiplayer.roster||[]).length;
 $('mpBody').innerHTML='<div class="mpRoomTop"><span class="pill">'+label+'</span><span class="pill">Players '+count+'/'+ROOM_MAX_PLAYERS+'</span><span class="pill">First to '+multiplayer.scoreLimit+'</span></div>'+connectInfo+'<div class="mpRuleBar"><div class="mpRule card"><strong>+1</strong>AI BOT</div><div class="mpRule card"><strong>+3</strong>PLAYER</div><div class="mpRule card"><strong>'+ROOM_BOTS+'</strong>AI BOTS</div></div><h3 class="yellow">Players in Room</h3><div class="mpPlayers">'+roomPlayerCards()+'</div>'+
 (isHost?'<div class="panel" style="padding:12px;margin-top:10px"><label><b>Score limit</b></label><input id="roomScoreLimit" class="mpInput" type="number" min="5" max="100" step="5" value="'+multiplayer.scoreLimit+'" onchange="hostChangeScoreLimit(this.value)"><div class="mpStartWrap"><button class="primary" '+(count<2?'disabled style="opacity:.55"':'')+' onclick="hostStartRoomGame()">START GAME</button></div><div class="muted" style="text-align:center;margin-top:8px">Only the host can start.</div></div>':'<div class="mpWaitingHost">⏳ WAITING FOR HOST TO START…<br><span class="muted">You do not need a Start button.</span></div>')+
 '<div style="text-align:center;margin-top:12px"><button class="secondary" onclick="leaveRoomToLobby(true)">LEAVE ROOM</button></div>';
 setMpStatus(isHost?(count<2?'Room open. Waiting for at least one player…':'Players joined. Start whenever you are ready.'):'Joined successfully. Waiting for the host…',count>=2||!isHost?'ok':'wait');
}
function hostChangeScoreLimit(value){
 if(multiplayer.role!=='host'||multiplayer.phase!=='room')return;multiplayer.scoreLimit=clamp(Math.round(Number(value)||20),5,100);broadcastRoomState();renderRoomLobby();
}
function broadcastRoomState(){
 if(multiplayer.role!=='host')return;
 sendLocalPacket({t:'room_state',roomId:multiplayer.roomId,scoreLimit:multiplayer.scoreLimit,maxPlayers:ROOM_MAX_PLAYERS,roster:multiplayer.roster.map(publicRoomPlayer)});
}
function publicRoomPlayer(p){return{id:p.id,name:p.name,body:p.body,head:p.head,accent:p.accent,host:!!p.host}}
function sendLocalPacket(packet,peerId){
 if(!nativeLocalNet())return;const raw=JSON.stringify(packet);
 try{if(peerId&&multiplayer.role==='host'&&LocalNet.sendTo)LocalNet.sendTo(peerId,raw);else LocalNet.send(raw)}catch(e){}
}
function sendJoinRequest(){sendLocalPacket({t:'join_request',clientId:roomClientId,profile:localProfile()})}
function handleJoinRequest(packet,peerId){
 if(multiplayer.role!=='host'||multiplayer.phase!=='room'||!peerId)return;
 const cid=String(packet.clientId||'').replace(/[^A-Za-z0-9_-]/g,'').slice(0,40);if(!cid)return;
 if(multiplayer.roster.length>=ROOM_MAX_PLAYERS&&!multiplayer.roster.some(function(p){return p.id===cid})){
  sendLocalPacket({t:'room_error',message:'Room is full.'},peerId);setTimeout(function(){try{LocalNet.disconnectPeer(peerId)}catch(e){}},220);return;
 }
 const prof=packet.profile||{};let item=multiplayer.roster.find(function(p){return p.id===cid});
 const clean={id:cid,name:sanitizePlayerName(prof.name)||'Player',body:String(prof.body||'#ff8f5a').slice(0,20),head:String(prof.head||prof.body||'#ffae76').slice(0,20),accent:String(prof.accent||'#fff').slice(0,20),host:false,peerId:peerId};
 if(item)Object.assign(item,clean);else multiplayer.roster.push(clean);
 multiplayer.peerToClient[peerId]=cid;multiplayer.scores[cid]=multiplayer.scores[cid]||0;multiplayer.connected=true;broadcastRoomState();renderRoomLobby();
}
function handleRoomState(packet){
 if(multiplayer.role!=='guest')return;
 multiplayer.connected=true;multiplayer.phase='room';multiplayer.roomId=String(packet.roomId||'');multiplayer.scoreLimit=clamp(Number(packet.scoreLimit)||20,5,100);multiplayer.roster=Array.isArray(packet.roster)?packet.roster.slice(0,ROOM_MAX_PLAYERS):[];
 multiplayer.scores={};multiplayer.roster.forEach(function(p){multiplayer.scores[p.id]=0});renderRoomLobby();
}
function hostStartRoomGame(){
 if(multiplayer.role!=='host'||multiplayer.phase!=='room')return;
 if(multiplayer.roster.length<2){toast('At least 2 players are required.');return}
 const input=$('roomScoreLimit');if(input)multiplayer.scoreLimit=clamp(Math.round(Number(input.value)||multiplayer.scoreLimit),5,100);
 multiplayer.matchId='M'+Date.now().toString(36)+Math.random().toString(36).slice(2,6);multiplayer.scores={};multiplayer.roster.forEach(function(p){multiplayer.scores[p.id]=0});
 const spawns=makeRoomSpawns(multiplayer.roster);
 const packet={t:'arena_start',roomId:multiplayer.roomId,matchId:multiplayer.matchId,scoreLimit:multiplayer.scoreLimit,botCount:ROOM_BOTS,roster:multiplayer.roster.map(publicRoomPlayer),spawns:spawns};
 sendLocalPacket(packet);beginRoomMatch(packet);
}
function makeRoomSpawns(roster){
 const out={},cx=WORLD/2,cy=WORLD/2,r=620;roster.forEach(function(p,i){const a=(Math.PI*2*i)/Math.max(2,roster.length);out[p.id]={x:wrap(cx+Math.cos(a)*r),y:wrap(cy+Math.sin(a)*r),a:a+Math.PI}});return out;
}
function placeFreshSnake(s,p){
 const q=p||safeSpawn();s.x=wrap(Number(q.x)||WORLD/2);s.y=wrap(Number(q.y)||WORLD/2);s.angle=Number.isFinite(Number(q.a))?Number(q.a):rand(-Math.PI,Math.PI);s.alive=true;s.length=PLAYER_START_LENGTH;s.energy=1;s.speed=BASE_SPEED;s.score=0;s.history=[];s.segments=[];
 for(let i=0;i<180;i++)s.history.push({x:s.x,y:s.y});s.updateBodySize();s.syncSegments();
}
function roomProfileById(id){return multiplayer.roster.find(function(p){return p.id===id})||{id:id,name:'Player',body:'#ff8f5a',head:'#ffb77c',accent:'#fff'}}
function makeRoomHuman(profile,isLocal,spawn){
 const skin=isLocal?currentSkin():null,s=new Snake(profile.name||'Player',isLocal?skin.body:(profile.body||'#ff8f5a'),!!isLocal);s.isRoomHuman=true;s.playerId=profile.id;s.isRemote=!isLocal;s.remoteHead=profile.head||profile.body||'#ffb77c';s.remoteAccent=profile.accent||'#fff';placeFreshSnake(s,spawn);return s;
}
function beginRoomMatch(packet){
 cleanupPreviousMatch(false);
 multiplayer.active=true;multiplayer.connected=true;multiplayer.phase='playing';multiplayer.roomId=String(packet.roomId||multiplayer.roomId||'');multiplayer.matchId=String(packet.matchId||'');multiplayer.scoreLimit=clamp(Number(packet.scoreLimit)||20,5,100);multiplayer.roster=Array.isArray(packet.roster)?packet.roster.slice(0,ROOM_MAX_PLAYERS):multiplayer.roster;multiplayer.scores={};multiplayer.roster.forEach(function(p){multiplayer.scores[p.id]=0});multiplayer.remoteTargets={};multiplayer.lastSend=0;multiplayer.lastSnapshot=0;multiplayer.winnerId=null;remotePlayers=new Map();
 gameState=GAME_STATE.STARTING;showScreen('gameScreen');clearMatchOverlays();if($('multiplayerModal'))$('multiplayerModal').classList.remove('show');if($('roomRespawn'))$('roomRespawn').classList.remove('show');
 run={fruits:0,bots:0,coins:0,xp:0,maxLength:PLAYER_START_LENGTH,startLevel:data.level,startXP:data.xp,elapsed:0,missionSurvivalBase:data.missions.survival};runStart=performance.now();lastMinuteReward=0;lastMissionSave=performance.now();
 foods=[];snakes=[];for(let i=0;i<760;i++)spawnFood();
 const me=roomProfileById(roomClientId);player=makeRoomHuman(me,true,(packet.spawns||{})[roomClientId]);snakes.push(player);
 multiplayer.roster.forEach(function(profile){if(profile.id===roomClientId)return;const s=makeRoomHuman(profile,false,(packet.spawns||{})[profile.id]);snakes.push(s);remotePlayers.set(profile.id,s)});
 if(multiplayer.role==='host'){
  for(let i=0;i<ROOM_BOTS;i++){const b=new Snake('Arena Bot '+(i+1),BOT_COLORS[i%BOT_COLORS.length],false);b.isRoomBot=true;b.roomEntityId='B'+i;snakes.push(b)}
 }
 rebuildFoodGrid();rebuildBodyGrid();joystick.lastAngle=player.angle;boost=false;boostPointerId=null;pointer.down=false;pointer.lastMove=0;$('boostBtn').classList.remove('active');$('emoteBtn').textContent=currentEmote().emoji;applyControlLayout();
 data.stats.gamesPlayed++;saveData();started=true;paused=false;gameState=GAME_STATE.PLAYING;last=performance.now();toast('Score race started — first to '+multiplayer.scoreLimit+'!');
 if(multiplayer.role==='host')sendRoomSnapshot(performance.now(),true);else sendLocalState(performance.now(),true);
}
function ensureRemoteEntity(id,profile,isBot){
 let s=remotePlayers.get(id);if(s)return s;
 const p=profile||roomProfileById(id);s=new Snake(p.name||(isBot?'AI Bot':'Player'),p.body||(isBot?'#ff8f5a':'#57d9ff'),false);s.isRemote=true;s.isRoomHuman=!isBot;s.isRoomBot=!!isBot;s.playerId=isBot?null:id;s.roomEntityId=id;s.remoteHead=p.head||p.body||s.color;s.remoteAccent=p.accent||'#fff';placeFreshSnake(s,{x:WORLD/2,y:WORLD/2,a:0});snakes.push(s);remotePlayers.set(id,s);return s;
}
function safeNet(v,f){const n=Number(v);return Number.isFinite(n)?n:f}
function stateOfSnake(s,id){return{id:id,x:+s.x.toFixed(1),y:+s.y.toFixed(1),a:+s.angle.toFixed(4),l:+s.length.toFixed(2),e:+s.energy.toFixed(2),r:+s.radius.toFixed(2),alive:!!s.alive}}
function sendLocalState(now,force){
 if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='guest'||!player)return;const interval=multiplayer.transport==='bluetooth'?85:50;if(!force&&now-multiplayer.lastSend<interval)return;multiplayer.lastSend=now;sendLocalPacket(Object.assign({t:'player_state',matchId:multiplayer.matchId,clientId:roomClientId},stateOfSnake(player,roomClientId)));
}
function sendRoomSnapshot(now,force){
 if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='host')return;const interval=multiplayer.transport==='bluetooth'?125:75;if(!force&&now-multiplayer.lastSnapshot<interval)return;multiplayer.lastSnapshot=now;
 const humans=multiplayer.roster.map(function(p){const s=p.id===roomClientId?player:remotePlayers.get(p.id);return s?stateOfSnake(s,p.id):{id:p.id,alive:false}});
 const bots=snakes.filter(function(s){return s.isRoomBot}).map(function(s){return stateOfSnake(s,s.roomEntityId)});
 sendLocalPacket({t:'arena_snapshot',matchId:multiplayer.matchId,humans:humans,bots:bots,scores:multiplayer.scores,limit:multiplayer.scoreLimit});
}
function handlePlayerState(packet,peerId){
 if(multiplayer.role!=='host'||multiplayer.phase!=='playing'||String(packet.matchId)!==multiplayer.matchId)return;
 const expected=multiplayer.peerToClient[peerId];const cid=String(packet.clientId||'');if(!expected||cid!==expected)return;
 const s=remotePlayers.get(cid);if(!s)return;multiplayer.remoteTargets[cid]={x:wrap(safeNet(packet.x,s.x)),y:wrap(safeNet(packet.y,s.y)),a:safeNet(packet.a,s.angle),l:clamp(safeNet(packet.l,PLAYER_START_LENGTH),PLAYER_START_LENGTH,900),e:clamp(safeNet(packet.e,1),0,1),r:clamp(safeNet(packet.r,6.2),5,13),alive:packet.alive!==false};
}
function handleArenaSnapshot(packet){
 if(multiplayer.role!=='guest'||multiplayer.phase!=='playing'||String(packet.matchId)!==multiplayer.matchId)return;
 multiplayer.scores=packet.scores||multiplayer.scores;multiplayer.scoreLimit=Number(packet.limit)||multiplayer.scoreLimit;
 (packet.humans||[]).forEach(function(t){if(t.id===roomClientId)return;const p=roomProfileById(t.id),s=ensureRemoteEntity(t.id,p,false);multiplayer.remoteTargets[t.id]=normalizeTarget(t,s)});
 (packet.bots||[]).forEach(function(t){const s=ensureRemoteEntity(t.id,{name:'AI Bot',body:'#ff8f5a',head:'#ffb875',accent:'#fff'},true);multiplayer.remoteTargets[t.id]=normalizeTarget(t,s)});
}
function normalizeTarget(t,s){return{x:wrap(safeNet(t.x,s.x)),y:wrap(safeNet(t.y,s.y)),a:safeNet(t.a,s.angle),l:clamp(safeNet(t.l,PLAYER_START_LENGTH),PLAYER_START_LENGTH,900),e:clamp(safeNet(t.e,1),0,1),r:clamp(safeNet(t.r,s.radius),5,13),alive:t.alive!==false}}
function updateRemoteEntities(dt){
 remotePlayers.forEach(function(s,id){const t=multiplayer.remoteTargets[id];if(!s||!t)return;const k=1-Math.exp(-14*dt);s.x=wrap(s.x+delta(s.x,t.x)*k);s.y=wrap(s.y+delta(s.y,t.y)*k);s.angle+=angleDiff(s.angle,t.a)*Math.min(1,16*dt);s.length=t.l;s.energy=t.e;s.radius=t.r;s.alive=t.alive;
  if(!s.alive)return;s.history.push({x:s.x,y:s.y});const required=Math.max(180,Math.floor(Math.min(s.length,900)*s.spacing+80));if(s.history.length>required+220)s.history.splice(0,Math.min(220,s.history.length-required));s.syncSegments();const hs=Math.max(1,s.history.length-1);for(let i=0;i<s.segments.length;i++){const idx=Math.max(0,hs-(i+1)*s.spacing),q=s.history[idx]||s.history[0];s.segments[i].x=q.x;s.segments[i].y=q.y}
 });
}
function roomSnakeDie(victim,killer){
 if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='host'||!victim||!victim.alive)return;
 victim.alive=false;
 if(victim.isRoomHuman){
  awardRoomKill(killer,victim);sendLocalPacket({t:'human_dead',matchId:multiplayer.matchId,id:victim.playerId,killer:killer&&killer.isRoomHuman?killer.playerId:null});scheduleRoomRespawn(victim,1500);
 }else if(victim.isRoomBot){
  awardRoomKill(killer,victim);scheduleRoomRespawn(victim,850+Math.random()*650);
 }
}
function awardRoomKill(killer,victim){
 if(!killer||!killer.isRoomHuman||!killer.playerId)return;const points=victim.isRoomBot?AI_KILL_POINTS:(victim.isRoomHuman&&victim.playerId!==killer.playerId?PLAYER_KILL_POINTS:0);if(!points)return;
 const id=killer.playerId;multiplayer.scores[id]=(multiplayer.scores[id]||0)+points;sendLocalPacket({t:'score_event',matchId:multiplayer.matchId,id:id,points:points,scores:multiplayer.scores});
 if(id===roomClientId)coinFeedback(points);
 if(multiplayer.scores[id]>=multiplayer.scoreLimit)endRoomMatch(id);
}
function scheduleRoomRespawn(snake,delay){
 const gen=matchGeneration,mid=multiplayer.matchId;const id=setTimeout(function(){matchTimeouts.delete(id);if(gen!==matchGeneration||multiplayer.phase!=='playing'||mid!==multiplayer.matchId||multiplayer.role!=='host')return;if(snake.isRoomHuman){const p=safeSpawn(),spawn={x:p.x,y:p.y,a:rand(-Math.PI,Math.PI)};placeFreshSnake(snake,spawn);sendLocalPacket({t:'human_respawn',matchId:mid,id:snake.playerId,spawn:spawn})}else if(snake.isRoomBot){snake.respawn(false)}},delay);matchTimeouts.add(id);
}
function handleHumanDead(packet){
 if(String(packet.matchId)!==multiplayer.matchId)return;const id=String(packet.id||''),s=id===roomClientId?player:remotePlayers.get(id);if(s)s.alive=false;if(id===roomClientId){boost=false;releaseBoost();if($('roomRespawn'))$('roomRespawn').classList.add('show')}
}
function handleHumanRespawn(packet){
 if(String(packet.matchId)!==multiplayer.matchId)return;const id=String(packet.id||''),s=id===roomClientId?player:remotePlayers.get(id);if(s)placeFreshSnake(s,packet.spawn||{});if(id===roomClientId){joystick.lastAngle=player.angle;if($('roomRespawn'))$('roomRespawn').classList.remove('show');toast('Respawned!')}
}
function roomCollisionCheck(){
 if(multiplayer.role!=='host'||multiplayer.phase!=='playing')return;
 for(const attacker of snakes){if(!attacker.alive)continue;const buckets=neighborBuckets(bodyGrid,attacker.x,attacker.y,BODY_CELL,BODY_CELLS,1);let hit=false;for(const b of buckets){for(const item of b){if(!attacker.alive||item.owner===attacker||!item.owner.alive)continue;if(distance(attacker.x,attacker.y,item.x,item.y)<attacker.radius+item.r-1.2){roomSnakeDie(attacker,item.owner);hit=true;break}}if(hit)break}}
 for(let i=0;i<snakes.length;i++){const a=snakes[i];if(!a.alive)continue;for(let j=i+1;j<snakes.length;j++){const b=snakes[j];if(!b.alive)continue;if(distance(a.x,a.y,b.x,b.y)<a.radius+b.radius-3){roomSnakeDie(a,null);roomSnakeDie(b,null)}}}
}
function endRoomMatch(winnerId){
 if(multiplayer.phase!=='playing')return;multiplayer.phase='ended';multiplayer.winnerId=winnerId;clearMatchTimeouts();const packet={t:'match_end',matchId:multiplayer.matchId,winnerId:winnerId,scores:multiplayer.scores};if(multiplayer.role==='host')sendLocalPacket(packet);showRoomResult(packet);
}
function showRoomResult(packet){
 multiplayer.scores=packet.scores||multiplayer.scores;multiplayer.winnerId=packet.winnerId||null;multiplayer.phase='ended';gameState=GAME_STATE.GAME_OVER;started=false;paused=false;boost=false;releaseJoystick();if($('roomRespawn'))$('roomRespawn').classList.remove('show');
 const winner=roomProfileById(multiplayer.winnerId),won=multiplayer.winnerId===roomClientId;$('postTitle').textContent=won?'YOU WIN!':mpEsc(winner.name)+' WINS!';
 const ordered=multiplayer.roster.slice().sort(function(a,b){return(multiplayer.scores[b.id]||0)-(multiplayer.scores[a.id]||0)});$('postStats').innerHTML=ordered.map(function(p,i){return '<div class="postStat card"><small>#'+(i+1)+' '+mpEsc(p.name)+'</small><strong>'+(multiplayer.scores[p.id]||0)+'</strong></div>'}).join('');$('xpSummary').innerHTML='<b class="yellow">FIRST TO '+multiplayer.scoreLimit+' POINTS</b><div class="muted" style="margin-top:6px">AI bot kill +1 · Player kill +3 · Players respawn after each death.</div>';clearMatchOverlays();$('postModal').classList.add('show');run=null;
}
function returnRoomToLobby(){
 cleanupPreviousMatch(false);multiplayer.active=false;multiplayer.phase='room';multiplayer.matchId=null;multiplayer.winnerId=null;multiplayer.scores={};multiplayer.roster.forEach(function(p){multiplayer.scores[p.id]=0});gameState=GAME_STATE.MENU;showScreen('lobby');$('multiplayerModal').classList.add('show');if(multiplayer.role==='host')broadcastRoomState();renderRoomLobby();
}
function postPlayAgain(){if(multiplayer.role&&multiplayer.connected){returnRoomToLobby();return}startNewMatch()}
function postMainMenu(){if(multiplayer.role||multiplayer.connected){leaveRoomToLobby(true);return}returnToMenuFromGameOver()}
function restartRoomMatch(){if(multiplayer.role!=='host'){toast('Only the host can restart the room match.');return}hostStartRoomGame()}
function leaveRoomToLobby(sendNotice){
 if(sendNotice&&multiplayer.connected)sendLocalPacket({t:'leave_room',clientId:roomClientId});cleanupPreviousMatch(false);try{if(nativeLocalNet())LocalNet.disconnect()}catch(e){}resetMultiplayerConnectionState();gameState=GAME_STATE.MENU;showScreen('lobby');if($('multiplayerModal'))$('multiplayerModal').classList.remove('show');
}
function disconnectLocalMultiplayer(silent){leaveRoomToLobby(false);if(!silent)toast('Local room closed.')}
function removeRoomPlayerByPeer(peerId){
 const cid=multiplayer.peerToClient[peerId];if(!cid)return;delete multiplayer.peerToClient[peerId];multiplayer.roster=multiplayer.roster.filter(function(p){return p.id!==cid});delete multiplayer.scores[cid];multiplayer.remoteTargets[cid]=null;const s=remotePlayers.get(cid);if(s){s.alive=false;remotePlayers.delete(cid);snakes=snakes.filter(function(x){return x!==s})}if(multiplayer.phase==='room'){broadcastRoomState();renderRoomLobby()}else if(multiplayer.phase==='playing'){sendLocalPacket({t:'player_left',matchId:multiplayer.matchId,id:cid});if(multiplayer.roster.length<2)endRoomMatch(roomClientId)}
}
function handleLocalPacket(packet,peerId){
 if(!packet||typeof packet!=='object')return;
 if(packet.t==='join_request'){handleJoinRequest(packet,peerId);return}
 if(packet.t==='room_state'){handleRoomState(packet);return}
 if(packet.t==='room_error'){setMpStatus(packet.message||'Could not join room.','error');return}
 if(packet.t==='arena_start'){if(multiplayer.role==='guest')beginRoomMatch(packet);return}
 if(packet.t==='player_state'){handlePlayerState(packet,peerId);return}
 if(packet.t==='arena_snapshot'){handleArenaSnapshot(packet);return}
 if(packet.t==='human_dead'){handleHumanDead(packet);return}
 if(packet.t==='human_respawn'){handleHumanRespawn(packet);return}
 if(packet.t==='score_event'&&String(packet.matchId)===multiplayer.matchId){multiplayer.scores=packet.scores||multiplayer.scores;return}
 if(packet.t==='match_end'&&String(packet.matchId)===multiplayer.matchId){showRoomResult(packet);return}
 if(packet.t==='player_left'&&String(packet.matchId)===multiplayer.matchId){const id=String(packet.id||''),s=remotePlayers.get(id);if(s){s.alive=false;remotePlayers.delete(id);snakes=snakes.filter(function(x){return x!==s})}multiplayer.roster=multiplayer.roster.filter(function(p){return p.id!==id});return}
 if(packet.t==='leave_room'&&multiplayer.role==='host'&&peerId){setTimeout(function(){try{LocalNet.disconnectPeer(peerId)}catch(e){}},80);return}
}
function onLocalNetEvent(raw){
 let evt;try{evt=typeof raw==='string'?JSON.parse(raw):raw}catch(e){return}if(!evt)return;
 if(evt.type==='message'){let packet;try{packet=JSON.parse(evt.data)}catch(e){return}handleLocalPacket(packet,evt.peerId||null);return}
 if(evt.type!=='status')return;const state=String(evt.state||'');
 if(state==='hosting'){
  multiplayer.connected=true;if(multiplayer.role==='host'){renderRoomLobby();setMpStatus(multiplayer.transport==='wifi'?'Room open at '+(evt.address||safeWifiAddress())+'. Waiting for players…':'Bluetooth room open. Waiting for paired players…','wait')}return;
 }
 if(state==='peer_connected'){multiplayer.connected=true;setMpStatus('A phone connected. Adding player to room…','wait');return}
 if(state==='peer_disconnected'){if(multiplayer.role==='host')removeRoomPlayerByPeer(String(evt.peerId||''));return}
 if(state==='connected'){
  multiplayer.connected=true;if(multiplayer.role==='guest'){setMpStatus('Connected. Joining host room…','ok');setTimeout(sendJoinRequest,80)}return;
 }
 if(state==='connecting'){setMpStatus(evt.message||'Connecting…','wait');return}
 if(state==='permission_requested'){setMpStatus('Allow Nearby devices / Bluetooth permission.','wait');return}
 if(state==='permission_granted'){setMpStatus('Bluetooth permission allowed.','ok');if(multiplayer.transport==='bluetooth'&&multiplayer.role==='guest')setTimeout(refreshBluetoothList,100);return}
 if(state==='paired_ready'){if(multiplayer.role==='guest')setTimeout(refreshBluetoothList,60);return}
 if(state==='room_full'){setMpStatus('Host room is full.','error');return}
 if(state==='error'||state==='permission_denied'){setMpStatus(evt.message||'Local connection failed.','error');return}
 if(state==='disconnected'||state==='closed'){
  if(multiplayer.role==='guest'&&(multiplayer.phase==='room'||multiplayer.phase==='playing'||multiplayer.phase==='connecting')){toast(evt.message||'Host disconnected.');leaveRoomToLobby(false)}
 }
}
function updateRoomHUD(){
 if(!player)return;const ordered=multiplayer.roster.slice().sort(function(a,b){return(multiplayer.scores[b.id]||0)-(multiplayer.scores[a.id]||0)}),myScore=multiplayer.scores[roomClientId]||0,myRank=Math.max(1,ordered.findIndex(function(p){return p.id===roomClientId})+1);$('score').textContent=myScore;$('length').textContent=Math.floor(player.length);$('rank').textContent=myRank+'/'+ordered.length;$('runCoins').textContent=run?run.coins:0;$('gameDifficulty').textContent=(multiplayer.transport==='wifi'?'WIFI':'BLUETOOTH')+' · '+myScore+'/'+multiplayer.scoreLimit;$('leaderList').innerHTML=ordered.map(function(p){return '<li style="'+(p.id===roomClientId?'color:#ffd45e;font-weight:900':'')+'">'+mpEsc(p.name)+' — '+(multiplayer.scores[p.id]||0)+'</li>'}).join('');if(emoteUntil>performance.now()){const q=screenPos(player.x,player.y,currentZoom());$('emoteBubble').style.display='block';$('emoteBubble').style.left=(q.x-16)+'px';$('emoteBubble').style.top=(q.y-55)+'px'}else $('emoteBubble').style.display='none';
}
''',
    "multiplayer functions"
)

# ---------- Multiplayer collision branch ----------
rep(
    "function collisionCheck(){\n for(const attacker of snakes){",
    "function collisionCheck(){\n if(multiplayer.active){roomCollisionCheck();return}\n for(const attacker of snakes){",
    "collision check"
)

# ---------- Multiplayer death is host authoritative ----------
rep(
    " die(killer){\n  if(!this.alive)return;",
    " die(killer){\n  if(multiplayer.active&&multiplayer.phase==='playing'){if(multiplayer.role==='host')roomSnakeDie(this,killer);return}\n  if(!this.alive)return;",
    "snake die"
)

# ---------- Remote humans/bots are not simulated locally ----------
rep(
    "for(const s of activeSnakes){if(s&&s.alive)s.update(dt)}",
    "for(const s of activeSnakes){if(s&&s.alive&&!s.isRemote)s.update(dt)}",
    "active snake update"
)

# ---------- Remote head/accent colors ----------
rep(
    "const body=skin?skin.body:s.color,head=skin?skin.head:s.color,accent=skin?skin.accent:'#ffffff';",
    "const body=skin?skin.body:s.color,head=skin?skin.head:(s.remoteHead||s.color),accent=skin?skin.accent:(s.remoteAccent||'#ffffff');",
    "draw remote colors"
)

# ---------- Room HUD ----------
rep(
    "function updateHUD(){\n const alive=snakes.filter(function(s){return s.alive}).sort(function(a,b){return(b.score+b.length*2)-(a.score+a.length*2)});",
    "function updateHUD(){\n if(multiplayer.active&&multiplayer.phase==='playing'){updateRoomHUD();return}\n const alive=snakes.filter(function(s){return s.alive}).sort(function(a,b){return(b.score+b.length*2)-(a.score+a.length*2)});",
    "room HUD"
)

# ---------- Single-player post title ----------
rep(
    "function finishMatch(){\n if(!run||gameState!==GAME_STATE.PLAYING)return;",
    "function finishMatch(){\n if(!run||gameState!==GAME_STATE.PLAYING)return;\n $('postTitle').textContent='GAME OVER';",
    "finish title"
)

# ---------- Single-player play leaves any room ----------
rep(
    "function startNewMatch(){\n if(!beginTransitionLock())return;",
    "function startNewMatch(){\n if(multiplayer.role||multiplayer.connected){leaveRoomToLobby(false)}\n if(!beginTransitionLock())return;",
    "single start"
)

# ---------- Top reset/menu are room aware ----------
rep(
    "function restartMatch(){\n startNewMatch();\n}",
    "function restartMatch(){\n if(multiplayer.active||multiplayer.phase==='ended'){restartRoomMatch();return}\n startNewMatch();\n}",
    "restart"
)
rep(
    "function quitToLobby(){\n if(!beginTransitionLock())return;",
    "function quitToLobby(){\n if(multiplayer.role||multiplayer.connected){leaveRoomToLobby(true);return}\n if(!beginTransitionLock())return;",
    "quit"
)

# ---------- Frame continues during multiplayer respawn + networking ----------
rep(
    "if(gameState===GAME_STATE.PLAYING&&started&&!paused&&run&&player&&player.alive){\n  rebuildFoodGrid();rebuildBodyGrid();",
    "if(gameState===GAME_STATE.PLAYING&&started&&!paused&&run&&player&&(player.alive||multiplayer.active)){\n  if(multiplayer.active)updateRemoteEntities(dt);\n  rebuildFoodGrid();rebuildBodyGrid();",
    "frame room update"
)
rep(
    "if(now-lastMissionSave>1800){data.missions.survival=Math.max(data.missions.survival,run.missionSurvivalBase+Math.floor(survival));scheduleSave();lastMissionSave=now}\n }",
    "if(now-lastMissionSave>1800){data.missions.survival=Math.max(data.missions.survival,run.missionSurvivalBase+Math.floor(survival));scheduleSave();lastMissionSave=now}\n  if(multiplayer.active){if(multiplayer.role==='host')sendRoomSnapshot(now,false);else sendLocalState(now,false)}\n }",
    "frame network send"
)

# ---------- Android back closes/leaves room correctly ----------
rep(
    "window.handleAndroidBack=function(){\n if($('dailyModal').classList.contains('show'))",
    "window.handleAndroidBack=function(){\n if($('multiplayerModal').classList.contains('show')){if(multiplayer.role||multiplayer.connected)leaveRoomToLobby(true);else $('multiplayerModal').classList.remove('show');return true}\n if($('dailyModal').classList.contains('show'))",
    "android back"
)

# ---------- Export room actions ----------
rep(
    "window.openDaily=openDaily;window.claimDaily=claimDaily;window.openMissions=openMissions;",
    "window.openLocalMultiplayer=openLocalMultiplayer;window.closeMultiplayerModal=closeMultiplayerModal;window.renderMpHome=renderMpHome;window.selectMultiplayerTransport=selectMultiplayerTransport;window.chooseMultiplayerRole=chooseMultiplayerRole;window.cancelRoomSetup=cancelRoomSetup;window.createHostRoom=createHostRoom;window.joinWifiRoom=joinWifiRoom;window.refreshBluetoothList=refreshBluetoothList;window.joinBluetoothRoom=joinBluetoothRoom;window.hostChangeScoreLimit=hostChangeScoreLimit;window.hostStartRoomGame=hostStartRoomGame;window.leaveRoomToLobby=leaveRoomToLobby;window.disconnectLocalMultiplayer=disconnectLocalMultiplayer;window.onLocalNetEvent=onLocalNetEvent;window.postPlayAgain=postPlayAgain;window.postMainMenu=postMainMenu;window.openDaily=openDaily;window.claimDaily=claimDaily;window.openMissions=openMissions;",
    "exports"
)

# ---------- Validation ----------
required = [
    "Wi-Fi / Hotspot",
    "Bluetooth",
    "HOST ROOM",
    "JOIN ROOM",
    "Players in Room",
    "Only the host can start",
    "function hostStartRoomGame()",
    "function roomCollisionCheck()",
    "function sendRoomSnapshot(now,force)",
    "function handlePlayerState(packet,peerId)",
    "AI_KILL_POINTS=1",
    "PLAYER_KILL_POINTS=3",
    "ROOM_MAX_PLAYERS=4",
    "PLAYER_START_LENGTH=3",
    "window.onLocalNetEvent=onLocalNetEvent",
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit("Multiplayer room patch incomplete: " + ", ".join(missing))

Path("/tmp/game-multiplayer.html").write_text(html, encoding="utf-8")
print("Multiplayer room patch applied")
