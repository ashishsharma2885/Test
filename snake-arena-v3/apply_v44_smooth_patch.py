from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f'v4.4 target missing: {label}')
    html = html.replace(old, new, 1)


# 1) Keep body beads tightly packed. Spacing is now measured over a fixed-distance
# history stream rather than raw rendered frames, so boost/FPS cannot stretch gaps.
rep(
    "this.name=name;this.color=color;this.isPlayer=!!isPlayer;this.radius=10.5;this.spacing=6;",
    "this.name=name;this.color=color;this.isPlayer=!!isPlayer;this.radius=10.5;this.spacing=4;",
    'compact body spacing'
)

rep(
    "this.x=wrap(this.x+Math.cos(this.angle)*this.speed*dt);this.y=wrap(this.y+Math.sin(this.angle)*this.speed*dt);\n  this.history.push({x:this.x,y:this.y});",
    """const oldX=this.x,oldY=this.y,moveX=Math.cos(this.angle)*this.speed*dt,moveY=Math.sin(this.angle)*this.speed*dt;
  const moveDistance=Math.hypot(moveX,moveY),pathSteps=Math.max(1,Math.ceil(moveDistance/2.2));
  for(let ps=1;ps<=pathSteps;ps++){
   const t=ps/pathSteps;this.history.push({x:wrap(oldX+moveX*t),y:wrap(oldY+moveY*t)});
  }
  this.x=wrap(oldX+moveX);this.y=wrap(oldY+moveY);""",
    'fixed distance body trail'
)

# 2) Render a cheap connected underlay when performance mode skips visual beads.
# This avoids visible gaps on very long snakes without forcing thousands of circles.
rep(
    "const useTexture=s.isPlayer&&data.useCustomTexture&&customTextureReady&&customTextureSprite;\n const visualStep=Math.max(1,Math.ceil(s.segments.length/pc.maxSegments));",
    """const useTexture=s.isPlayer&&data.useCustomTexture&&customTextureReady&&customTextureSprite;
 const isBoosting=s.isPlayer?!!boost:(s.isRemote?!!s.networkBoosting:!!(s.ai&&s.ai.boosting));
 const visualStep=Math.max(1,Math.ceil(s.segments.length/pc.maxSegments));
 if(visualStep>1&&s.segments.length>2){
  ctx.save();ctx.globalAlpha=useTexture?.72:.92;ctx.strokeStyle=body;ctx.lineWidth=Math.max(5,s.radius*1.42*zoom);ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();
  let pathStarted=false,prevP=null;
  for(let bi=s.segments.length-1;bi>=0;bi-=visualStep){
   const bp=screenPos(s.segments[bi].x,s.segments[bi].y,zoom);
   if(bp.x<-70||bp.x>W+70||bp.y<-70||bp.y>H+70){prevP=null;continue}
   if(!pathStarted||!prevP||Math.abs(bp.x-prevP.x)>W*.45||Math.abs(bp.y-prevP.y)>H*.45){ctx.moveTo(bp.x,bp.y);pathStarted=true}else ctx.lineTo(bp.x,bp.y);
   prevP=bp;
  }
  ctx.stroke();ctx.restore();
 }""",
    'connected long snake rendering'
)

# 3) Glow every visible body bead during boost using translucent aura circles.
rep(
    "const r=Math.max(3.2,s.radius*(1-(i/Math.max(1,s.segments.length))*.25)*zoom);\n  if(useTexture){",
    """const bridge=visualStep>1?Math.min(s.radius*.55*zoom,(visualStep-1)*2.6*zoom):0;
  const r=Math.max(3.2,s.radius*(1-(i/Math.max(1,s.segments.length))*.25)*zoom+bridge);
  if(isBoosting){
   const pulse=1.34+Math.sin(performance.now()*.014+i*.22)*.06;
   ctx.save();ctx.globalAlpha=.24;ctx.fillStyle='#b7fbff';ctx.beginPath();ctx.arc(p.x,p.y,r*pulse,0,Math.PI*2);ctx.fill();ctx.restore();
  }
  if(useTexture){""",
    'boost body aura'
)

rep(
    "const h=screenPos(s.x,s.y,zoom),hr=Math.max(5,s.radius*zoom+1);\n ctx.save();",
    """const h=screenPos(s.x,s.y,zoom),hr=Math.max(5,s.radius*zoom+1);
 if(isBoosting){ctx.save();ctx.globalAlpha=.28;ctx.fillStyle='#d5ffff';ctx.beginPath();ctx.arc(h.x,h.y,hr*1.52,0,Math.PI*2);ctx.fill();ctx.restore()}
 ctx.save();""",
    'boost head aura'
)

# 4) Sync boost state for remote humans and host-authoritative AI so every phone sees glow.
rep(
    "function stateOfSnake(s,id){return{id:id,x:+s.x.toFixed(1),y:+s.y.toFixed(1),a:+s.angle.toFixed(4),l:+s.length.toFixed(2),e:+s.energy.toFixed(2),r:+s.radius.toFixed(2),alive:!!s.alive}}",
    """function stateOfSnake(s,id){
 const netBoost=s.isPlayer?!!boost:(s.isRemote?!!s.networkBoosting:!!(s.ai&&s.ai.boosting));
 return{id:id,x:+s.x.toFixed(1),y:+s.y.toFixed(1),a:+s.angle.toFixed(4),l:+s.length.toFixed(2),e:+s.energy.toFixed(2),r:+s.radius.toFixed(2),alive:!!s.alive,b:netBoost}
}""",
    'network boost state'
)

rep(
    "alive:packet.alive!==false};",
    "alive:packet.alive!==false,b:!!packet.b};",
    'guest boost target'
)
rep(
    "alive:t.alive!==false}}",
    "alive:t.alive!==false,b:!!t.b}}",
    'snapshot boost target'
)
rep(
    "s.length=t.l;s.energy=t.e;s.radius=t.r;s.alive=t.alive;",
    "s.length=t.l;s.energy=t.e;s.radius=t.r;s.alive=t.alive;s.networkBoosting=!!t.b;",
    'remote boost interpolation'
)
rep(
    "s.speed=BASE_SPEED;s.score=0;s.history=[];s.segments=[];",
    "s.speed=BASE_SPEED;s.score=0;s.networkBoosting=false;s.history=[];s.segments=[];",
    'reset remote boost state'
)

# 5) Fix single-player rank after death. The previous implementation filtered out the dead
# player, then indexOf(player) returned -1 and Math.max(...) incorrectly produced rank #1.
rep(
    "function currentRank(){const alive=snakes.filter(function(s){return s.alive}).sort(function(a,b){return(b.score+b.length*2)-(a.score+a.length*2)});return Math.max(1,alive.indexOf(player)+1)}",
    """function currentRank(){
 const ranked=snakes.slice().sort(function(a,b){return(b.score+b.length*2)-(a.score+a.length*2)});
 const pos=ranked.indexOf(player);return pos<0?ranked.length:pos+1;
}""",
    'single player rank bug'
)

# 6) Smoother default AUTO mode. Quality mode remains available for powerful phones.
rep(
    """function performanceConfig(){
 const mode=(data.performance&&data.performance.mode)||'auto';
 if(mode==='smooth')return{mode:'smooth',dpr:1.15,maxSegments:220,maxFood:280,radarEvery:3,shadows:false};
 if(mode==='quality')return{mode:'quality',dpr:1.75,maxSegments:500,maxFood:700,radarEvery:1,shadows:true};
 const low=(navigator.hardwareConcurrency&&navigator.hardwareConcurrency<=4)||Math.min(innerWidth,innerHeight)<390;
 return low
  ?{mode:'auto',dpr:1.25,maxSegments:260,maxFood:340,radarEvery:2,shadows:false}
  :{mode:'auto',dpr:1.5,maxSegments:340,maxFood:460,radarEvery:2,shadows:true};
}""",
    """let adaptiveRenderLoad=1,perfWindowStart=performance.now(),perfFrames=0;
function performanceConfig(){
 const mode=(data.performance&&data.performance.mode)||'auto';
 if(mode==='smooth')return{mode:'smooth',dpr:1.05,maxSegments:250,maxFood:250,radarEvery:4,shadows:false};
 if(mode==='quality')return{mode:'quality',dpr:1.65,maxSegments:520,maxFood:650,radarEvery:1,shadows:true};
 const low=(navigator.hardwareConcurrency&&navigator.hardwareConcurrency<=4)||Math.min(innerWidth,innerHeight)<390;
 const base=low
  ?{dpr:1.12,maxSegments:285,maxFood:300,radarEvery:3,shadows:false}
  :{dpr:1.35,maxSegments:380,maxFood:400,radarEvery:2,shadows:true};
 return{mode:'auto',dpr:base.dpr,maxSegments:Math.max(190,Math.floor(base.maxSegments*adaptiveRenderLoad)),maxFood:Math.max(210,Math.floor(base.maxFood*adaptiveRenderLoad)),radarEvery:adaptiveRenderLoad<.8?Math.max(4,base.radarEvery):base.radarEvery,shadows:base.shadows&&adaptiveRenderLoad>.72};
}
function trackAutoPerformance(now){
 perfFrames++;
 if(now-perfWindowStart<1500)return;
 const fps=perfFrames*1000/Math.max(1,now-perfWindowStart);perfFrames=0;perfWindowStart=now;
 if((data.performance&&data.performance.mode||'auto')!=='auto'){adaptiveRenderLoad=1;return}
 if(fps<43)adaptiveRenderLoad=Math.max(.62,adaptiveRenderLoad-.10);
 else if(fps>56)adaptiveRenderLoad=Math.min(1,adaptiveRenderLoad+.05);
}""",
    'adaptive auto performance'
)

rep(
    "const dt=Math.min(.033,Math.max(0,(now-last)/1000));last=now;renderFrameCount++;",
    "const dt=Math.min(.033,Math.max(0,(now-last)/1000));last=now;renderFrameCount++;trackAutoPerformance(now);",
    'fps tracker'
)

# 7) Slightly lighter multiplayer arena population of static food while retaining plentiful food.
rep(
    "foods=[];snakes=[];for(let i=0;i<760;i++)spawnFood();",
    "foods=[];snakes=[];for(let i=0;i<620;i++)spawnFood();",
    'room food performance'
)

# Bluetooth benefits from a slightly lower snapshot rate; interpolation keeps motion smooth.
rep(
    "const interval=multiplayer.transport==='bluetooth'?125:75;",
    "const interval=multiplayer.transport==='bluetooth'?150:72;",
    'network snapshot pacing'
)

required = [
    'this.spacing=4',
    'pathSteps=Math.max(1,Math.ceil(moveDistance/2.2))',
    "const isBoosting=s.isPlayer?!!boost",
    "ctx.fillStyle='#b7fbff'",
    'networkBoosting=!!t.b',
    'function trackAutoPerformance(now)',
    'const ranked=snakes.slice()',
    'for(let i=0;i<620;i++)spawnFood()',
    "t:'death_loot'",
    'ROOM_MAX_PLAYERS=4',
    'PLAYER_START_LENGTH=3',
]
missing=[x for x in required if x not in html]
if missing:
    raise SystemExit('v4.4 smooth patch incomplete: '+', '.join(missing))

p.write_text(html, encoding='utf-8')
print('v4.4 compact-body, boost-glow and performance patch applied')
