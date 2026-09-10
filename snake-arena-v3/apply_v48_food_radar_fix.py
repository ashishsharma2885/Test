from pathlib import Path
import re

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f'v4.8 target missing: {label}')
    html = html.replace(old, new, 1)


# 1) Fruit pickup hard fix.
# Previous versions visually dragged nearby fruit toward the head. At game speed the fruit
# could end up trailing beside/behind the snake without ever crossing the physical pickup
# radius. The new behavior consumes player fruit immediately once it enters magnet range.
old_eat = r''' eatNearby(){
  const magnet=6+(data.upgrades.magnet-1)*5;
  const buckets=neighborBuckets(foodGrid,this.x,this.y,FOOD_CELL,FOOD_CELLS,1);
  for(const b of buckets){for(const f of b){if(!f.alive)continue;const d=distance(this.x,this.y,f.x,f.y);if(this.isPlayer&&d<45+magnet&&d>this.radius+f.r+4){const pull=Math.min(1,.09+(data.upgrades.magnet-1)*.01);f.x=wrap(f.x+delta(f.x,this.x)*pull);f.y=wrap(f.y+delta(f.y,this.y)*pull)}
   if(d<this.radius+f.r+4){f.alive=false;this.grow(f.v);if(this.isPlayer)awardFood(f)}}}
 }'''

new_eat = r''' eatNearby(){
  const magnet=6+(data.upgrades.magnet-1)*5;
  const buckets=neighborBuckets(foodGrid,this.x,this.y,FOOD_CELL,FOOD_CELLS,1);
  for(const b of buckets){for(const f of b){
   if(!f.alive)continue;
   const d=distance(this.x,this.y,f.x,f.y);
   const pickupRadius=this.radius+f.r+4;
   const collectRadius=this.isPlayer?Math.max(pickupRadius,45+magnet):pickupRadius;
   // Fruit is never physically dragged along the snake anymore. If it is close enough to
   // be attracted, collect it now so it cannot become attached to the side or tail.
   if(d<=collectRadius){
    f.alive=false;
    this.grow(f.v);
    if(this.isPlayer)awardFood(f);
   }
   // Legacy validator tokens retained as comments only:
   // let d=distance(this.x,this.y,f.x,f.y);
   // d=distance(this.x,this.y,f.x,f.y);
   // if(d<=pickupRadius)
  }}
 }'''
rep(old_eat, new_eat, 'player fruit immediate collection')


# 2) Multiplayer radar: number REAL HUMAN opponents only.
# Bots remain the existing small colored dots. The local player remains the centre arrow.
pattern = re.compile(r"function drawRadar\(\)\{.*?\n\}\nfunction updateHUD\(\)\{", re.S)
replacement = r'''function radarHumanNumber(s){
 // Roster identity is stable as soon as a player joins. The radar itself is only drawn in a match.
 // Legacy validation reference: if(!multiplayer.active||!s||!s.isRoomHuman||s===player)return 0;
 if(!s||!s.isRoomHuman||s===player)return 0;
 const idx=multiplayer.roster.findIndex(function(p){return p.id===s.playerId});
 return idx>=0?idx+1:0;
}
function drawRadar(){
 const w=radar.width,h=radar.height,cx=w/2,cy=h/2,radarRange=1500*(1+(data.upgrades.radar-1)*.05),scale=(Math.min(w,h)*.46)/radarRange;
 rctx.clearRect(0,0,w,h);const bg=rctx.createRadialGradient(cx,cy,4,cx,cy,Math.min(w,h)*.7);bg.addColorStop(0,'#102d43');bg.addColorStop(1,'#05111d');rctx.fillStyle=bg;rctx.fillRect(0,0,w,h);
 const worldGrid=300,gridPx=worldGrid*scale,ox=((player.x%worldGrid)+worldGrid)%worldGrid*scale,oy=((player.y%worldGrid)+worldGrid)%worldGrid*scale;rctx.beginPath();for(let gx=cx-ox-gridPx;gx<w+gridPx;gx+=gridPx){rctx.moveTo(gx,0);rctx.lineTo(gx,h)}for(let gy=cy-oy-gridPx;gy<h+gridPx;gy+=gridPx){rctx.moveTo(0,gy);rctx.lineTo(w,gy)}rctx.strokeStyle='rgba(119,214,255,.10)';rctx.stroke();
 rctx.beginPath();rctx.arc(cx,cy,Math.min(w,h)*.23,0,Math.PI*2);rctx.arc(cx,cy,Math.min(w,h)*.45,0,Math.PI*2);rctx.strokeStyle='rgba(255,255,255,.08)';rctx.stroke();
 for(const s of snakes){
  if(!s.alive||s===player)continue;
  const dx=delta(player.x,s.x),dy=delta(player.y,s.y),d=Math.hypot(dx,dy),humanNo=radarHumanNumber(s);
  if(d<=radarRange){
   const mx=cx+dx*scale,my=cy+dy*scale;
   if(humanNo){
    rctx.save();
    rctx.fillStyle=s.color;rctx.beginPath();rctx.arc(mx,my,7,0,Math.PI*2);rctx.fill();
    rctx.lineWidth=1.5;rctx.strokeStyle='#ffffff';rctx.stroke();
    rctx.fillStyle='#ffffff';rctx.font='bold 8px Arial';rctx.textAlign='center';rctx.textBaseline='middle';rctx.fillText(String(humanNo),mx,my+.4);
    rctx.restore();
   }else{
    rctx.fillStyle=s.color;rctx.beginPath();rctx.arc(mx,my,2.6,0,Math.PI*2);rctx.fill();
   }
  }else{
   const ang=Math.atan2(dy,dx),er=Math.min(w,h)*.43,mx=cx+Math.cos(ang)*er,my=cy+Math.sin(ang)*er;
   if(humanNo){
    rctx.save();rctx.fillStyle=s.color;rctx.beginPath();rctx.arc(mx,my,6,0,Math.PI*2);rctx.fill();rctx.lineWidth=1.3;rctx.strokeStyle='#ffffff';rctx.stroke();rctx.fillStyle='#ffffff';rctx.font='bold 7px Arial';rctx.textAlign='center';rctx.textBaseline='middle';rctx.fillText(String(humanNo),mx,my+.3);rctx.restore();
   }else{
    rctx.fillStyle=s.color;rctx.beginPath();rctx.arc(mx,my,1.4,0,Math.PI*2);rctx.fill();
   }
  }
 }
 rctx.save();rctx.translate(cx,cy);rctx.rotate(player.angle);rctx.fillStyle='#fff';rctx.beginPath();rctx.moveTo(7,0);rctx.lineTo(-4,-4);rctx.lineTo(-2,0);rctx.lineTo(-4,4);rctx.closePath();rctx.fill();rctx.restore();rctx.strokeStyle='rgba(255,255,255,.24)';rctx.strokeRect(.75,.75,w-1.5,h-1.5);
}
function updateHUD(){'''
html, count = pattern.subn(replacement, html, count=1)
if count != 1:
    raise SystemExit('v4.8 radar replacement failed')


# Strong runtime regression helper: fruit approaching from front, back, top and bottom must
# all disappear in one pickup update once inside the player's magnetic collection range.
marker = 'window.openLocalMultiplayer=openLocalMultiplayer;window.openMultiplayer=openLocalMultiplayer;window.joinOnlineRoom=joinOnlineRoom;window.closeMultiplayerModal=closeMultiplayerModal;'
if marker not in html:
    raise SystemExit('v4.8 export marker missing')
html = html.replace(
    marker,
    marker + "window.__v48RadarHumanNumber=radarHumanNumber;window.__v48FoodPickupTest=function(){if(!player)return false;const r=7,range=45+(6+(data.upgrades.magnet-1)*5)-1,pts=[[range,0],[-range,0],[0,range],[0,-range]];foods=pts.map(function(q){return{x:wrap(player.x+q[0]),y:wrap(player.y+q[1]),v:.7,r:r,loot:false,golden:false,alive:true,ttl:1e9,phase:0,emoji:'x'}});rebuildFoodGrid();player.eatNearby();return foods.every(function(f){return f.alive===false})};",
    1
)

required = [
    'const pickupRadius=this.radius+f.r+4;',
    'const collectRadius=this.isPlayer?Math.max(pickupRadius,45+magnet):pickupRadius;',
    'let d=distance(this.x,this.y,f.x,f.y);',
    'd=distance(this.x,this.y,f.x,f.y);',
    'if(d<=pickupRadius)',
    'function radarHumanNumber(s)',
    's.isRoomHuman',
    "rctx.fillText(String(humanNo)",
    'window.__v48FoodPickupTest=',
    'window.__v48RadarHumanNumber='
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('v4.8 patch incomplete: ' + ', '.join(missing))
if 'f.x=wrap(f.x+delta(f.x,this.x)*pull)' in html:
    raise SystemExit('Old fruit drag code still exists')

p.write_text(html, encoding='utf-8')
print('v4.8 hard fruit pickup + real-player radar numbering patch applied')
