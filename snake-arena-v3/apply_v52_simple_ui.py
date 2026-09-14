from pathlib import Path
import re

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global html
    if old not in html:
        raise SystemExit(f'v5.2 target missing: {label}')
    html = html.replace(old, new, count)


def sub(pattern, replacement, label, count=1):
    global html
    html, n = re.subn(pattern, replacement, html, count=count, flags=re.S)
    if n != count:
        raise SystemExit(f'v5.2 regex target missing: {label} ({n}/{count})')

# -----------------------------------------------------------------------------
# 1) Remove duplicate/overloaded lobby actions and keep four obvious bottom actions.
# Profile remains available from the player card. Shop/Upgrades remain inside Snakes.
# -----------------------------------------------------------------------------
sub(r'\n\s*<div class="sideMenu">.*?</div>\n', '\n', 'remove duplicate left menu')
sub(r'\n\s*<div class="quickRight">.*?</div>\n', '\n', 'remove duplicate right menu')

old_bottom = '''    <div class="bottomNav">\n      <button class="navBtn" onclick="showScreen('profile')"><span>👤</span>PROFILE</button>\n      <button class="navBtn" onclick="openMissions()"><span>🎯</span>MISSIONS</button>\n      <button class="navBtn" onclick="showScreen('wardrobe')"><span>🐍</span>WARDROBE</button>\n      <button class="navBtn" onclick="showScreen('wardrobe');setWardrobeTab('shop')"><span>🛒</span>SHOP</button>\n      <button class="navBtn" onclick="showScreen('settings')"><span>⚙️</span>SETTINGS</button>\n    </div>'''
new_bottom = '''    <div class="bottomNav simpleBottomNav">\n      <button class="navBtn" onclick="openDaily()" aria-label="Daily reward"><span>🎁</span>REWARD <i id="dailyBadge" class="badge">!</i></button>\n      <button class="navBtn" onclick="openMissions()" aria-label="Daily missions"><span>🎯</span>MISSIONS <i id="missionBadge" class="badge">!</i></button>\n      <button class="navBtn" onclick="showScreen('wardrobe')" aria-label="Snakes and shop"><span>🐍</span>SNAKES</button>\n      <button class="navBtn" onclick="showScreen('settings')" aria-label="Settings"><span>⚙️</span>SETTINGS</button>\n    </div>'''
rep(old_bottom, new_bottom, 'simple bottom navigation')

# Clearer lobby copy and touch labels.
rep('>∞ INFINITE MATCH</button>', '>♾️ INFINITE MATCH</button>', 'infinite mode label')
rep('>◉ ZONAL MATCH</button>', '>⭕ ZONAL MATCH</button>', 'zonal mode label')
rep('>MEDIUM</button>', '>NORMAL</button>', 'normal difficulty label')
rep(
    '<button class="primary playBtn" onclick="startNewMatch()">PLAY</button>',
    '<button id="playGameBtn" class="primary playBtn" onclick="safeStartMatch()" aria-label="Start selected match">PLAY</button>',
    'safe play button'
)
rep(
    '<div class="muted" style="margin-top:10px;font-weight:800">Start at length 3 · grow gradually by eating · 50 AI rivals · bots fight each other · offline</div>',
    '<div class="lobbyTip">🍎 Eat fruit & grow &nbsp; • &nbsp; 🐍 Avoid snake bodies</div>',
    'short lobby help'
)
rep('⌂ MAIN MENU</button>', '⌂ MENU</button>', 'short game menu label')
rep('<b>LEADERBOARD</b>', '<b>TOP SNAKES</b>', 'friendly leaderboard label')

# Short, child-readable difficulty hints while mechanics stay unchanged.
rep('Slower, more reckless bots. Easier to cut them off and make them crash.', 'Best for beginners.', 'easy hint')
rep('Balanced bot speed, reactions, fighting and body avoidance.', 'Balanced speed and smart bots.', 'normal hint')
rep('Faster smart bots: stronger avoidance, boosting, ambushes and interceptions.', 'Fast bots for a bigger challenge.', 'hard hint')

# -----------------------------------------------------------------------------
# 2) Clean gameplay HUD. Keep the same IDs so gameplay logic is untouched.
# -----------------------------------------------------------------------------
old_stats = '<div id="stats" class="hudBox">Score <b id="score">0</b><br>Length <b id="length">3</b><br>Rank <b id="rank">-</b><br>Coins <b id="runCoins">0</b><br>Mode <b id="gameDifficulty">MEDIUM</b></div>'
new_stats = '''<div id="stats" class="hudBox simpleStats">\n      <span>⭐ <b id="score">0</b></span><span>📏 <b id="length">3</b></span><span>🏁 <b id="rank">-</b></span><span>🪙 <b id="runCoins">0</b></span><span class="modeStat"><b id="gameDifficulty">NORMAL</b></span>\n    </div>'''
rep(old_stats, new_stats, 'compact gameplay stats')

# The old reset button is easy to hit accidentally. Restart is still available after a match.
# Hiding it also frees the top centre for Zonal information.

# -----------------------------------------------------------------------------
# 3) Robust start guard: repeated child taps cannot launch overlapping matches.
# -----------------------------------------------------------------------------
mode_pattern = r'''function renderGameModeSelector\(\)\{\n const mode=selectedGameMode\(\);\n const a=\$\('mode-infinite'\),b=\$\('mode-zonal'\);\n if\(a\)a\.classList\.toggle\('active',mode==='infinite'\);\n if\(b\)b\.classList\.toggle\('active',mode==='zonal'\);\n const hint=\$\('gameModeHint'\);\n if\(hint\)hint\.textContent=mode==='zonal'\n  \?'50 snakes · shrinking safe zone · no respawns · last snake standing wins'\n  :'Endless arena · bots respawn forever · grow, fight and chase high scores';\n\}'''
mode_replacement = r'''function renderGameModeSelector(){
 const mode=selectedGameMode();
 const a=$('mode-infinite'),b=$('mode-zonal'),play=$('playGameBtn');
 if(a)a.classList.toggle('active',mode==='infinite');
 if(b)b.classList.toggle('active',mode==='zonal');
 const hint=$('gameModeHint');
 if(hint)hint.textContent=mode==='zonal'
  ?'Safe zone shrinks. Last snake alive wins!'
  :'Play forever. Bots keep coming back.';
 if(play)play.textContent=mode==='zonal'?'PLAY ZONAL':'PLAY INFINITE';
}'''
sub(mode_pattern, mode_replacement, 'friendly game mode renderer')

start_guard = r'''
let uiStartLocked=false;
function safeStartMatch(){
 if(uiStartLocked)return;
 uiStartLocked=true;
 const btn=$('playGameBtn');if(btn){btn.disabled=true;btn.classList.add('starting');btn.textContent='STARTING…'}
 try{startNewMatch()}finally{
  setTimeout(function(){uiStartLocked=false;if(btn){btn.disabled=false;btn.classList.remove('starting');renderGameModeSelector()}},650);
 }
}
'''
rep('function selectedGameMode(){', start_guard + '\nfunction selectedGameMode(){', 'safe start function')

# -----------------------------------------------------------------------------
# 4) Child-friendly visual system and responsive phone fixes.
# -----------------------------------------------------------------------------
css = r'''
/* v5.2 simple child-friendly UI */
button{touch-action:manipulation;min-height:44px}
button:active{filter:brightness(1.08)}
#lobby{background:radial-gradient(circle at 50% 42%,rgba(46,145,210,.20),transparent 34%),linear-gradient(180deg,#071c32,#04101e)}
#lobby:before{opacity:.08;background-size:42px 42px}
.lobbyHUD{grid-template-columns:1fr 1fr;grid-template-rows:70px minmax(0,1fr) 70px;gap:8px;padding:10px 14px}
.profileChip{grid-column:1;grid-row:1;width:min(205px,42vw);padding:7px 9px;border-width:2px;border-radius:16px;background:linear-gradient(180deg,#2d78ba,#20598c);border-color:#82d8ff;box-shadow:0 5px 16px rgba(0,0,0,.28)}
.avatar{width:46px;height:46px;font-size:25px;border-radius:13px}.levelBox b{font-size:16px}.levelBox{font-size:11px}
.lobbyWallet{grid-column:2;grid-row:1;justify-self:end;align-self:start}.lobbyWallet .wallet{font-size:17px;padding:6px 10px}.coinIcon{width:28px;height:28px;border-width:2px}
.centerLobby{grid-column:1/3;grid-row:2;justify-content:center;min-height:0}
.logoText{font-size:34px;line-height:.88;transform:none;margin:0}.snakePreview{width:min(430px,72vw);height:82px;margin:4px 0}
.matchModeSection{width:min(500px,78vw);min-width:0!important;margin:2px 0 5px!important;padding:7px!important;border-radius:17px!important;background:rgba(4,18,35,.72)!important;border:1px solid rgba(132,215,255,.22)!important}
.matchModeTitle{font-size:10px!important;margin-bottom:5px!important;color:#ccecff!important}.matchModeButtons{gap:9px!important}
.matchModeBtn{flex:1;min-width:0!important;min-height:48px;padding:8px 10px!important;border-radius:14px!important;font-size:13px!important;box-shadow:0 4px 0 rgba(0,0,0,.28)!important}
.matchModeBtn.active{transform:translateY(-1px);box-shadow:0 5px 0 rgba(0,0,0,.34),0 0 18px rgba(84,220,255,.18)!important}.matchModeHint{font-size:10px!important;margin-top:6px!important;min-height:12px!important;color:#d6eaff!important}
.difficultySelect{margin:3px 0 3px;padding:4px;border-radius:14px}.diffBtn{min-width:84px;min-height:38px;padding:6px 11px;font-size:11px;border-radius:10px}.diffHint{font-size:10px;min-height:12px;color:#d2e5f3}
.playBtn{min-width:250px;min-height:56px;font-size:25px;padding:10px 30px;border-radius:19px;letter-spacing:.02em}.playBtn.starting{opacity:.8;transform:scale(.98)}
.lobbyTip{margin-top:7px;font-size:11px;font-weight:900;color:#c9e4f6;text-align:center}
.simpleBottomNav{grid-column:1/3;grid-row:3;display:grid;grid-template-columns:repeat(4,minmax(90px,132px));justify-content:center;align-items:center;gap:9px}
.simpleBottomNav .navBtn{width:auto;height:58px;min-height:58px;border-radius:16px;font-size:11px;position:relative;padding:4px 7px}.simpleBottomNav .navBtn span{font-size:21px;margin:0 0 1px}.simpleBottomNav .badge{position:absolute;right:7px;top:5px;font-style:normal}
.topbar{min-height:60px}.closeBtn{min-width:44px}
.tabs{scroll-snap-type:x proximity;scrollbar-width:none}.tabs::-webkit-scrollbar{display:none}.tabBtn{scroll-snap-align:start;min-width:122px}
.content{-webkit-overflow-scrolling:touch}.optionCard,.itemCard,.upgradeCard{touch-action:manipulation}
.modal{padding:max(8px,env(safe-area-inset-top)) max(8px,env(safe-area-inset-right)) max(8px,env(safe-area-inset-bottom)) max(8px,env(safe-area-inset-left))}.modalBox{width:min(680px,94vw);max-height:90vh;border-radius:20px}
.primary,.secondary,.shopBtn,.closeBtn,.navBtn,.tabBtn,.diffBtn,.matchModeBtn,.gameActionBtn{cursor:pointer}

/* Cleaner in-match information. */
.simpleStats{left:calc(8px + env(safe-area-inset-left));top:calc(8px + env(safe-area-inset-top));display:flex!important;flex-wrap:wrap;gap:5px 9px;width:190px;min-width:0!important;padding:7px 9px!important;font-size:10px!important;line-height:1.1!important}
.simpleStats span{display:inline-flex;align-items:center;gap:3px;white-space:nowrap}.simpleStats .modeStat{width:100%;color:#8eeaff;font-size:9px;letter-spacing:.04em}
#leader{right:calc(8px + env(safe-area-inset-right));top:calc(8px + env(safe-area-inset-top));width:148px;padding:7px 8px;font-size:9px}
#gameTopActions{top:calc(8px + env(safe-area-inset-top))}.gameResetBtn{display:none!important}.gameMenuBtn{min-width:76px;height:38px;font-size:11px;padding:0 11px}
#zoneHud{top:52px!important;min-width:240px!important;max-width:52vw;padding:6px 10px!important;font-size:10px!important;border-radius:13px!important;white-space:nowrap}
#boostBtn{width:94px;height:94px;font-size:13px;font-weight:1000;border-width:3px;right:calc(18px + env(safe-area-inset-right));bottom:calc(18px + env(safe-area-inset-bottom))}
#emoteBtn{right:calc(122px + env(safe-area-inset-right));bottom:calc(30px + env(safe-area-inset-bottom));width:54px;height:54px;font-size:25px}
#energy{bottom:calc(13px + env(safe-area-inset-bottom));height:10px}
#radarWrap{left:calc(12px + env(safe-area-inset-left));bottom:142px;padding:5px}
#radarWrap:before{font-size:7px}.hudBox{backdrop-filter:blur(5px)}
#pauseOverlay .panel{width:min(390px,90vw)!important;padding:20px!important}#pauseOverlay h1{margin-top:0}
.postGrid{gap:8px}.postStat{padding:10px}.postStat strong{font-size:20px}

@media(max-width:1000px){#leader{display:none}.simpleStats{width:176px}.modeGrid{grid-template-columns:repeat(2,1fr)}.upgradeGrid{grid-template-columns:repeat(2,minmax(150px,1fr))}.itemGrid{grid-template-columns:repeat(2,minmax(150px,1fr))}}
@media(max-width:760px){.lobbyHUD{grid-template-columns:1fr 1fr!important;grid-template-rows:64px minmax(0,1fr) 64px!important;padding:7px 10px!important}.profileChip{width:min(190px,45vw)}.simpleBottomNav{grid-template-columns:repeat(4,minmax(78px,1fr));width:min(520px,94vw);gap:6px}.simpleBottomNav .navBtn{height:54px;min-height:54px;font-size:9px}.matchModeSection{width:min(470px,82vw)}.playBtn{min-width:220px}.settingsLayout,.profileGrid,.wardrobeLayout{grid-template-columns:1fr}.previewArena{height:260px}}
@media(max-height:500px){.lobbyHUD{grid-template-rows:58px minmax(0,1fr) 58px!important;padding:5px 10px!important}.profileChip{height:52px;padding:4px 7px}.avatar{width:40px;height:40px;font-size:22px}.lobbyWallet .wallet{padding:4px 8px}.logoText{font-size:25px}.snakePreview{height:42px;margin:0}.previewSeg{width:25px;height:25px;margin-left:-8px}.previewHead{width:34px;height:34px}.matchModeSection{padding:4px 6px!important;margin:1px 0 2px!important}.matchModeTitle{display:none!important}.matchModeBtn{min-height:38px;padding:4px 7px!important;font-size:10px!important}.matchModeHint{font-size:8px!important;margin-top:3px!important}.difficultySelect{margin:1px 0;padding:2px}.diffBtn{min-height:32px;min-width:70px;padding:3px 7px;font-size:9px}.diffHint{display:none}.playBtn{min-height:44px;min-width:210px;font-size:19px;padding:6px 22px}.lobbyTip{display:none}.simpleBottomNav .navBtn{height:48px;min-height:48px}.simpleBottomNav .navBtn span{font-size:17px}.simpleStats{top:6px;width:166px;padding:6px 7px!important;font-size:9px!important}#zoneHud{top:43px!important;min-width:205px!important;font-size:8px!important;padding:4px 7px!important}#gameTopActions{top:6px}.gameMenuBtn{height:34px;min-height:34px;font-size:9px}#boostBtn{width:80px;height:80px}#emoteBtn{right:108px;width:46px;height:46px;font-size:22px}#radarWrap{bottom:112px}#radar{width:70px;height:70px}.modalBox{max-height:94vh;padding:14px}.rewardDays{grid-template-columns:repeat(4,1fr)}.rewardDay{min-height:76px;padding:7px 4px}}
'''
rep('</style>', css + '\n</style>', 'v5.2 CSS')

# Expose the guarded starter for inline onclick and tests.
rep('window.setGameMode=setGameMode;', 'window.setGameMode=setGameMode;window.safeStartMatch=safeStartMatch;', 'export safe start')

required = [
    'class="bottomNav simpleBottomNav"',
    'id="playGameBtn"',
    'function safeStartMatch()',
    "play.textContent=mode==='zonal'?'PLAY ZONAL':'PLAY INFINITE'",
    'class="hudBox simpleStats"',
    '.gameResetBtn{display:none!important}',
    '@media(max-height:500px)',
    'window.safeStartMatch=safeStartMatch;',
    'id="dailyBadge"',
    'id="missionBadge"',
    'id="mode-infinite"',
    'id="mode-zonal"',
    'function updateZonalMode(dt)',
    'while(snakes.length>50)snakes.pop()',
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('v5.2 simple UI patch incomplete: ' + ', '.join(missing))
if 'class="sideMenu"' in html or 'class="quickRight"' in html:
    raise SystemExit('Duplicate lobby side menus still present')
if html.count('id="dailyBadge"') != 1 or html.count('id="missionBadge"') != 1:
    raise SystemExit('Reward/mission badge IDs are duplicated')

p.write_text(html, encoding='utf-8')
print('v5.2 child-friendly simple UI patch applied')
