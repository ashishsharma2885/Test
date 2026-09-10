from pathlib import Path
import re

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f'v4.5 target missing: {label}')
    html = html.replace(old, new, 1)


# 1) Add a persistent joystick style. Existing installs inherit FLOATING by default,
# while FIXED remains selectable and keeps the saved X/Y adjustment sliders.
rep(
    "controls:{mode:'joystick',handed:'left',size:1,sensitivity:1,joyX:0,joyY:0},",
    "controls:{mode:'joystick',joystickStyle:'floating',handed:'left',size:1,sensitivity:1,joyX:0,joyY:0},",
    'joystick style default'
)

# 2) Rebuild Controls settings so joystick size/side/style are obvious and actually adjustable.
pattern = re.compile(r"function renderControlSettings\(\)\{.*?\n\}\nfunction setControlMode", re.S)
replacement = r'''function renderControlSettings(){
 const c=data.controls;
 const fixed=c.joystickStyle!=='floating';
 $('settingsContent').innerHTML='<div class="settingsLayout"><div class="panel" style="padding:14px"><h2 class="yellow">Controls</h2>'+ 
 ['joystick','follow','tap'].map(function(m){return '<div class="optionCard card '+(c.mode===m?'selected':'')+'" onclick="setControlMode(\''+m+'\')"><b>'+({joystick:'Virtual Joystick',follow:'Follow Finger',tap:'Tap Direction'})[m]+'</b><div class="muted">'+({joystick:'Analog thumb control',follow:'Hold and guide',tap:'Tap where to turn'})[m]+'</div></div>'}).join('')+
 '<h3>Joystick Type</h3><div class="optionList"><div class="optionCard card '+(fixed?'selected':'')+'" onclick="setJoystickStyle(\'fixed\')"><b>Fixed Joystick</b><div class="muted">Use saved screen position</div></div><div class="optionCard card '+(!fixed?'selected':'')+'" onclick="setJoystickStyle(\'floating\')"><b>Floating Joystick</b><div class="muted">Appears where your finger touches</div></div></div>'+ 
 '<h3>Control Side</h3><div class="optionList"><div class="optionCard card '+(c.handed==='left'?'selected':'')+'" onclick="setHanded(\'left\')"><b>LEFT SIDE</b><div class="muted">Touch left half for joystick · boost on right</div></div><div class="optionCard card '+(c.handed==='right'?'selected':'')+'" onclick="setHanded(\'right\')"><b>RIGHT SIDE</b><div class="muted">Touch right half for joystick · boost on left</div></div></div>'+ 
 '<div class="sliderRow"><b>Joystick size</b><input type="range" min="0.65" max="1.55" step="0.05" value="'+c.size+'" oninput="setControlValue(\'size\',this.value);this.nextElementSibling.textContent=Math.round(this.value*100)+\'%\'"><span>'+Math.round(c.size*100)+'%</span></div>'+ 
 '<div class="sliderRow"><b>Sensitivity</b><input type="range" min="0.6" max="1.6" step="0.05" value="'+c.sensitivity+'" oninput="setControlValue(\'sensitivity\',this.value);this.nextElementSibling.textContent=Number(this.value).toFixed(2)+\'×\'"><span>'+Number(c.sensitivity).toFixed(2)+'×</span></div>'+ 
 (fixed?'<h3>Fixed Joystick Position</h3><div class="sliderRow"><b>Move inward</b><input type="range" min="0" max="220" step="5" value="'+c.joyX+'" oninput="setControlValue(\'joyX\',this.value);this.nextElementSibling.textContent=this.value+\' px\'"><span>'+c.joyX+' px</span></div><div class="sliderRow"><b>Move upward</b><input type="range" min="0" max="210" step="5" value="'+c.joyY+'" oninput="setControlValue(\'joyY\',this.value);this.nextElementSibling.textContent=this.value+\' px\'"><span>'+c.joyY+' px</span></div><button class="secondary" onclick="resetJoystickPosition()">RESET JOYSTICK POSITION</button>':'<div class="pill" style="margin-top:12px">👆 During gameplay, touch anywhere on the selected side. The joystick appears under your finger and disappears when you release.</div>')+'</div>'+ 
 '<div class="previewArena" id="controlPreview"><div class="miniSnake" id="controlMini"></div><div class="foodDot" style="left:66%;top:25%">🍎</div><div class="foodDot" style="left:35%;top:60%">🍇</div><div class="controlDemo"><div class="demoJoy">'+(fixed?'MOVE':'TOUCH')+'</div><div class="demoBoost">BOOST</div></div><div class="pill" style="position:absolute;left:50%;bottom:20px;transform:translateX(-50%);white-space:nowrap">'+(fixed?'Fixed position preview':'Floating joystick follows your first touch')+'</div></div></div>';
 makePreviewSnake($('controlMini'),currentSkin());applyControlPreview();
}
function setControlMode'''
html, count = pattern.subn(replacement, html, count=1)
if count != 1:
    raise SystemExit('v4.5 controls settings replacement failed')

# 3) Add joystick style setter and harden size/position values.
rep(
    "function setControlMode(m){data.controls.mode=m;saveData();renderControlSettings()}\nfunction setHanded(h){data.controls.handed=h;saveData();renderControlSettings()}\nfunction setControlValue(k,v){\n data.controls[k]=Number(v);saveData();applyControlPreview();applyControlLayout();\n}",
    """function setControlMode(m){data.controls.mode=m;saveData();applyControlLayout();renderControlSettings()}
function setJoystickStyle(style){
 if(style!=='fixed'&&style!=='floating')return;
 releaseJoystick();data.controls.joystickStyle=style;saveData();applyControlLayout();renderControlSettings();
}
function setHanded(h){
 if(h!=='left'&&h!=='right')return;
 releaseJoystick();data.controls.handed=h;saveData();applyControlLayout();renderControlSettings();
}
function setControlValue(k,v){
 let n=Number(v);if(!Number.isFinite(n))return;
 if(k==='size')n=clamp(n,.65,1.55);
 else if(k==='sensitivity')n=clamp(n,.6,1.6);
 else if(k==='joyX')n=clamp(n,0,220);
 else if(k==='joyY')n=clamp(n,0,210);
 data.controls[k]=n;saveData();applyControlPreview();applyControlLayout();
}""",
    'control setters'
)

# 4) Preview respects Fixed/Floating and the selected side.
pattern = re.compile(r"function applyControlPreview\(\)\{.*?\n\}\nfunction autoFitScale", re.S)
replacement = r'''function applyControlPreview(){
 const p=$('controlPreview');if(!p)return;const joy=p.querySelector('.demoJoy'),boostEl=p.querySelector('.demoBoost');
 const floating=data.controls.joystickStyle==='floating';
 const px=floating?28:Math.round((data.controls.joyX||0)*.28),py=floating?28:Math.round((data.controls.joyY||0)*.28);
 if(data.controls.handed==='right'){joy.style.left='auto';joy.style.right=(22+px)+'px';boostEl.style.right='auto';boostEl.style.left='22px'}else{joy.style.left=(22+px)+'px';joy.style.right='auto';boostEl.style.right='22px';boostEl.style.left='auto'}
 joy.style.bottom=(22+py)+'px';joy.style.transform='scale('+data.controls.size+')';joy.style.opacity=floating?'.72':'1';
}
function autoFitScale'''
html, count = pattern.subn(replacement, html, count=1)
if count != 1:
    raise SystemExit('v4.5 control preview replacement failed')

# 5) Replace gameplay layout. Fixed = saved position. Floating = hidden until touch.
pattern = re.compile(r"function applyControlLayout\(\)\{.*?\n\}\nfunction steerFromPointer", re.S)
replacement = r'''function applyControlLayout(){
 const joy=$('joystick'),boostEl=$('boostBtn'),emote=$('emoteBtn'),scale=clamp(Number(data.controls.size)||1,.65,1.55);
 if(!joy||!boostEl||!emote)return;
 const floating=data.controls.joystickStyle==='floating';
 joy.style.transform='scale('+scale+')';
 if(data.controls.handed==='right'){
  boostEl.style.right='auto';boostEl.style.left='20px';emote.style.right='auto';emote.style.left='118px';
 }else{
  boostEl.style.right='20px';boostEl.style.left='auto';emote.style.right='118px';emote.style.left='auto';
 }
 if(data.controls.mode!=='joystick'){joy.style.display='none';return}
 if(floating){
  joy.style.transformOrigin='center center';
  joy.style.right='auto';joy.style.bottom='auto';
  if(!joystick.active)joy.style.display='none';
  return;
 }
 const inward=clamp(Number(data.controls.joyX)||0,0,Math.max(0,W*.38));
 const upward=clamp(Number(data.controls.joyY)||0,0,Math.max(0,H*.48));
 joy.style.top='auto';joy.style.bottom=(18+upward)+'px';joy.style.display='block';
 joy.style.transformOrigin=data.controls.handed==='right'?'bottom right':'bottom left';
 if(data.controls.handed==='right'){joy.style.left='auto';joy.style.right=(18+inward)+'px'}
 else{joy.style.left=(18+inward)+'px';joy.style.right='auto'}
}
function steerFromPointer'''
html, count = pattern.subn(replacement, html, count=1)
if count != 1:
    raise SystemExit('v4.5 applyControlLayout replacement failed')

# 6) Floating joystick: touch anywhere on the chosen half of the gameplay canvas.
rep(
    "function steerFromPointer(e){pointer.x=e.clientX;pointer.y=e.clientY;pointer.lastMove=performance.now()}\ncanvas.addEventListener('pointerdown',function(e){pointer.down=true;steerFromPointer(e);if(data.controls.mode==='follow'||data.controls.mode==='tap')e.preventDefault()});\ncanvas.addEventListener('pointermove',function(e){if(data.controls.mode==='follow'&&pointer.down)steerFromPointer(e)});\ncanvas.addEventListener('pointerup',function(){pointer.down=false});\ncanvas.addEventListener('pointercancel',function(){pointer.down=false});\n\nconst joy=$('joystick'),stick=$('stick');",
    """function steerFromPointer(e){pointer.x=e.clientX;pointer.y=e.clientY;pointer.lastMove=performance.now()}
function isFloatingJoystickMode(){return data.controls.mode==='joystick'&&data.controls.joystickStyle==='floating'}
function floatingTouchAllowed(e){
 const x=e.clientX;return data.controls.handed==='right'?x>=W*.45:x<=W*.55;
}
function positionFloatingJoystick(x,y){
 const joy=$('joystick');if(!joy)return;
 joy.style.display='block';joy.style.visibility='hidden';joy.style.right='auto';joy.style.bottom='auto';joy.style.transformOrigin='center center';joy.style.transform='scale('+clamp(Number(data.controls.size)||1,.65,1.55)+')';
 const base=joy.offsetWidth||116,scale=clamp(Number(data.controls.size)||1,.65,1.55),r=base*scale*.5;
 const cx=clamp(x,r+8,W-r-8),cy=clamp(y,r+8,H-r-8);
 joy.style.left=(cx-base/2)+'px';joy.style.top=(cy-base/2)+'px';joy.style.visibility='visible';
}
function beginFloatingJoystick(e){
 if(!isFloatingJoystickMode()||!floatingTouchAllowed(e)||joystick.active)return false;
 positionFloatingJoystick(e.clientX,e.clientY);joystick.active=true;joystick.pointerId=e.pointerId;
 canvas.setPointerCapture&&canvas.setPointerCapture(e.pointerId);updateJoystick(e);return true;
}
canvas.addEventListener('pointerdown',function(e){
 if(beginFloatingJoystick(e)){e.preventDefault();return}
 pointer.down=true;steerFromPointer(e);if(data.controls.mode==='follow'||data.controls.mode==='tap')e.preventDefault()
});
canvas.addEventListener('pointermove',function(e){
 if(isFloatingJoystickMode()&&joystick.active&&e.pointerId===joystick.pointerId){updateJoystick(e);e.preventDefault();return}
 if(data.controls.mode==='follow'&&pointer.down)steerFromPointer(e)
});
canvas.addEventListener('pointerup',function(e){pointer.down=false;if(isFloatingJoystickMode())releaseJoystick(e)});
canvas.addEventListener('pointercancel',function(e){pointer.down=false;if(isFloatingJoystickMode())releaseJoystick(e)});

const joy=$('joystick'),stick=$('stick');""",
    'floating joystick canvas input'
)

# 7) Release floating joystick cleanly and hide it without losing last steering direction.
rep(
    "function releaseJoystick(e){\n if(!joystick.active)return;if(e&&joystick.pointerId!==null&&e.pointerId!==joystick.pointerId)return;\n if(Math.hypot(joystick.x,joystick.y)>.12)joystick.lastAngle=Math.atan2(joystick.y,joystick.x);\n joystick.active=false;joystick.pointerId=null;joystick.x=0;joystick.y=0;stick.style.transform='translate(-50%,-50%)';\n}",
    """function releaseJoystick(e){
 if(!joystick.active)return;if(e&&joystick.pointerId!==null&&e.pointerId!==joystick.pointerId)return;
 if(Math.hypot(joystick.x,joystick.y)>.12)joystick.lastAngle=Math.atan2(joystick.y,joystick.x);
 joystick.active=false;joystick.pointerId=null;joystick.x=0;joystick.y=0;if(stick)stick.style.transform='translate(-50%,-50%)';
 if(data.controls.mode==='joystick'&&data.controls.joystickStyle==='floating'&&joy)joy.style.display='none';
}""",
    'floating joystick release'
)

# Fixed joystick's own pointerdown should only be active in Fixed mode.
rep(
    "joy.addEventListener('pointerdown',function(e){joystick.active=true;joystick.pointerId=e.pointerId;joy.setPointerCapture&&joy.setPointerCapture(e.pointerId);updateJoystick(e);e.preventDefault();e.stopPropagation()});",
    "joy.addEventListener('pointerdown',function(e){if(data.controls.mode!=='joystick'||data.controls.joystickStyle==='floating')return;joystick.active=true;joystick.pointerId=e.pointerId;joy.setPointerCapture&&joy.setPointerCapture(e.pointerId);updateJoystick(e);e.preventDefault();e.stopPropagation()});",
    'fixed joystick input guard'
)

# 8) Reset transient input also hides a floating joystick, preventing stale touch UI after death/restart.
rep(
    "const stickEl=$('stick');if(stickEl)stickEl.style.transform='translate(-50%,-50%)';",
    "const stickEl=$('stick');if(stickEl)stickEl.style.transform='translate(-50%,-50%)';const joyEl=$('joystick');if(joyEl&&data.controls.joystickStyle==='floating')joyEl.style.display='none';",
    'reset floating joystick'
)

# 9) Export joystick style setter.
rep(
    "window.setControlMode=setControlMode;window.setHanded=setHanded;window.setControlValue=setControlValue;",
    "window.setControlMode=setControlMode;window.setJoystickStyle=setJoystickStyle;window.setHanded=setHanded;window.setControlValue=setControlValue;",
    'joystick style export'
)

# 10) Explicit toroidal helper used as a safety guard for every snake after movement/remote update.
# Movement already wraps; this additionally guarantees no NaN/out-of-range coordinate can linger.
rep(
    "function distance(ax,ay,bx,by){return Math.hypot(delta(ax,bx),delta(ay,by))}",
    """function distance(ax,ay,bx,by){return Math.hypot(delta(ax,bx),delta(ay,by))}
function enforceLoopPosition(s){
 if(!s)return;if(!Number.isFinite(s.x))s.x=WORLD/2;if(!Number.isFinite(s.y))s.y=WORLD/2;s.x=wrap(s.x);s.y=wrap(s.y);
}""",
    'loop safety helper'
)

# v4.4 movement ends with wrapped x/y already. Add explicit safety after assignment.
rep(
    "this.x=wrap(oldX+moveX);this.y=wrap(oldY+moveY);",
    "this.x=wrap(oldX+moveX);this.y=wrap(oldY+moveY);enforceLoopPosition(this);",
    'loop safety movement'
)

# Remote interpolation also wraps, but enforce the same invariant for network players/bots.
rep(
    "s.x=wrap(s.x+delta(s.x,t.x)*k);s.y=wrap(s.y+delta(s.y,t.y)*k);",
    "s.x=wrap(s.x+delta(s.x,t.x)*k);s.y=wrap(s.y+delta(s.y,t.y)*k);enforceLoopPosition(s);",
    'loop safety remote movement'
)

# 11) Validate all requested game rules are present in the generated game.
required = [
    "joystickStyle:'floating'",
    "function setJoystickStyle(style)",
    "function beginFloatingJoystick(e)",
    "function floatingTouchAllowed(e)",
    "min=\"0.65\" max=\"1.55\"",
    "data.controls.handed==='right'?x>=W*.45:x<=W*.55",
    "const wrap=function(v){return ((v%WORLD)+WORLD)%WORLD}",
    "function delta(a,b){let d=b-a;if(d>WORLD/2)d-=WORLD;if(d<-WORLD/2)d+=WORLD;return d}",
    "this.x=wrap(oldX+moveX);this.y=wrap(oldY+moveY);enforceLoopPosition(this)",
    "function enforceLoopPosition(s)",
    "for(const attacker of snakes)",
    "this.eatNearby()",
    "spawnFood(p.x+rand(-9,9),p.y+rand(-9,9),1.55,true)",
    "function spawnRoomDeathLoot(victim)",
    "t:'death_loot'",
    "ROOM_BOTS=24",
    "PLAYER_START_LENGTH=3",
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('v4.5 controls/world validation failed: ' + ', '.join(missing))

p.write_text(html, encoding='utf-8')
print('v4.5 floating joystick, loop arena, AI/loot validation patch applied')
