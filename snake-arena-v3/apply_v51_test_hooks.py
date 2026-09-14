from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')
marker='window.handleAndroidBack=function(){'
if marker not in html:
    raise SystemExit('v5.1 test hook target missing')
hook="window.__v51State=function(){return{mode:selectedGameMode(),zoneActive:zoneState.active,totalSnakes:snakes.length,aliveSnakes:snakes.filter(function(s){return s.alive}).length,zoneRadius:zoneState.radius,foodCount:foods.length};};\n"
if 'window.__v51State=' not in html:
    html=html.replace(marker,hook+marker,1)
p.write_text(html,encoding='utf-8')
print('v5.1 runtime state hook applied')
