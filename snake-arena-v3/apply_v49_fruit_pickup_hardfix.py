from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')

old = r''' eatNearby(){
  const magnet=6+(data.upgrades.magnet-1)*5;
  const buckets=neighborBuckets(foodGrid,this.x,this.y,FOOD_CELL,FOOD_CELLS,1);
  for(const b of buckets){for(const f of b){
   if(!f.alive)continue;
   const pickupRadius=this.radius+f.r+4;
   let d=distance(this.x,this.y,f.x,f.y);
   if(this.isPlayer&&d<45+magnet&&d>pickupRadius){
    const pull=Math.min(1,.09+(data.upgrades.magnet-1)*.01);
    f.x=wrap(f.x+delta(f.x,this.x)*pull);
    f.y=wrap(f.y+delta(f.y,this.y)*pull);
    // IMPORTANT: the fruit moved, so use its NEW position for pickup testing.
    d=distance(this.x,this.y,f.x,f.y);
   }
   if(d<=pickupRadius){
    f.alive=false;
    this.grow(f.v);
    if(this.isPlayer)awardFood(f);
   }
  }}
 }'''

new = r''' eatNearby(){
  const magnet=6+(data.upgrades.magnet-1)*5;
  const buckets=neighborBuckets(foodGrid,this.x,this.y,FOOD_CELL,FOOD_CELLS,1);
  for(const b of buckets){for(const f of b){
   if(!f.alive)continue;
   const d=distance(this.x,this.y,f.x,f.y);
   const pickupRadius=this.radius+f.r+4;
   // HARD FIX: never drag fruit beside/behind the player snake. Once a fruit enters
   // the magnetic collection zone it is consumed immediately in this same update.
   // Bots still use physical head contact only.
   const collectRadius=this.isPlayer?Math.max(pickupRadius,45+magnet):pickupRadius;
   if(d<=collectRadius){
    f.alive=false;
    this.grow(f.v);
    if(this.isPlayer)awardFood(f);
   }
  }}
 }'''

if old not in html:
    raise SystemExit('v4.9 target missing: v4.8 eatNearby block')
html = html.replace(old, new, 1)

# Replace the old v4.8 regression helper with a stronger front/back/side pickup test.
old_helper = "window.__v48RadarHumanNumber=radarHumanNumber;window.__v48FoodPickupTest=function(){if(!player)return false;const r=7,d=player.radius+r+4+.65,f={x:wrap(player.x+d),y:player.y,v:.7,r:r,loot:false,golden:false,alive:true,ttl:1e9,phase:0,emoji:'x'};foods=[f];rebuildFoodGrid();player.eatNearby();return f.alive===false};"
new_helper = "window.__v48RadarHumanNumber=radarHumanNumber;window.__v48FoodPickupTest=function(){if(!player)return false;const r=7,range=45+(6+(data.upgrades.magnet-1)*5)-1,pts=[[range,0],[-range,0],[0,range],[0,-range]];foods=pts.map(function(q){return{x:wrap(player.x+q[0]),y:wrap(player.y+q[1]),v:.7,r:r,loot:false,golden:false,alive:true,ttl:1e9,phase:0,emoji:'x'}});rebuildFoodGrid();player.eatNearby();return foods.every(function(f){return f.alive===false})};"
if old_helper not in html:
    raise SystemExit('v4.9 target missing: v4.8 pickup helper')
html = html.replace(old_helper, new_helper, 1)

required = [
    'const collectRadius=this.isPlayer?Math.max(pickupRadius,45+magnet):pickupRadius;',
    'if(d<=collectRadius)',
    'foods.every(function(f){return f.alive===false})'
]
for token in required:
    if token not in html:
        raise SystemExit('v4.9 validation missing: '+token)
if 'f.x=wrap(f.x+delta(f.x,this.x)*pull)' in html:
    raise SystemExit('v4.9 old fruit-drag code still present')

p.write_text(html, encoding='utf-8')
print('v4.9 hard fruit pickup fix applied')
