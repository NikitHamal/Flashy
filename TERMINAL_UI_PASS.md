# Terminal UI/UX Production Pass

This pass focuses on making Flashy feel like a serious daily coding CLI without adding heavy framework complexity.

## What changed

- Added a cleaner Rich-powered welcome surface with workspace, model, reasoning, and mode.
- Added prompt_toolkit command autocomplete for slash commands.
- Added persistent CLI prompt history in Flashy's user data directory.
- Added a bottom toolbar showing model, context usage, reasoning effort, and output mode.
- Made the assistant turn header cleaner and easier to scan.
- Changed raw thinking output to a clean `thinking…` progress line by default.
- Added `/verbose` / `/thoughts` to toggle raw streamed thinking tokens when desired.
- Added `flashy chat --show-thinking` for one-off verbose thinking sessions.
- Upgraded `/help` into a command palette-style table.
- Upgraded `/config`, `/tools`, and `/status` into readable terminal tables.
- Added `/workspace <path>` / `/cwd <path>` to switch workspace inside chat.
- Added compact, useful tool-call rendering with action labels, paths/commands, edit stats, duration, and result summaries.
- Stopped Rich from interpreting model output as markup, preventing broken output when the model prints brackets or markup-like code.
- Added final turn summaries with duration, tool count, and context usage.
- Kept plain-terminal fallbacks intact when Rich or prompt_toolkit are not available.
- Honored `--no-color` for the interactive chat console.

## UX principles used

- Default to clean output, not noisy logs.
- Keep advanced visibility available, but opt-in.
- Make command discovery immediate.
- Make tool activity trustworthy and glanceable.
- Avoid overengineering: no heavy TUI framework, no extra daemon, no complicated security layer.

## Validation

- `python -m compileall -q cli.py flashy_cli backend`
- `python -m unittest discover -s tests -v`
- `python cli.py chat --help`
- `python cli.py --json version`
