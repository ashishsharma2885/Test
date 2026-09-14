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

# 2) Some earlier generated builds insert extra lobby work between these two calls.
# Preserve those calls, but move them after resetDailyMissionsIfNeeded so the v5.1
# patch can safely insert renderGameModeSelector between the canonical pair.
target='  renderDifficultySelector();\n  resetDailyMissionsIfNeeded();'
if target not in html:
    fs=html.find('function renderLobby(){')
    fe=html.find('\nfunction renderProfile(){',fs)
    if fs<0 or fe<0:
        raise SystemExit('Could not locate renderLobby for v5.1 normalization')
    block=html[fs:fe]
    a='  renderDifficultySelector();'
    b='  resetDailyMissionsIfNeeded();'
    ai=block.find(a);bi=block.find(b)
    if ai<0 or bi<0 or bi<ai:
        raise SystemExit('Could not normalize renderLobby calls for v5.1')
    between=block[ai+len(a):bi]
    block=block[:ai]+target+between+block[bi+len(b):]
    html=html[:fs]+block+html[fe:]

p.write_text(html,encoding='utf-8')
print('v5.1 generated title + lobby targets prepared')
