from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global html
    if old not in html:
        raise SystemExit(f'v4.6 target missing: {label}')
    html=html.replace(old,new,1)

# Critical v4.5 regression: resize() calls applyControlLayout() during script startup.
# The floating branch referenced the lexical `joystick` binding before it had been
# initialized, causing Android WebView to stop the entire game script.
rep(
""" if(floating){
  joy.style.transformOrigin='center center';
  joy.style.right='auto';joy.style.bottom='auto';
  if(!joystick.active)joy.style.display='none';
  return;
 }""",
""" if(floating){
  joy.style.transformOrigin='center center';
  joy.style.right='auto';joy.style.bottom='auto';
  // Never read runtime joystick state here: this function also runs during startup.
  // beginFloatingJoystick() explicitly shows the control when a valid touch begins.
  joy.style.display='none';
  return;
 }""",
'joystick TDZ startup crash'
)

# Harden floating position math for unusual Android WebView sizes/orientation transitions.
rep(
""" const base=joy.offsetWidth||116,scale=clamp(Number(data.controls.size)||1,.65,1.55),r=base*scale*.5;
 const cx=clamp(x,r+8,W-r-8),cy=clamp(y,r+8,H-r-8);""",
""" const base=Math.max(72,joy.offsetWidth||116),scale=clamp(Number(data.controls.size)||1,.65,1.55),r=base*scale*.5;
 const safeW=Math.max(base+20,Number(W)||innerWidth||800),safeH=Math.max(base+20,Number(H)||innerHeight||400);
 const cx=clamp(Number(x)||safeW*.25,r+8,safeW-r-8),cy=clamp(Number(y)||safeH*.7,r+8,safeH-r-8);""",
'floating joystick safe geometry'
)

# Ensure invalid legacy control values can never break a startup/layout pass.
rep(
"""function applyControlLayout(){
 const joy=$('joystick'),boostEl=$('boostBtn'),emote=$('emoteBtn'),scale=clamp(Number(data.controls.size)||1,.65,1.55);""",
"""function applyControlLayout(){
 const joy=$('joystick'),boostEl=$('boostBtn'),emote=$('emoteBtn');
 if(!data.controls||typeof data.controls!=='object')data.controls={mode:'joystick',joystickStyle:'floating',handed:'left',size:1,sensitivity:1,joyX:0,joyY:0};
 if(data.controls.joystickStyle!=='fixed'&&data.controls.joystickStyle!=='floating')data.controls.joystickStyle='floating';
 if(data.controls.handed!=='left'&&data.controls.handed!=='right')data.controls.handed='left';
 const scale=clamp(Number(data.controls.size)||1,.65,1.55);""",
'legacy controls safety'
)

# Avoid a stale floating control surviving orientation/resize changes.
rep(
"""function positionFloatingJoystick(x,y){
 const joy=$('joystick');if(!joy)return;""",
"""function positionFloatingJoystick(x,y){
 const joy=$('joystick');if(!joy||data.controls.mode!=='joystick'||data.controls.joystickStyle!=='floating')return;""",
'floating joystick mode guard'
)

required=[
    "joy.style.display='none';\n  return;",
    'Never read runtime joystick state here',
    'const safeW=Math.max(base+20',
    "data.controls.joystickStyle!=='fixed'&&data.controls.joystickStyle!=='floating'",
    "function beginFloatingJoystick(e)",
    "function enforceLoopPosition(s)",
    "t:'death_loot'",
    'ROOM_BOTS=24',
    'PLAYER_START_LENGTH=3',
]
missing=[x for x in required if x not in html]
if missing:
    raise SystemExit('v4.6 runtime fix incomplete: '+', '.join(missing))

p.write_text(html,encoding='utf-8')
print('v4.6 Android startup/runtime fix applied')
