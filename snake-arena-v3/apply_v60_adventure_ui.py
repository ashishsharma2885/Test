from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')
root=Path(__file__).resolve().parent
css=(root/'v60_adventure.css').read_text(encoding='utf-8')
js=(root/'v60_adventure.js').read_text(encoding='utf-8')

if '</style>' not in html: raise SystemExit('v6.0 target missing: style close')
html=html.replace('</style>',css+'\n</style>',1)

champ='placementCoins=1000;run.xp+=500'
if champ in html:
    html=html.replace(champ,champ+";data.gems=(data.gems||0)+25;data.trophies=(data.trophies||0)+50",1)

extra='''\n#bootSplash{background:radial-gradient(circle at 50% 35%,#78e769 0 22%,#37bfe8 53%,#126a3a 100%)!important}\n#bootSplash:before{background:#ffe83d!important;opacity:.20!important}#bootSplash:after{background:#37ff6b!important;opacity:.22!important}\n.bootSnake{color:#ffd52b!important;text-shadow:0 4px 0 #8d3c08,0 0 14px #ff9b18!important}.bootIO{color:#fff5b5!important;text-shadow:0 3px 0 #9a4b09!important}.bootBy{color:#fff!important;text-shadow:0 3px 0 #17652e!important}.bootHint{color:#e9ffd5!important}\n'''
html=html.replace('</style>',extra+'\n</style>',1)

marker='window.handleAndroidBack=function(){'
if marker not in html: raise SystemExit('v6.0 target missing: runtime insertion marker')
html=html.replace(marker,js+'\n'+marker,1)

required=["home.id='advHome'",'class="advBottom"','SHOP, REWARDS & QUESTS','function advOpenPanel(type)','function advChooseArena(key)','window.__v60UiTest=function()','#advPanel{position:fixed','#lobby>.lobbyHUD{display:none!important}','ZONAL SURVIVAL','ONLINE BATTLE','WI-FI / HOTSPOT','BLUETOOTH','Jungle Garden','Candy Land','Ocean Reef','Desert Ruins','Snow World','Space Neon',"const map={jungle:'grass',candy:'neon',ocean:'blue',desert:'desert',snow:'ice',space:'space'}","data.gems=(data.gems||0)+25",'setTimeout(finish,2000);','value*1.28','while(snakes.length>50)snakes.pop()']
missing=[x for x in required if x not in html]
if missing: raise SystemExit('v6.0 UI patch incomplete: '+', '.join(missing))
if 'f.x=wrap(f.x+delta(f.x,this.x)*pull)' in html: raise SystemExit('Fruit dragging returned in v6.0')

p.write_text(html,encoding='utf-8')
print('v6.0 original tropical Adventure UI applied')
