from pathlib import Path
import re

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global html
    if old not in html:
        raise SystemExit(f'v5.1 target missing: {label}')
    html = html.replace(old, new, count)

# -----------------------------------------------------------------------------
# 1) Lobby game-mode selector + zonal HUD styling.
# -----------------------------------------------------------------------------
css = r'''
.matchModeSection{margin:4px 0 7px;padding:7px 9px;background:rgba(0,0,0,.28);border:1px solid rgba(255,255,255,.12);border-radius:15px;text-align:center;min-width:min(410px,55vw)}
.matchModeTitle{font-size:10px;letter-spacing:1.6px;color:#a9c8e2;font-weight:1000;margin-bottom:5px}.matchModeButtons{display:flex;gap:7px;justify-content:center}.matchModeBtn{min-width:145px;padding:8px 12px;border-radius:11px;border:2px solid rgba(255,255,255,.16);font-size:12px;font-weight:1000;color:#eaf6ff;background:linear-gradient(#376b9f,#224c78);box-shadow:0 3px 0 rgba(0,0,0,.3)}.matchModeBtn.active.infinite{background:linear-gradient(#47b8f6,#236fb7);border-color:#93ddff}.matchModeBtn.active.zonal{background:linear-gradient(#ffb943,#e36b22);border-color:#ffe19b;color:#371700}.matchModeHint{font-size:9px;color:#bdd4e6;font-weight:800;margin-top:5px;min-height:11px}
#zoneHud{display:none;position:absolute;left:50%;top:58px;transform:translateX(-50%);min-width:270px;text-align:center;padding:7px 12px;font-size:11px;z-index:11;border-color:rgba(92,225,255,.42)}#zoneHud.show{display:block}#zoneHud.warning{border-color:#ff6874;background:rgba(97,8,16,.9);color:#ffd1d5;animation:zonePulse .65s infinite alternate}@keyframes zonePulse{to{box-shadow:0 0 24px rgba(255,65,75,.48)}}
@media(max-height:430px){.matchModeSection{margin:1px 0 3px;padding:4px 6px;min-width:min(350px,52vw)}.matchModeTitle{display:none}.matchModeBtn{min-width:112px;padding:5px 8px;font-size:10px}.matchModeHint{font-size:8px;margin-top:3px}.centerLobby .snakePreview{margin:2px 0;height:70px}#zoneHud{top:46px;min-width:220px;padding:5px 9px;font-size:9px}}
'''
rep('</style>', css + '\n</style>', 'style close')

mode_html = '''<div class="matchModeSection">\n        <div class="matchModeTitle">GAME MODE</div>\n        <div class="matchModeButtons">\n          <button id="mode-infinite" class="matchModeBtn infinite" onclick="setGameMode('infinite')">∞ INFINITE MATCH</button>\n          <button id="mode-zonal" class="matchModeBtn zonal" onclick="setGameMode('zonal')">◉ ZONAL MATCH</button>\n        </div>\n        <div id="gameModeHint" class="matchModeHint"></div>\n      </div>\n      <div class="difficultySelect">'''
rep('<div class="difficultySelect">', mode_html, 'lobby difficulty selector')

rep(
    '<div id="gameTopActions">',
    '<div id="zoneHud" class="hudBox"></div>\n    <div id="gameTopActions">',
    'game top actions'
)
rep(
    '<div class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>',
    '<div id="postTitle" class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>',
    'post match title'
)

# -----------------------------------------------------------------------------
# 2) Persist selected mode and render lobby selector.
# -----------------------------------------------------------------------------
rep(
    "name:'Player',coins:500,level:1,xp:0,difficulty:'medium',",
    "name:'Player',coins:500,level:1,xp:0,difficulty:'medium',gameMode:'infinite',",
    'default game mode'
)

mode_funcs = r'''
function selectedGameMode(){return data.gameMode==='zonal'?'zonal':'infinite'}
function setGameMode(mode){
 if(mode!=='infinite'&&mode!=='zonal')return;
 data.gameMode=mode;saveData();renderGameModeSelector();
}
function renderGameModeSelector(){
 const mode=selectedGameMode();
 const a=$('mode-infinite'),b=$('mode-zonal');
 if(a)a.classList.toggle('active',mode==='infinite');
 if(b)b.classList.toggle('active',mode==='zonal');
 const hint=$('gameModeHint');
 if(hint)hint.textContent=mode==='zonal'
  ?'50 snakes · shrinking safe zone · no respawns · last snake standing wins'
  :'Endless arena · bots respawn forever · grow, fight and chase high scores';
}
'''
rep('function defaultData(){', mode_funcs + '\nfunction defaultData(){', 'defaultData insertion')
rep('  renderDifficultySelector();\n  resetDailyMissionsIfNeeded();', '  renderDifficultySelector();\n  renderGameModeSelector();\n  resetDailyMissionsIfNeeded();', 'render lobby game mode')

# -----------------------------------------------------------------------------
# 3) Zonal match engine. 50 total snakes, staged shrinking circle, no bot respawn.
# -----------------------------------------------------------------------------
zone_engine = r'''
const ZONE_STAGES=[
 {hold:14,shrink:22,radius:3600},
 {hold:9,shrink:20,radius:2450},
 {hold:8,shrink:18,radius:1600},
 {hold:7,shrink:16,radius:980},
 {hold:6,shrink:14,radius:560},
 {hold:5,shrink:12,radius:280}
];
let zoneState={active:false,x:WORLD/2,y:WORLD/2,radius:5450,fromRadius:5450,stage:0,stageTime:0,elapsed:0,resolving:false,winner:null};
function resetZoneState(){
 zoneState.active=false;zoneState.radius=5450;zoneState.fromRadius=5450;zoneState.stage=0;zoneState.stageTime=0;zoneState.elapsed=0;zoneState.resolving=false;zoneState.winner=null;
 const hud=$('zoneHud');if(hud){hud.classList.remove('show','warning');hud.textContent=''}
}
function isZonalMatch(){return !!zoneState.active}
function targetFoodCount(){return zoneState.active?1050:(data.gameMode==='zonal'?1050:FOOD_TARGET)}
function initZonalMatch(){
 resetZoneState();zoneState.active=true;zoneState.x=rand(0,WORLD);zoneState.y=rand(0,WORLD);
 // Exactly 50 snakes total: player + 49 AI.
 while(snakes.length>50)snakes.pop();
 for(const s of snakes){s.zoneOutside=0}
}
function zoneSecondsToChange(){
 if(!zoneState.active||zoneState.stage>=ZONE_STAGES.length)return 0;
 const st=ZONE_STAGES[zoneState.stage];return Math.max(0,Math.ceil(st.hold+st.shrink-zoneState.stageTime));
}
function checkZonalWinner(){
 if(!zoneState.active||zoneState.resolving||!run||gameState!==GAME_STATE.PLAYING)return;
 const alive=snakes.filter(function(s){return s.alive});
 if(alive.length===1){
  zoneState.winner=alive[0];
  if(alive[0]===player){run.zonalWinner=true;run.zonalPlacement=1;finishMatch()}
 }
}
function updateZonalMode(dt){
 if(!zoneState.active||gameState!==GAME_STATE.PLAYING)return;
 zoneState.elapsed+=dt;zoneState.stageTime+=dt;
 if(zoneState.stage<ZONE_STAGES.length){
  const st=ZONE_STAGES[zoneState.stage];
  if(zoneState.stageTime>st.hold){
   const t=clamp((zoneState.stageTime-st.hold)/st.shrink,0,1),smooth=t*t*(3-2*t);
   zoneState.radius=zoneState.fromRadius+(st.radius-zoneState.fromRadius)*smooth;
   if(t>=1){zoneState.radius=st.radius;zoneState.fromRadius=st.radius;zoneState.stage++;zoneState.stageTime=0}
  }
 }
 const toKill=[];
 for(const s of snakes){
  if(!s.alive)continue;
  const outside=distance(s.x,s.y,zoneState.x,zoneState.y)>zoneState.radius;
  if(outside){s.zoneOutside=(s.zoneOutside||0)+dt;if(s.zoneOutside>=1.05)toKill.push(s)}else{s.zoneOutside=0}
 }
 // Resolve everyone against the same zone snapshot before choosing a winner.
 zoneState.resolving=true;
 toKill.sort(function(a,b){return (a.isPlayer?1:0)-(b.isPlayer?1:0)});
 for(const s of toKill){if(s.alive)s.die(null)}
 zoneState.resolving=false;
 if(gameState===GAME_STATE.PLAYING)checkZonalWinner();
}
function drawZoneOverlay(zoom){
 if(!zoneState.active||!player)return;
 const p=screenPos(zoneState.x,zoneState.y,zoom),r=zoneState.radius*zoom;
 ctx.save();ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.lineWidth=5;ctx.strokeStyle='rgba(83,225,255,.9)';ctx.shadowColor='#32dfff';ctx.shadowBlur=14;ctx.stroke();ctx.shadowBlur=0;
 const outside=distance(player.x,player.y,zoneState.x,zoneState.y)>zoneState.radius;
 if(outside){ctx.fillStyle='rgba(255,36,48,.10)';ctx.fillRect(0,0,W,H)}ctx.restore();
}
function updateZoneHud(aliveCount){
 const hud=$('zoneHud');if(!hud)return;
 if(!zoneState.active){hud.classList.remove('show','warning');return}
 const outside=player&&player.alive&&distance(player.x,player.y,zoneState.x,zoneState.y)>zoneState.radius;
 hud.classList.add('show');hud.classList.toggle('warning',!!outside);
 if(outside)hud.textContent='⚠ RETURN TO SAFE ZONE · '+Math.max(0,1.05-(player.zoneOutside||0)).toFixed(1)+'s';
 else if(zoneState.stage<ZONE_STAGES.length)hud.textContent='◉ ZONE '+Math.ceil(zoneState.radius)+' · '+aliveCount+' ALIVE · SHRINK '+zoneSecondsToChange()+'s';
 else hud.textContent='◉ FINAL ZONE · '+aliveCount+' ALIVE';
}
'''
rep('const FOOD_CELL=190,', zone_engine + '\nconst FOOD_CELL=190,', 'zone engine after world constants')

# Slightly larger fruit visuals (loot/death food remains unchanged).
rep(
    " foods.push({x:wrap(x),y:wrap(y),v:v,r:r,loot:loot,golden:golden,alive:true,ttl:loot?45:1e9,phase:rand(0,Math.PI*2),emoji:currentFoodTheme().emoji[Math.random()*currentFoodTheme().emoji.length|0]});",
    " if(!loot)r*=1.22;\n foods.push({x:wrap(x),y:wrap(y),v:v,r:r,loot:loot,golden:golden,alive:true,ttl:loot?45:1e9,phase:rand(0,Math.PI*2),emoji:currentFoodTheme().emoji[Math.random()*currentFoodTheme().emoji.length|0]});",
    'larger fruit'
)

# Use fewer, larger fruits in Zonal mode for smoother Android rendering.
rep('foods=[];snakes=[];for(let i=0;i<FOOD_TARGET;i++)spawnFood();', 'foods=[];snakes=[];for(let i=0;i<targetFoodCount();i++)spawnFood();', 'initial food target')
rep('foods=foods.filter(function(f){return f.alive});while(foods.length<FOOD_TARGET)spawnFood();', 'foods=foods.filter(function(f){return f.alive});const foodTarget=targetFoodCount();while(foods.length<foodTarget)spawnFood();', 'food refill target')

# Bots close to the zone edge prioritize returning toward the safe centre.
rep(
    '  const p=this.ai.target;\n  const ta=Math.atan2(delta(this.y,p.y),delta(this.x,p.x));',
    "  if(zoneState.active){\n   const safeEdge=zoneState.radius-Math.min(320,Math.max(120,zoneState.radius*.13));\n   if(distance(this.x,this.y,zoneState.x,zoneState.y)>safeEdge){this.ai.target={x:zoneState.x,y:zoneState.y,type:'zone'};this.ai.boosting=false}\n  }\n  const p=this.ai.target;\n  const ta=Math.atan2(delta(this.y,p.y),delta(this.x,p.x));",
    'bot zone steering'
)

# No respawns in Zonal mode. Every dead snake still uses the existing edible loot drop.
rep(
    '   scheduleBotRespawn(this,650+Math.random()*900,matchGeneration);',
    '   if(zoneState.active){checkZonalWinner()}else{scheduleBotRespawn(this,650+Math.random()*900,matchGeneration)}',
    'disable zonal bot respawn'
)
rep(
    '  if(this.isPlayer){finishMatch()}',
    '  if(this.isPlayer){if(zoneState.active&&run)run.zonalPlacement=snakes.filter(function(s){return s.alive}).length+1;finishMatch()}',
    'zonal player placement'
)

# -----------------------------------------------------------------------------
# 4) Start/cleanup/frame integration.
# -----------------------------------------------------------------------------
rep(
    ' player=initWorld();\n joystick.lastAngle=player.angle;',
    " player=initWorld();\n if(data.gameMode==='zonal')initZonalMatch();else resetZoneState();\n joystick.lastAngle=player.angle;",
    'initialize selected match mode'
)
rep(' matchGeneration++;\n clearMatchTimeouts();', ' matchGeneration++;\n resetZoneState();\n clearMatchTimeouts();', 'cleanup zone state')
rep(
    '  rebuildBodyGrid();collisionCheck();updateFood(dt);rebuildFoodGrid();',
    '  rebuildBodyGrid();collisionCheck();if(zoneState.active&&gameState===GAME_STATE.PLAYING)updateZonalMode(dt);updateFood(dt);rebuildFoodGrid();',
    'frame zone update'
)
rep(
    '  const z=currentZoom();drawBackground(z);drawFood(now/1000,z);const order=snakes.slice().sort(function(a,b){return a.length-b.length});for(const s of order)drawSnake(s,z);if(renderFrameCount%performanceConfig().radarEvery===0)drawRadar();updateHUD();',
    '  const z=currentZoom();drawBackground(z);drawFood(now/1000,z);const order=snakes.slice().sort(function(a,b){return a.length-b.length});for(const s of order)drawSnake(s,z);drawZoneOverlay(z);if(renderFrameCount%performanceConfig().radarEvery===0)drawRadar();updateHUD();',
    'draw zone overlay'
)

# HUD shows alive count and zone status only in Zonal mode.
rep(
    "$('score').textContent=Math.floor(player.score);$('length').textContent=Math.floor(player.length);$('rank').textContent=player.alive?(alive.indexOf(player)+1)+'/'+alive.length:'-';$('runCoins').textContent=run?run.coins:0;$('gameDifficulty').textContent=difficultyConfig().label;",
    "$('score').textContent=Math.floor(player.score);$('length').textContent=Math.floor(player.length);$('rank').textContent=player.alive?(alive.indexOf(player)+1)+'/'+alive.length:'-';$('runCoins').textContent=run?run.coins:0;$('gameDifficulty').textContent=zoneState.active?('ZONAL · '+alive.length+' ALIVE'):('INFINITE · '+difficultyConfig().label);updateZoneHud(alive.length);",
    'zonal HUD'
)

# -----------------------------------------------------------------------------
# 5) Last-snake-standing placement + high champion reward.
# -----------------------------------------------------------------------------
rep(
    ' const survival=run.elapsed,rank=currentRank();run.maxLength=Math.max(run.maxLength,Math.floor(player.length));\n let placementCoins=0;if(rank===1){placementCoins+=100;data.stats.gamesWon++}else if(rank<=5)placementCoins+=50;if(placementCoins){run.coins+=placementCoins;addCoins(placementCoins)}',
    " const survival=run.elapsed;\n const zonal=zoneState.active;\n const rank=zonal?(run.zonalWinner?1:(run.zonalPlacement||Math.max(2,snakes.filter(function(s){return s.alive}).length+1))):currentRank();\n run.maxLength=Math.max(run.maxLength,Math.floor(player.length));\n let placementCoins=0;if(zonal){if(run.zonalWinner){placementCoins=1000;run.xp+=500;data.stats.gamesWon++}else if(rank<=5){placementCoins=100}}else{if(rank===1){placementCoins+=100;data.stats.gamesWon++}else if(rank<=5)placementCoins+=50}if(placementCoins){run.coins+=placementCoins;addCoins(placementCoins)}",
    'zonal rewards'
)
rep(
    "  ['SCORE',Math.floor(player.score)],['LENGTH',run.maxLength],['SURVIVAL',formatTime(survival)],['FRUITS',run.fruits],['BOTS',run.bots],['COINS','+'+run.coins],['XP','+'+run.xp],['RANK','#'+rank],['MODE',difficultyConfig().label]",
    "  ['SCORE',Math.floor(player.score)],['LENGTH',run.maxLength],['SURVIVAL',formatTime(survival)],['FRUITS',run.fruits],['BOTS',run.bots],['COINS','+'+run.coins],['XP','+'+run.xp],['RANK','#'+rank],['MODE',zonal?'ZONAL':'INFINITE'],['DIFFICULTY',difficultyConfig().label]",
    'post match mode stats'
)
rep(
    " $('postStats').innerHTML=[",
    " const postTitle=$('postTitle');if(postTitle)postTitle.textContent=zonal?(run.zonalWinner?'👑 ZONE CHAMPION!':'ELIMINATED'):'GAME OVER';\n $('postStats').innerHTML=[",
    'post title state'
)

# Make champion reward obvious in the XP summary.
rep(
    " $('xpSummary').innerHTML='<b class=\"yellow\">LEVEL '+run.startLevel+' → LEVEL '+data.level+'</b>",
    " $('xpSummary').innerHTML=(zonal&&run.zonalWinner?'<div class=\"good\" style=\"font-size:18px;font-weight:1000;margin-bottom:7px\">🏆 CHAMPION REWARD: 1,000 COINS + 500 XP</div>':'')+'<b class=\"yellow\">LEVEL '+run.startLevel+' → LEVEL '+data.level+'</b>",
    'champion reward summary'
)

# Export selector for the lobby buttons.
rep('window.showScreen=showScreen;window.setDifficulty=setDifficulty;', 'window.showScreen=showScreen;window.setDifficulty=setDifficulty;window.setGameMode=setGameMode;', 'game mode export')

required = [
    "gameMode:'infinite'",
    'id="mode-infinite"',
    'id="mode-zonal"',
    'function initZonalMatch()',
    'while(snakes.length>50)snakes.pop()',
    'function updateZonalMode(dt)',
    "placementCoins=1000;run.xp+=500",
    "if(zoneState.active){checkZonalWinner()}else{scheduleBotRespawn",
    'if(!loot)r*=1.22;',
    'drawZoneOverlay(z);',
    'window.setGameMode=setGameMode;'
]
missing=[x for x in required if x not in html]
if missing:
    raise SystemExit('v5.1 zonal patch incomplete: '+', '.join(missing))

p.write_text(html, encoding='utf-8')
print('v5.1 Infinite + Zonal last-snake-standing mode applied')
