from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')

# 1) Stronger but still safe magnet progression.
old = "const magnetBonus=this.isPlayer?6+Math.max(0,magnetLevel-1)*5:0;"
new = "const magnetBonus=this.isPlayer?10+Math.max(0,magnetLevel-1)*7:0;"
if old not in html:
    raise SystemExit('v5.0 target missing: v4.9.1 magnet formula')
html = html.replace(old, new, 1)

# Update nearby explanatory comment if present.
html = html.replace(
    '// Magnet Lv.1 has a SMALL 6px magnetic bonus; every upgrade adds 5px more.',
    '// Magnet Lv.1 has a useful 10px magnetic bonus; every upgrade adds 7px more.',
    1
)

# 2) Add a lightweight 2-second boot splash. It appears only once because the HTML page
# itself is not reloaded on Play Again / Reset / Main Menu.
css_marker = '</style>'
splash_css = r'''
#bootSplash{position:fixed;inset:0;z-index:100000;display:flex;align-items:center;justify-content:center;overflow:hidden;background:radial-gradient(circle at 50% 45%,#173d84 0%,#081933 42%,#020711 100%);pointer-events:auto;opacity:1;transition:opacity .34s ease}
#bootSplash.hide{opacity:0;pointer-events:none}
#bootSplash:before,#bootSplash:after{content:"";position:absolute;width:55vmax;height:55vmax;border-radius:50%;filter:blur(65px);opacity:.28}
#bootSplash:before{left:-20vmax;top:-30vmax;background:#7b2cff}#bootSplash:after{right:-22vmax;bottom:-32vmax;background:#00cfff}
.bootLogo{text-align:center;position:relative;z-index:2;transform:scale(.92);animation:bootPop .5s ease forwards}.bootSnake{font-size:clamp(48px,10vw,120px);line-height:.9;font-weight:1000;letter-spacing:-3px;color:#ffd51f;text-shadow:0 3px 0 #b65f00,0 0 14px #ff8b00,0 0 32px rgba(255,190,0,.65)}.bootIO{color:#37ddff;text-shadow:0 3px 0 #1262a9,0 0 15px #00d9ff,0 0 34px rgba(0,174,255,.7)}.bootBy{margin-top:16px;font-size:clamp(21px,4vw,48px);font-weight:1000;font-style:italic;color:#f6fbff;text-shadow:0 0 12px #22cfff}.bootHint{margin-top:10px;color:#9fdaff;font-size:clamp(10px,1.8vw,16px);font-weight:800;letter-spacing:2px}@keyframes bootPop{to{transform:scale(1)}}
'''
if css_marker not in html:
    raise SystemExit('v5.0 target missing: style close')
html = html.replace(css_marker, splash_css + '\n' + css_marker, 1)

body_marker = '<body>'
splash_html = '''<body>\n<div id="bootSplash" aria-label="Snake IO by Ashish">\n  <div class="bootLogo">\n    <div class="bootSnake">SNAKE <span class="bootIO">IO</span></div>\n    <div class="bootBy">BY ASHISH</div>\n    <div class="bootHint">EAT • GROW • DOMINATE</div>\n  </div>\n</div>'''
if body_marker not in html:
    raise SystemExit('v5.0 target missing: body')
html = html.replace(body_marker, splash_html, 1)

# Use a pure DOM timer outside the match lifecycle; restarting a match cannot show it again.
script_close = '</script>'
boot_js = r'''
(function initBootSplash(){
 const splash=document.getElementById('bootSplash');
 if(!splash)return;
 let hidden=false;
 const finish=function(){
  if(hidden)return;hidden=true;
  splash.classList.add('hide');
  setTimeout(function(){if(splash&&splash.parentNode)splash.parentNode.removeChild(splash)},380);
 };
 setTimeout(finish,2000);
})();
'''
# Add to the final inline script so all UI exists before it runs.
pos = html.rfind(script_close)
if pos < 0:
    raise SystemExit('v5.0 target missing: script close')
html = html[:pos] + boot_js + '\n' + html[pos:]

# 3) Update visible game branding where safe.
html = html.replace('SNAKE ARENA IO', 'SNAKE IO', 10)
html = html.replace('Snake Arena IO', 'Snake IO by Ashish', 10)

# Replace v4.9 runtime helper with a stronger-magnet balance check.
start = html.find('window.__v48FoodPickupTest=function(){')
if start < 0:
    raise SystemExit('v5.0 target missing: magnet runtime helper')
end = html.find('};', start)
if end < 0:
    raise SystemExit('v5.0 helper end missing')
end += 2
helper = "window.__v48FoodPickupTest=function(){if(!player)return false;const oldLv=data.upgrades.magnet,r=5,base=player.radius+r+3;function mk(dist){return{x:wrap(player.x+dist),y:player.y,v:.7,r:r,loot:false,golden:false,alive:true,ttl:1e9,phase:0,emoji:'x'}}data.upgrades.magnet=1;let near=mk(base+9.5),far=mk(base+13);foods=[near,far];rebuildFoodGrid();player.eatNearby();const level1Ok=!near.alive&&far.alive;data.upgrades.magnet=2;let upgraded=mk(base+16.5);foods=[upgraded];rebuildFoodGrid();player.eatNearby();const level2Ok=!upgraded.alive;data.upgrades.magnet=oldLv;return level1Ok&&level2Ok};"
html = html[:start] + helper + html[end:]

required = [
    'const magnetBonus=this.isPlayer?10+Math.max(0,magnetLevel-1)*7:0;',
    'id="bootSplash"',
    'SNAKE <span class="bootIO">IO</span>',
    'BY ASHISH',
    'setTimeout(finish,2000);',
    'window.__v48FoodPickupTest=function()'
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('v5.0 stable patch incomplete: ' + ', '.join(missing))
if 'f.x=wrap(f.x+delta(f.x,this.x)*pull)' in html:
    raise SystemExit('Fruit drag code returned')

p.write_text(html, encoding='utf-8')
print('v5.0 stable branding + stronger magnet applied')
