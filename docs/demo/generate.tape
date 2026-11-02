# Records docs/demo/generate.gif from a real run: `vhs docs/demo/generate.tape` from the repo root.
Output docs/demo/generate.gif
Set Shell "bash"
Set FontSize 15
Set Width 1300
Set Height 420
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 22ms

Hide
Type `export PS1='$ ' && uv sync -q && source .venv/bin/activate && clear` Enter
Sleep 10s
Show
Type `python -m constrained_generation_library generate` Enter
Sleep 2s
Type `python -m constrained_generation_library pattern` Enter
Sleep 2.5s
