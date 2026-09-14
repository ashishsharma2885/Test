from pathlib import Path

p = Path('/tmp/game-multiplayer.html')
html = p.read_text(encoding='utf-8')


def rep(old, new, label, count=1):
    global html
    if old not in html:
        raise SystemExit(f'v5.3 target missing: {label}')
    html = html.replace(old, new, count)

rep(
"  speed:.86,turn:.78,decisionMin:.34,decisionMax:.62,avoidRange:82,\n  aggression:.38,boostChance:.18,boostEnergy:.42,combatRange:760,\n  combatLead:130,combatOffset:115,playerThreat:.08,easyCrashBonus:5",
"  speed:.88,turn:.82,decisionMin:.24,decisionMax:.45,avoidRange:86,\n  aggression:.70,boostChance:.32,boostEnergy:.38,combatRange:920,\n  combatLead:145,combatOffset:108,playerThreat:.04,easyCrashBonus:5",
'easy bot combat tuning')
rep(
"  speed:1,turn:1,decisionMin:.22,decisionMax:.44,avoidRange:112,\n  aggression:.55,boostChance:.46,boostEnergy:.30,combatRange:900,\n  combatLead:160,combatOffset:100,playerThreat:.28,easyCrashBonus:0",
"  speed:1.02,turn:1.04,decisionMin:.16,decisionMax:.32,avoidRange:116,\n  aggression:.82,boostChance:.58,boostEnergy:.27,combatRange:1080,\n  combatLead:175,combatOffset:94,playerThreat:.12,easyCrashBonus:0",
'normal bot combat tuning')
rep(
"  speed:1.12,turn:1.2,decisionMin:.12,decisionMax:.28,avoidRange:150,\n  aggression:.78,boostChance:.78,boostEnergy:.20,combatRange:1120,\n  combatLead:210,combatOffset:80,playerThreat:.62,easyCrashBonus:0",
"  speed:1.14,turn:1.24,decisionMin:.09,decisionMax:.21,avoidRange:154,\n  aggression:.92,boostChance:.84,boostEnergy:.18,combatRange:1320,\n  combatLead:225,combatOffset:76,playerThreat:.28,easyCrashBonus:0",
'hard bot combat tuning')

rep(
"     let score=(cfg.combatRange-d)+(other.isPlayer?80:145)+rand(-90,90);",
"     let score=(cfg.combatRange-d)+(other.isPlayer?45:300)+rand(-65,65);",
'prefer AI opponents')

rep(
"  if(this.ai.boostTimer<=0){\n   this.ai.boosting=(p.type==='combat'||p.type==='food')&&\n     Math.random()<cfg.boostChance&&this.energy>cfg.boostEnergy&&dToTarget>190;\n   this.ai.boostTimer=rand(.45,.9);\n  }",
"  if(this.ai.boostTimer<=0){\n   const botBoostChance=p.type==='combat'?Math.min(.96,cfg.boostChance+.10):cfg.boostChance;\n   this.ai.boosting=(p.type==='combat'||p.type==='food')&&\n     Math.random()<botBoostChance&&this.energy>cfg.boostEnergy&&dToTarget>190;\n   this.ai.boostTimer=rand(.42,.82);\n  }",
'combat boost pressure')

rep(
"  const base=this.isPlayer?value*.95*stage*upgrade:value*.82;\n  const growth=Math.max(this.isPlayer?.38:.30,base);",
"  const base=this.isPlayer?value*.95*stage*upgrade:value*1.28;\n  const growth=Math.max(this.isPlayer?.38:.45,base);",
'faster bot growth')

# Insert the CI hook beside the existing v5.1 runtime hook, inside the main game IIFE.
insert = r'''
window.__v53BotTuningTest=function(){
 const bot=snakes.find(function(s){return s&&!s.isPlayer&&s.alive});
 if(!bot)return false;
 const before=bot.length;bot.grow(1);const delta=bot.length-before;
 const m=DIFFICULTY.medium,h=DIFFICULTY.hard,e=DIFFICULTY.easy;
 return delta>=1.27&&e.aggression>=.69&&m.aggression>=.81&&h.aggression>=.91&&m.playerThreat<=.13&&m.combatRange>=1070;
};
'''
marker='window.handleAndroidBack=function(){'
if marker not in html:
    raise SystemExit('v5.3 target missing: scoped runtime helper marker')
if 'window.__v53BotTuningTest=' not in html:
    html=html.replace(marker,insert+'\n'+marker,1)

required = [
    'aggression:.70,boostChance:.32',
    'aggression:.82,boostChance:.58',
    'aggression:.92,boostChance:.84',
    '(other.isPlayer?45:300)',
    'const botBoostChance=',
    'value*1.28',
    "Math.max(this.isPlayer?.38:.45,base)",
    'window.__v53BotTuningTest=function()'
]
missing = [x for x in required if x not in html]
if missing:
    raise SystemExit('v5.3 bot patch incomplete: ' + ', '.join(missing))

p.write_text(html, encoding='utf-8')
print('v5.3 aggressive AI battles + faster bot growth applied')
