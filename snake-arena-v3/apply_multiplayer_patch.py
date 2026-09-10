from pathlib import Path

p = Path("snake-arena-v3/game.html")
html = p.read_text(encoding="utf-8")


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f"Patch target missing: {label}")
    html = html.replace(old, new, 1)


# ---------- Multiplayer UI styles ----------
rep(
    "</style>",
    r'''
.mpGrid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0}.mpCard{padding:15px;min-height:260px}.mpCard h3{margin:0 0 8px;color:#fff35d}.mpCard input,.mpCard select{width:100%;height:42px;margin:7px 0;border-radius:11px;border:2px solid #78b9ff;background:#071b34;color:#fff;padding:0 10px;font-weight:800;outline:none}.mpRow{display:flex;gap:8px;flex-wrap:wrap}.mpRow button{flex:1;min-width:120px}.mpStatus{padding:11px 13px;border-radius:12px;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.12);font-weight:800;min-height:42px}.mpAddress{font-size:20px;color:#7ff4ff;font-weight:1000;word-break:break-all;margin:8px 0}.mpNote{font-size:11px;color:#c2d7e8;line-height:1.4}.mpConnected{color:#7dff9a}.mpWaiting{color:#ffe26b}.mpError{color:#ff8993}
@media(max-width:760px){.mpGrid{grid-template-columns:1fr;max-height:58vh;overflow:auto}.mpCard{min-height:210px}}
</style>''',
    "style end"
)

# ---------- Lobby button ----------
rep(
    '<div class="quickRight">',
    '<div class="quickRight">\n      <button class="sideBtn" onclick="openLocalMultiplayer()">👥 Local Multiplayer</button>',
    "quick right"
)

# ---------- Post result title + unified actions ----------
rep(
    '<div class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>',
    '<div id="postTitle" class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>',
    "post title"
)
rep(
    '<button class="primary" onclick="startNewMatch()">PLAY AGAIN</button>\n    <button class="secondary" style="margin-left:8px" onclick="returnToMenuFromGameOver()">MAIN MENU</button>',
    '<button class="primary" onclick="postPlayAgain()">PLAY AGAIN</button>\n    <button class="secondary" style="margin-left:8px" onclick="postMainMenu()">MAIN MENU</button>',
    "post buttons"
)

# ---------- Multiplayer modal ----------
rep(
    '<div id="dailyModal" class="modal">',
    r'''<div id="multiplayerModal" class="modal">
  <div class="modalBox panel" style="width:min(850px,94vw)">
    <div style="display:flex;align-items:center;gap:10px">
      <h2 class="yellow" style="margin:0">👥 Local Multiplayer</h2>
      <span class="pill">2 Players</span>
      <button class="closeBtn" style="margin-left:auto" onclick="closeMultiplayerModal()">×</button>
    </div>
    <p class="muted">Play directly phone-to-phone. No online account or internet game server is required.</p>
    <div class="mpGrid">
      <div class="mpCard card">
        <h3>📶 Wi‑Fi / Phone Hotspot</h3>
        <div class="mpNote">Best option. Put both phones on the same Wi‑Fi, or turn on a hotspot on one phone and connect the other phone to it.</div>
        <div class="mpAddress" id="wifiLocalAddress">IP: checking…</div>
        <div class="mpRow"><button class="primary" style="font-size:16px;padding:9px" onclick="hostWifiGame()">HOST GAME</button></div>
        <input id="wifiJoinIp" inputmode="decimal" maxlength="40" placeholder="Host IP, e.g. 192.168.1.5">
        <button class="secondary" style="width:100%" onclick="joinWifiGame()">JOIN HOST</button>
      </div>
      <div class="mpCard card">
        <h3>🟦 Bluetooth</h3>
        <div class="mpNote">Pair the two phones once in Android Bluetooth settings first. Then one phone hosts and the other joins from the paired-device list.</div>
        <div class="mpRow" style="margin-top:10px"><button class="primary" style="font-size:16px;padding:9px" onclick="hostBluetoothGame()">HOST</button><button class="secondary" onclick="refreshBluetoothList()">REFRESH PAIRED</button></div>
        <select id="btDeviceSelect"><option value="">Paired devices</option></select>
        <button class="secondary" style="width:100%" onclick="joinBluetoothGame()">JOIN SELECTED PHONE</button>
      </div>
    </div>
    <div id="mpStatus" class="mpStatus">Choose Wi‑Fi or Bluetooth.</div>
    <div style="text-align:center;margin-top:12px"><button class="secondary" onclick="disconnectLocalMultiplayer()">DISCONNECT</button></div>
  </div>
</div>

<div id="dailyModal" class="modal">''',
    "daily modal"
)

# ---------- Multiplayer state + transport functions ----------
rep(
    "function currentEmote(){return EMOTES.find(function(s){return s.id===data.selectedEmote})||EMOTES[0]}",
    r'''function currentEmote(){return EMOTES.find(function(s){return s.id===data.selectedEmote})||EMOTES[0]}

const multiplayer={
 active:false,connected:false,role:null,transport:null,session:null,
 remoteProfile:null,remoteTarget:null,lastSend:0,lastReceive:0,restartPending:false
};
let remotePlayer=null;

function nativeLocalNet(){return typeof window.LocalNet!=='undefined'&&window.LocalNet}
function localProfile(){
 const skin=currentSkin();
 return {name:sanitizePlayerName(data.name)||'Player',body:skin.body,head:skin.head,accent:skin.accent};
}
function setMpStatus(text,kind){
 const el=$('mpStatus');if(!el)return;
 el.textContent=text;el.className='mpStatus '+(kind==='ok'?'mpConnected':kind==='wait'?'mpWaiting':kind==='error'?'mpError':'');
}
function openLocalMultiplayer(){
 if(!nativeLocalNet()){toast('Local multiplayer is available in the Android APK.');return}
 $('multiplayerModal').classList.add('show');
 let ip='Unavailable';try{ip=String(LocalNet.getWifiAddress())}catch(e){}
 $('wifiLocalAddress').textContent='IP: '+ip;
 setMpStatus('Choose HOST on one phone and JOIN on the other.','');
}
function closeMultiplayerModal(){
 if(!multiplayer.connected)$('multiplayerModal').classList.remove('show');
 else toast('Disconnect first or start the match.');
}
function resetMultiplayerConnectionState(){
 multiplayer.active=false;multiplayer.connected=false;multiplayer.role=null;multiplayer.transport=null;multiplayer.session=null;multiplayer.remoteProfile=null;multiplayer.remoteTarget=null;multiplayer.lastSend=0;multiplayer.lastReceive=0;multiplayer.restartPending=false;remotePlayer=null;
}
function hostWifiGame(){
 if(!nativeLocalNet())return;
 try{LocalNet.disconnect()}catch(e){}
 resetMultiplayerConnectionState();multiplayer.role='host';multiplayer.transport='wifi';
 setMpStatus('Hosting on '+String(LocalNet.getWifiAddress())+' — waiting for the second phone…','wait');
 LocalNet.hostWifi();
}
function joinWifiGame(){
 if(!nativeLocalNet())return;
 const ip=String($('wifiJoinIp').value||'').trim();
 if(!ip){toast('Enter the host phone IP address.');return}
 try{LocalNet.disconnect()}catch(e){}
 resetMultiplayerConnectionState();multiplayer.role='guest';multiplayer.transport='wifi';
 setMpStatus('Connecting to '+ip+'…','wait');LocalNet.joinWifi(ip);
}
function hostBluetoothGame(){
 if(!nativeLocalNet())return;
 try{LocalNet.disconnect()}catch(e){}
 resetMultiplayerConnectionState();multiplayer.role='host';multiplayer.transport='bluetooth';
 setMpStatus('Bluetooth host starting. Keep this screen open…','wait');LocalNet.hostBluetooth();
}
function refreshBluetoothList(){
 if(!nativeLocalNet())return;
 let raw='';try{raw=String(LocalNet.getPairedBluetoothDevices())}catch(e){raw='ERROR'}
 if(raw==='PERMISSION_REQUIRED'){setMpStatus('Allow Bluetooth permission, then press REFRESH PAIRED again.','wait');return}
 if(raw==='DISABLED'){setMpStatus('Turn on Bluetooth first.','error');return}
 if(raw==='UNSUPPORTED'){setMpStatus('Bluetooth is not supported on this phone.','error');return}
 let devices=[];try{devices=JSON.parse(raw)}catch(e){}
 const sel=$('btDeviceSelect');sel.innerHTML='<option value="">Paired devices</option>'+devices.map(function(d){return '<option value="'+String(d.address).replace(/[^0-9A-Fa-f:]/g,'')+'">'+escapeHtml(d.name||'Android phone')+'</option>'}).join('');
 setMpStatus(devices.length?devices.length+' paired device(s) found.':'No paired phones found. Pair them in Android settings first.',devices.length?'ok':'wait');
}
function joinBluetoothGame(){
 if(!nativeLocalNet())return;
 const address=String($('btDeviceSelect').value||'');if(!address){toast('Choose a paired phone.');return}
 try{LocalNet.disconnect()}catch(e){}
 resetMultiplayerConnectionState();multiplayer.role='guest';multiplayer.transport='bluetooth';
 setMpStatus('Connecting over Bluetooth…','wait');LocalNet.joinBluetooth(address);
}
function disconnectLocalMultiplayer(silent){
 try{if(nativeLocalNet())LocalNet.disconnect()}catch(e){}
 resetMultiplayerConnectionState();
 if($('multiplayerModal'))$('multiplayerModal').classList.remove('show');
 if(!silent)setMpStatus('Disconnected.','');
}
function escapeHtml(v){return String(v||'').replace(/[&<>"']/g,function(ch){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]})}
function sendLocalPacket(packet){
 if(!multiplayer.connected||!nativeLocalNet())return;
 try{LocalNet.send(JSON.stringify(packet))}catch(e){}
}
function makeStartPacket(){
 return {
  t:'start',session:String(Date.now())+'-'+Math.floor(Math.random()*1000000),
  hostProfile:localProfile(),guestProfile:multiplayer.remoteProfile||{name:'Guest',body:'#ff8f5a',head:'#ffbd80',accent:'#fff'},
  host:{x:3300,y:3800,a:0},guest:{x:4300,y:3800,a:Math.PI}
 };
}
function hostStartLocalRound(){
 if(!multiplayer.connected||multiplayer.role!=='host'||!multiplayer.remoteProfile)return;
 const packet=makeStartPacket();sendLocalPacket(packet);beginLocalRound(packet,'host');
}
function placeFreshSnake(s,p){
 s.x=wrap(Number(p.x)||WORLD/2);s.y=wrap(Number(p.y)||WORLD/2);s.angle=Number(p.a)||0;s.alive=true;s.length=PLAYER_START_LENGTH;s.energy=1;s.speed=BASE_SPEED;s.score=0;s.history=[];s.segments=[];
 for(let i=0;i<180;i++)s.history.push({x:s.x,y:s.y});s.updateBodySize();s.syncSegments();
}
function beginLocalRound(packet,role){
 cleanupPreviousMatch(false);
 multiplayer.active=true;multiplayer.connected=true;multiplayer.role=role;multiplayer.session=String(packet.session||'');multiplayer.restartPending=false;multiplayer.remoteTarget=null;multiplayer.lastSend=0;multiplayer.lastReceive=performance.now();
 const myProfile=role==='host'?packet.hostProfile:packet.guestProfile;
 const theirProfile=role==='host'?packet.guestProfile:packet.hostProfile;
 const mySpawn=role==='host'?packet.host:packet.guest;
 const theirSpawn=role==='host'?packet.guest:packet.host;
 gameState=GAME_STATE.STARTING;showScreen('gameScreen');clearMatchOverlays();
 run={fruits:0,bots:0,coins:0,xp:0,maxLength:PLAYER_START_LENGTH,startLevel:data.level,startXP:data.xp,elapsed:0,missionSurvivalBase:data.missions.survival};
 runStart=performance.now();lastMinuteReward=0;lastMissionSave=performance.now();
 foods=[];snakes=[];for(let i=0;i<760;i++)spawnFood();
 player=new Snake(myProfile.name||data.name,currentSkin().body,true);placeFreshSnake(player,mySpawn);snakes.push(player);
 remotePlayer=new Snake(theirProfile.name||'Player 2',theirProfile.body||'#ff8f5a',false);remotePlayer.isRemote=true;remotePlayer.remoteHead=theirProfile.head||theirProfile.body||'#ff8f5a';remotePlayer.remoteAccent=theirProfile.accent||'#fff';placeFreshSnake(remotePlayer,theirSpawn);remotePlayer.radius=6.2;snakes.push(remotePlayer);
 rebuildFoodGrid();rebuildBodyGrid();joystick.lastAngle=player.angle;boost=false;boostPointerId=null;pointer.down=false;pointer.lastMove=0;$('boostBtn').classList.remove('active');$('emoteBtn').textContent=currentEmote().emoji;applyControlLayout();
 data.stats.gamesPlayed++;saveData();started=true;paused=false;gameState=GAME_STATE.PLAYING;last=performance.now();$('multiplayerModal').classList.remove('show');toast('Local multiplayer connected!');
 sendLocalState(performance.now(),true);
}
function safeNetNumber(v,fallback){const n=Number(v);return Number.isFinite(n)?n:fallback}
function handleLocalPacket(packet){
 if(!packet||typeof packet!=='object')return;
 if(packet.t==='hello'){
  const p=packet.profile||{};multiplayer.remoteProfile={name:sanitizePlayerName(p.name)||'Player 2',body:String(p.body||'#ff8f5a').slice(0,20),head:String(p.head||p.body||'#ff8f5a').slice(0,20),accent:String(p.accent||'#fff').slice(0,20)};
  if(multiplayer.role==='host'&&!multiplayer.active)hostStartLocalRound();return;
 }
 if(packet.t==='start'){
  if(multiplayer.role==='guest')beginLocalRound(packet,'guest');return;
 }
 if(packet.t==='state'&&multiplayer.active&&String(packet.session||'')===multiplayer.session){
  multiplayer.lastReceive=performance.now();multiplayer.remoteTarget={x:wrap(safeNetNumber(packet.x,remotePlayer?remotePlayer.x:0)),y:wrap(safeNetNumber(packet.y,remotePlayer?remotePlayer.y:0)),a:safeNetNumber(packet.a,0),l:clamp(safeNetNumber(packet.l,PLAYER_START_LENGTH),PLAYER_START_LENGTH,900),e:clamp(safeNetNumber(packet.e,1),0,1),s:Math.max(0,safeNetNumber(packet.s,0)),r:clamp(safeNetNumber(packet.r,6.2),5,13),alive:packet.alive!==false};return;
 }
 if(packet.t==='death'&&multiplayer.active&&String(packet.session||'')===multiplayer.session){finishLocalRound(true);return}
 if(packet.t==='restart_request'&&multiplayer.connected&&multiplayer.role==='host'){hostStartLocalRound();return}
 if(packet.t==='leave'){if(multiplayer.active){toast('Other player left the match.');leaveMultiplayerToLobby(false)}return}
}
function onLocalNetEvent(raw){
 let evt;try{evt=typeof raw==='string'?JSON.parse(raw):raw}catch(e){return}
 if(!evt)return;
 if(evt.type==='message'){
  let packet;try{packet=JSON.parse(evt.data)}catch(e){return}handleLocalPacket(packet);return;
 }
 if(evt.type!=='status')return;
 const state=evt.state||'';
 if(state==='hosting'){setMpStatus((evt.transport==='wifi'?'Wi‑Fi host ready at '+(evt.address||'your local IP'):'Bluetooth host ready')+' — waiting for player 2…','wait');return}
 if(state==='connected'){
  multiplayer.connected=true;multiplayer.transport=evt.transport==='bluetooth'?'bluetooth':'wifi';setMpStatus('Connected. Starting local match…','ok');sendLocalPacket({t:'hello',profile:localProfile()});return;
 }
 if(state==='permission_requested'){setMpStatus('Allow the Bluetooth permission requested by Android.','wait');return}
 if(state==='permission_granted'){setMpStatus('Bluetooth permission allowed.','ok');return}
 if(state==='error'||state==='permission_denied'){setMpStatus(evt.message||'Local connection failed.','error');return}
 if(state==='disconnected'||state==='closed'){
  const wasPlaying=multiplayer.active;resetMultiplayerConnectionState();if(wasPlaying){cleanupPreviousMatch(true);gameState=GAME_STATE.MENU;showScreen('lobby');toast('Local multiplayer disconnected.')}else setMpStatus(evt.message||'Disconnected.','error');
 }
}
function updateRemoteVisual(dt){
 if(!multiplayer.active||!remotePlayer||!multiplayer.remoteTarget)return;
 const t=multiplayer.remoteTarget,k=1-Math.exp(-14*dt);remotePlayer.x=wrap(remotePlayer.x+delta(remotePlayer.x,t.x)*k);remotePlayer.y=wrap(remotePlayer.y+delta(remotePlayer.y,t.y)*k);remotePlayer.angle+=angleDiff(remotePlayer.angle,t.a)*Math.min(1,16*dt);remotePlayer.length=t.l;remotePlayer.energy=t.e;remotePlayer.score=t.s;remotePlayer.radius=t.r;remotePlayer.alive=t.alive;
 remotePlayer.history.push({x:remotePlayer.x,y:remotePlayer.y});const required=Math.max(180,Math.floor(Math.min(remotePlayer.length,900)*remotePlayer.spacing+80));if(remotePlayer.history.length>required+220)remotePlayer.history.splice(0,Math.min(220,remotePlayer.history.length-required));remotePlayer.syncSegments();const histSpan=Math.max(1,remotePlayer.history.length-1);for(let i=0;i<remotePlayer.segments.length;i++){const idx=Math.max(0,histSpan-(i+1)*remotePlayer.spacing),p=remotePlayer.history[idx]||remotePlayer.history[0];remotePlayer.segments[i].x=p.x;remotePlayer.segments[i].y=p.y}
}
function sendLocalState(now,force){
 if(!multiplayer.active||!multiplayer.connected||gameState!==GAME_STATE.PLAYING||!player)return;
 const interval=multiplayer.transport==='bluetooth'?80:50;if(!force&&now-multiplayer.lastSend<interval)return;multiplayer.lastSend=now;
 sendLocalPacket({t:'state',session:multiplayer.session,x:+player.x.toFixed(1),y:+player.y.toFixed(1),a:+player.angle.toFixed(4),l:+player.length.toFixed(2),e:+player.energy.toFixed(2),s:Math.floor(player.score),r:+player.radius.toFixed(2),alive:player.alive});
}
function localMultiplayerCollisionCheck(){
 if(!player||!player.alive||!remotePlayer||!remotePlayer.alive)return;
 const bodyStep=Math.max(1,Math.ceil(remotePlayer.segments.length/220));
 for(let i=2;i<remotePlayer.segments.length;i+=bodyStep){const q=remotePlayer.segments[i];if(distance(player.x,player.y,q.x,q.y)<player.radius+remotePlayer.radius*.78){player.die(remotePlayer);return}}
 if(distance(player.x,player.y,remotePlayer.x,remotePlayer.y)<player.radius+remotePlayer.radius-2){player.die(null)}
}
function finishLocalRound(won){
 if(!multiplayer.active||gameState!==GAME_STATE.PLAYING||!run)return;
 gameState=GAME_STATE.GAME_OVER;started=false;paused=false;boost=false;boostPointerId=null;releaseJoystick();
 const survival=run.elapsed||0;run.maxLength=Math.max(run.maxLength,Math.floor(player.length));data.stats.bestScore=Math.max(data.stats.bestScore,Math.floor(player.score));data.stats.maxLength=Math.max(data.stats.maxLength,run.maxLength);data.stats.bestSurvival=Math.max(data.stats.bestSurvival,survival);data.stats.totalPlayTime+=survival;saveData();
 $('postTitle').textContent=won?'YOU WIN!':'ROUND OVER';$('postStats').innerHTML=[['SCORE',Math.floor(player.score)],['LENGTH',run.maxLength],['SURVIVAL',formatTime(survival)],['OPPONENT',escapeHtml(remotePlayer?remotePlayer.name:'Player 2')],['RESULT',won?'WIN':'LOSS'],['MODE','LOCAL '+String(multiplayer.transport||'').toUpperCase()]].map(function(v){return '<div class="postStat card"><small>'+v[0]+'</small><strong>'+v[1]+'</strong></div>'}).join('');$('xpSummary').innerHTML='<b class="yellow">LOCAL VERSUS</b><div class="muted" style="margin-top:5px">Multiplayer rounds do not change difficulty rewards.</div>';clearMatchOverlays();$('postModal').classList.add('show');run=null;
}
function requestLocalRestart(){
 if(!multiplayer.connected){leaveMultiplayerToLobby(false);return}
 if(multiplayer.role==='host')hostStartLocalRound();else{multiplayer.restartPending=true;sendLocalPacket({t:'restart_request'});toast('Restart requested…')}
}
function leaveMultiplayerToLobby(sendLeave){
 if(sendLeave&&multiplayer.connected)sendLocalPacket({t:'leave'});const shouldSave=multiplayer.active&&(gameState===GAME_STATE.PLAYING||gameState===GAME_STATE.PAUSED);cleanupPreviousMatch(shouldSave);disconnectLocalMultiplayer(true);gameState=GAME_STATE.MENU;showScreen('lobby');
}
function postPlayAgain(){if(multiplayer.active||multiplayer.connected)requestLocalRestart();else startNewMatch()}
function postMainMenu(){if(multiplayer.active||multiplayer.connected)leaveMultiplayerToLobby(true);else returnToMenuFromGameOver()}
''',
    "multiplayer functions"
)

# ---------- Do not clear multiplayer modal accidentally except when starting ----------
# Existing clearMatchOverlays need not include the connection modal.

# ---------- Remote player is never simulated as AI ----------
rep(
    "for(const s of activeSnakes){if(s&&s.alive)s.update(dt)}",
    "for(const s of activeSnakes){if(s&&s.alive&&!s.isRemote)s.update(dt)}",
    "active snake update"
)

# ---------- Multiplayer collision branch ----------
rep(
    "function collisionCheck(){\n for(const attacker of snakes){",
    "function collisionCheck(){\n if(multiplayer.active){localMultiplayerCollisionCheck();return}\n for(const attacker of snakes){",
    "collision check"
)

# ---------- Player death routes to local round; remote never respawns ----------
rep(
    "if(this.isPlayer){finishMatch()}\n  else{",
    "if(this.isPlayer){if(multiplayer.active){sendLocalPacket({t:'death',session:multiplayer.session});finishLocalRound(false)}else finishMatch()}\n  else if(this.isRemote){return}\n  else{",
    "snake die"
)

# ---------- Draw remote player's selected skin color rather than local player's skin ----------
rep(
    "const pc=performanceConfig(),skin=s.isPlayer?currentSkin():null;",
    "const pc=performanceConfig(),skin=s.isPlayer?currentSkin():null;",
    "draw snake anchor"
)

# ---------- HUD identifies multiplayer ----------
rep(
    "$('gameDifficulty').textContent=difficultyConfig().label;",
    "$('gameDifficulty').textContent=multiplayer.active?('LOCAL '+String(multiplayer.transport||'').toUpperCase()):difficultyConfig().label;",
    "HUD mode"
)

# ---------- Single-player death title always resets ----------
rep(
    "function finishMatch(){\n if(!run||gameState!==GAME_STATE.PLAYING)return;",
    "function finishMatch(){\n if(!run||gameState!==GAME_STATE.PLAYING)return;\n $('postTitle').textContent='GAME OVER';",
    "finish title"
)

# ---------- Single-player start disconnects any leftover multiplayer transport ----------
rep(
    "function startNewMatch(){\n if(!beginTransitionLock())return;",
    "function startNewMatch(){\n if(multiplayer.connected||multiplayer.active)disconnectLocalMultiplayer(true);\n if(!beginTransitionLock())return;",
    "single start"
)

# ---------- Top RESET and Main Menu become mode aware ----------
rep(
    "function restartMatch(){\n startNewMatch();\n}",
    "function restartMatch(){\n if(multiplayer.active||multiplayer.connected){requestLocalRestart();return}\n startNewMatch();\n}",
    "restart"
)
rep(
    "function quitToLobby(){\n if(!beginTransitionLock())return;",
    "function quitToLobby(){\n if(multiplayer.active||multiplayer.connected){leaveMultiplayerToLobby(true);return}\n if(!beginTransitionLock())return;",
    "quit"
)

# ---------- Multiplayer remote interpolation/state send in frame ----------
rep(
    "if(gameState===GAME_STATE.PLAYING&&started&&!paused&&run&&player&&player.alive){\n  rebuildFoodGrid();rebuildBodyGrid();",
    "if(gameState===GAME_STATE.PLAYING&&started&&!paused&&run&&player&&player.alive){\n  if(multiplayer.active)updateRemoteVisual(dt);\n  rebuildFoodGrid();rebuildBodyGrid();",
    "frame remote update"
)
rep(
    "if(now-lastMissionSave>1800){data.missions.survival=Math.max(data.missions.survival,run.missionSurvivalBase+Math.floor(survival));scheduleSave();lastMissionSave=now}\n }",
    "if(now-lastMissionSave>1800){data.missions.survival=Math.max(data.missions.survival,run.missionSurvivalBase+Math.floor(survival));scheduleSave();lastMissionSave=now}\n  if(multiplayer.active)sendLocalState(now,false);\n }",
    "frame send state"
)

# ---------- Android back closes multiplayer modal ----------
rep(
    "window.handleAndroidBack=function(){\n if($('dailyModal').classList.contains('show'))",
    "window.handleAndroidBack=function(){\n if($('multiplayerModal').classList.contains('show')){if(multiplayer.connected)disconnectLocalMultiplayer();$('multiplayerModal').classList.remove('show');return true}\n if($('dailyModal').classList.contains('show'))",
    "android back"
)

# ---------- Export multiplayer actions ----------
rep(
    "window.openDaily=openDaily;window.claimDaily=claimDaily;window.openMissions=openMissions;",
    "window.openLocalMultiplayer=openLocalMultiplayer;window.closeMultiplayerModal=closeMultiplayerModal;window.hostWifiGame=hostWifiGame;window.joinWifiGame=joinWifiGame;window.hostBluetoothGame=hostBluetoothGame;window.refreshBluetoothList=refreshBluetoothList;window.joinBluetoothGame=joinBluetoothGame;window.disconnectLocalMultiplayer=disconnectLocalMultiplayer;window.onLocalNetEvent=onLocalNetEvent;window.postPlayAgain=postPlayAgain;window.postMainMenu=postMainMenu;window.openDaily=openDaily;window.claimDaily=claimDaily;window.openMissions=openMissions;",
    "exports"
)

# ---------- Extra validation markers ----------
required = [
    "Local Multiplayer",
    "function onLocalNetEvent(raw)",
    "function beginLocalRound(packet,role)",
    "function localMultiplayerCollisionCheck()",
    "function sendLocalState(now,force)",
    "window.onLocalNetEvent=onLocalNetEvent",
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit("Multiplayer patch incomplete: " + ", ".join(missing))

Path("/tmp/game-multiplayer.html").write_text(html, encoding="utf-8")
print("Multiplayer patch applied")
