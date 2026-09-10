from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')

old = r''' eatNearby(){
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

new = r''' eatNearby(){
  const magnetLevel=clamp(Number(data.upgrades.magnet)||1,1,10);
  const buckets=neighborBuckets(foodGrid,this.x,this.y,FOOD_CELL,FOOD_CELLS,1);
  for(const b of buckets){for(const f of b){
   if(!f.alive)continue;
   // Pickup is measured from the snake HEAD only.
   // Magnet Lv.1 has a SMALL 6px magnetic bonus; every upgrade adds 5px more.
   // This gives visible/useful magnet behavior from the start without collecting fruit far away.
   const pickupRadius=this.radius+f.r+3;
   const magnetBonus=this.isPlayer?6+Math.max(0,magnetLevel-1)*5:0;
   const collectRadius=pickupRadius+magnetBonus;
   const d=distance(this.x,this.y,f.x,f.y);
   if(d<=collectRadius){
    f.alive=false;
    this.grow(f.v);
    if(this.isPlayer)awardFood(f);
   }
  }}
 }'''

if old not in html:
    # Support rebuilding on top of the previous v4.9 patch during iterative CI runs.
    old = r''' eatNearby(){
  const magnetLevel=clamp(Number(data.upgrades.magnet)||1,1,10);
  const buckets=neighborBuckets(foodGrid,this.x,this.y,FOOD_CELL,FOOD_CELLS,1);
  for(const b of buckets){for(const f of b){
   if(!f.alive)continue;
   // Pickup is measured from the SNAKE HEAD only. At Magnet Lv.1 the fruit must be
   // almost touching the face. Extra collection distance exists only after upgrades.
   const pickupRadius=this.radius+f.r+3;
   const magnetBonus=this.isPlayer?Math.max(0,magnetLevel-1)*5:0;
   const collectRadius=pickupRadius+magnetBonus;
   const d=distance(this.x,this.y,f.x,f.y);
   if(d<=collectRadius){
    f.alive=false;
    this.grow(f.v);
    if(this.isPlayer)awardFood(f);
   }
  }}
 }'''
if old not in html:
    raise SystemExit('v4.9.1 target missing: eatNearby block')
html = html.replace(old, new, 1)

# Runtime balance test:
# - Lv.1 has a small real magnet bonus.
# - It still does NOT collect fruit well outside that small zone.
# - Lv.2 expands the collection radius further.
start = html.find('window.__v48FoodPickupTest=function(){')
if start < 0:
    raise SystemExit('v4.9.1 target missing: pickup test helper')
end = html.find('};', start)
if end < 0:
    raise SystemExit('v4.9.1 helper end missing')
end += 2
helper = "window.__v48FoodPickupTest=function(){if(!player)return false;const oldLv=data.upgrades.magnet,r=5,base=player.radius+r+3;function mk(dist){return{x:wrap(player.x+dist),y:player.y,v:.7,r:r,loot:false,golden:false,alive:true,ttl:1e9,phase:0,emoji:'x'}}data.upgrades.magnet=1;let near=mk(base+5.5),far=mk(base+9);foods=[near,far];rebuildFoodGrid();player.eatNearby();const level1Ok=!near.alive&&far.alive;data.upgrades.magnet=2;let upgraded=mk(base+9);foods=[upgraded];rebuildFoodGrid();player.eatNearby();const level2Ok=!upgraded.alive;data.upgrades.magnet=oldLv;return level1Ok&&level2Ok};"
html = html[:start] + helper + html[end:]

required = [
    'const magnetLevel=clamp(Number(data.upgrades.magnet)||1,1,10);',
    'const pickupRadius=this.radius+f.r+3;',
    'const magnetBonus=this.isPlayer?6+Math.max(0,magnetLevel-1)*5:0;',
    'const collectRadius=pickupRadius+magnetBonus;',
    'window.__v48FoodPickupTest=function()'
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('v4.9.1 patch incomplete: ' + ', '.join(missing))
if 'Math.max(pickupRadius,45+magnet)' in html:
    raise SystemExit('Old oversized base magnet range still present')
if 'f.x=wrap(f.x+delta(f.x,this.x)*pull)' in html:
    raise SystemExit('Fruit drag code returned')

p.write_text(html, encoding='utf-8')
print('v4.9.1 small level-1 magnet + progressive upgrades applied')
