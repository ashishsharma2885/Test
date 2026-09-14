from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')

# 1) Multiplayer already gives the results heading an id. v5.1 owns the final heading,
# so normalize exactly one generated tag before the v5.1 patch re-adds it.
expected='<div class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>'
already='<div id="postTitle" class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>'
if expected not in html:
    if already in html:
        html=html.replace(already,expected,1)
    else:
        raise SystemExit('Could not normalize generated post-match title for v5.1')

# 2) Insert the real game-mode selector call into renderLobby robustly. Earlier patches may
# add extra work around renderDifficultySelector(), so do not depend on exact adjacency.
fs=html.find('function renderLobby(){')
if fs<0:
    raise SystemExit('Could not locate renderLobby for v5.1')

# Brace-scan the function because an earlier patch may have changed which function follows it.
i=html.find('{',fs)
depth=0
quote=None
escape=False
fe=-1
while i < len(html):
    ch=html[i]
    if quote:
        if escape:
            escape=False
        elif ch=='\\':
            escape=True
        elif ch==quote:
            quote=None
    else:
        if ch in ('"',"'",'`'):
            quote=ch
        elif ch=='{':
            depth+=1
        elif ch=='}':
            depth-=1
            if depth==0:
                fe=i+1
                break
    i+=1
if fe<0:
    raise SystemExit('Could not find renderLobby end for v5.1')

block=html[fs:fe]
if 'renderGameModeSelector();' not in block:
    difficulty='renderDifficultySelector();'
    di=block.find(difficulty)
    if di>=0:
        pos=di+len(difficulty)
        block=block[:pos]+'\n  renderGameModeSelector();'+block[pos:]
    else:
        # Safe fallback: insert just before the function closes.
        block=block[:-1]+'  renderGameModeSelector();\n}'
    html=html[:fs]+block+html[fe:]

# 3) apply_v51_zonal_mode.py still contains one legacy exact replacement for the old
# adjacency. Give it a harmless JS-comment target so that replacement succeeds without
# changing the already-correct renderLobby implementation above.
legacy='  renderDifficultySelector();\n  resetDailyMissionsIfNeeded();'
# Do not let the exact target occur in live renderLobby, otherwise it could add a duplicate.
fs2=html.find('function renderLobby(){')
window=html[fs2:fs2+2500] if fs2>=0 else ''
if legacy in window:
    html=html[:fs2]+html[fs2:].replace(legacy,'  renderDifficultySelector();\n  renderGameModeSelector();\n  resetDailyMissionsIfNeeded();',1)

if legacy not in html:
    marker=html.rfind('</script>')
    if marker<0:
        raise SystemExit('Could not add v5.1 legacy lobby target comment')
    dummy='\n/* v5.1 compatibility target\n  renderDifficultySelector();\n  resetDailyMissionsIfNeeded();\n*/\n'
    html=html[:marker]+dummy+html[marker:]

p.write_text(html,encoding='utf-8')
print('v5.1 generated title + robust lobby targets prepared')
