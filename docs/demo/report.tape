# Records docs/demo/report.gif from a real run: `vhs docs/demo/report.tape` from the repo root.
Output docs/demo/report.gif
Set Shell "bash"
Set FontSize 15
Set Width 1300
Set Height 400
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 22ms

Hide
Type `export PS1='$ ' && uv sync -q && source .venv/bin/activate && clear` Enter
Sleep 10s
Show
Type `python -m constrained_generation_library report` Enter
Sleep 3.5s
