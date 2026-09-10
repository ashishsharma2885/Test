from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')

old="multiplayer.remoteTargets[cid]={x:wrap(safeNet(packet.x,s.x)),y:wrap(safeNet(packet.y,s.y)),a:safeNet(packet.a,s.angle),l:clamp(safeNet(packet.l,PLAYER_START_LENGTH),PLAYER_START_LENGTH,900),e:clamp(safeNet(packet.e,1),0,1),r:clamp(safeNet(packet.r,6.2),5,13),alive:packet.alive!==false};"
new="multiplayer.remoteTargets[cid]={x:wrap(safeNet(packet.x,s.x)),y:wrap(safeNet(packet.y,s.y)),a:safeNet(packet.a,s.angle),l:clamp(safeNet(packet.l,PLAYER_START_LENGTH),PLAYER_START_LENGTH,900),e:clamp(safeNet(packet.e,1),0,1),r:clamp(safeNet(packet.r,6.2),5,13),alive:s.alive};"
if old not in html: raise SystemExit('player state authority target missing')
html=html.replace(old,new,1)

old="if(id===roomClientId)coinFeedback(points);"
new="if(id===roomClientId)roomPointFeedback(points);"
if old not in html: raise SystemExit('point feedback target missing')
html=html.replace(old,new,1)

anchor="function scheduleRoomRespawn(snake,delay){"
insert="""function roomPointFeedback(points){
 const f=document.createElement('div');f.className='floatText';f.textContent='+'+points+' POINT'+(points===1?'':'S');f.style.left='50%';f.style.top='40%';f.style.color='#7dff9a';$('gameUI').appendChild(f);setTimeout(function(){f.remove()},1000);
}
function scheduleRoomRespawn(snake,delay){"""
if anchor not in html: raise SystemExit('respawn anchor missing')
html=html.replace(anchor,insert,1)

old="placeFreshSnake(snake,spawn);sendLocalPacket({t:'human_respawn',matchId:mid,id:snake.playerId,spawn:spawn})"
new="placeFreshSnake(snake,spawn);multiplayer.remoteTargets[snake.playerId]=normalizeTarget(stateOfSnake(snake,snake.playerId),snake);sendLocalPacket({t:'human_respawn',matchId:mid,id:snake.playerId,spawn:spawn})"
if old not in html: raise SystemExit('host respawn target missing')
html=html.replace(old,new,1)

old="if(s)s.alive=false;if(id===roomClientId){boost=false;releaseBoost();if($('roomRespawn'))$('roomRespawn').classList.add('show')}"
new="if(s){s.alive=false;if(multiplayer.remoteTargets[id])multiplayer.remoteTargets[id].alive=false}if(id===roomClientId){boost=false;releaseBoost();if($('roomRespawn'))$('roomRespawn').classList.add('show')}"
if old not in html: raise SystemExit('dead state target missing')
html=html.replace(old,new,1)

old="if(s)placeFreshSnake(s,packet.spawn||{});if(id===roomClientId){joystick.lastAngle=player.angle;"
new="if(s){placeFreshSnake(s,packet.spawn||{});multiplayer.remoteTargets[id]=normalizeTarget(stateOfSnake(s,id),s)}if(id===roomClientId){joystick.lastAngle=player.angle;"
if old not in html: raise SystemExit('guest respawn target missing')
html=html.replace(old,new,1)

p.write_text(html,encoding='utf-8')
print('Multiplayer room hotfix applied')
