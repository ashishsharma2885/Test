from pathlib import Path

p=Path('/tmp/game-multiplayer.html')
html=p.read_text(encoding='utf-8')

expected='<div class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>'
already='<div id="postTitle" class="yellow" style="font-size:34px;font-weight:1000">GAME OVER</div>'

# The multiplayer patch already adds postTitle. v5.1 owns the final post-match title,
# so normalize this one generated tag before applying the v5.1 patch.
if expected not in html:
    if already in html:
        html=html.replace(already,expected,1)
    else:
        raise SystemExit('Could not normalize generated post-match title for v5.1')

p.write_text(html,encoding='utf-8')
print('v5.1 generated post-title target prepared')
