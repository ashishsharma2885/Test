from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')
root=Path(__file__).resolve().parent
css=(root/'v61_ui_cleanup.css').read_text(encoding='utf-8')
js=(root/'v61_ui_cleanup.js').read_text(encoding='utf-8')

if '</style>' not in html: raise SystemExit('v6.1 target missing: style close')
html=html.replace('</style>',css+'\n</style>',1)
marker='window.handleAndroidBack=function(){'
if marker not in html: raise SystemExit('v6.1 target missing: runtime marker')
html=html.replace(marker,js+'\n'+marker,1)

required=[
 'function advV61RebuildHome()',
 'function advV61Start(mode,kids)',
 'window.__v61UiAudit=function()',
 'Daily reward stays on Home. Quests stay in Quests. Multiplayer stays in Friends.',
 'Multiplayer is only in Friends. Arena selection is only in Arena.',
 '.advMainActions .advAction{display:none!important}',
 '.advSettingsTop{position:absolute',
 'PLAY CLASSIC','PLAY ZONAL','PLAY EASY',
 'ONLINE ROOM','WI-FI / HOTSPOT','BLUETOOTH',
 'SNAKE SKINS','UPGRADES','THEMES & ITEMS',
 'while(snakes.length>50)snakes.pop()',
 'value*1.28',
 'const magnetBonus=this.isPlayer?10+Math.max(0,magnetLevel-1)*7:0;'
]
missing=[x for x in required if x not in html]
if missing: raise SystemExit('v6.1 cleanup incomplete: '+', '.join(missing))
if 'f.x=wrap(f.x+delta(f.x,this.x)*pull)' in html: raise SystemExit('Fruit drag code returned')

p.write_text(html,encoding='utf-8')
print('v6.1 UI cleanup applied: duplicate destinations removed')
