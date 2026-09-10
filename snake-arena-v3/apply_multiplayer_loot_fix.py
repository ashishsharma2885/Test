from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global html
    if old not in html:
        raise SystemExit(f'Loot fix target missing: {label}')
    html = html.replace(old, new, 1)


rep(
    "function roomSnakeDie(victim,killer){\n if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='host'||!victim||!victim.alive)return;\n victim.alive=false;",
    """function spawnRoomDeathLoot(victim){
 if(!victim)return [];
 const drops=[];
 const segs=Array.isArray(victim.segments)?victim.segments:[];
 const maxDrops=72;
 const step=Math.max(1,Math.ceil(Math.max(1,segs.length)/maxDrops));
 if(segs.length>1){
  for(let i=1;i<segs.length;i+=step){
   const q=segs[i];if(!q)continue;
   const x=wrap(q.x+rand(-7,7)),y=wrap(q.y+rand(-7,7)),v=1.55;
   spawnFood(x,y,v,true);
   drops.push({x:+x.toFixed(1),y:+y.toFixed(1),v:v});
  }
 }
 if(!drops.length){
  const x=wrap(victim.x),y=wrap(victim.y),v=1.55;
  spawnFood(x,y,v,true);
  drops.push({x:+x.toFixed(1),y:+y.toFixed(1),v:v});
 }
 return drops;
}
function handleRoomDeathLoot(packet){
 if(!multiplayer.active||multiplayer.phase!=='playing'||String(packet.matchId||'')!==multiplayer.matchId)return;
 const drops=Array.isArray(packet.drops)?packet.drops.slice(0,80):[];
 for(const d of drops){
  const x=wrap(safeNet(d.x,0)),y=wrap(safeNet(d.y,0)),v=clamp(safeNet(d.v,1.55),.5,3);
  spawnFood(x,y,v,true);
 }
 rebuildFoodGrid();
}
function roomSnakeDie(victim,killer){
 if(!multiplayer.active||multiplayer.phase!=='playing'||multiplayer.role!=='host'||!victim||!victim.alive)return;
 victim.alive=false;
 const deathLoot=spawnRoomDeathLoot(victim);
 if(deathLoot.length)sendLocalPacket({t:'death_loot',matchId:multiplayer.matchId,drops:deathLoot});""",
    'room death loot creation'
)

rep(
    " if(packet.t==='human_dead'){handleHumanDead(packet);return}",
    " if(packet.t==='death_loot'){handleRoomDeathLoot(packet);return}\n if(packet.t==='human_dead'){handleHumanDead(packet);return}",
    'death loot network handler'
)

required = [
    'function spawnRoomDeathLoot(victim)',
    "t:'death_loot'",
    'function handleRoomDeathLoot(packet)',
    "if(packet.t==='death_loot')",
    'spawnFood(x,y,v,true)',
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('Multiplayer death-loot fix incomplete: ' + ', '.join(missing))

p.write_text(html, encoding='utf-8')
print('Multiplayer death loot synchronized')
