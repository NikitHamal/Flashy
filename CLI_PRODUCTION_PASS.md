# Flashy CLI production pass

This pass upgrades Flashy from a thin script into a small production CLI package while keeping the app minimal and hackable.

## Highlights

- Added `flashy_cli/` as the real CLI package and kept `cli.py` / `python -m flashy` compatible shims.
- Polished commands: `chat`, `ask`, `serve`, `server`, `status`, `config`, `init`, `doctor`, `tools`, `models`, and `version`.
- Made bare prompts work like modern coding CLIs: `flashy "fix the failing tests"` routes straight into chat.
- Added JSON output for automation and scripts: `flashy --json doctor`, `flashy --json status`, `flashy --json tools`.
- Added `flashy doctor` for pre-flight checks covering Python, dependencies, workspace permissions, git, ripgrep, node, internet, config, servers, and tool registry health.
- Fixed CLI config handling to use the same backend user-data config file instead of reading a stale project-root `config.json`.
- Added `flashy init` for a clean first-run setup, with optional confirmations.
- Added session overrides for `--provider`, `--model`, `--reasoning`, and `--max-iterations` without forcing permanent config edits.
- Added in-chat `/help`, `/status`, `/workspace`, `/config`, and `/tools` commands.
- Lowered the default agent tool-loop cap from 500 to 25 via `max_agent_iterations` so runaway loops fail fast.
- Fixed broken tooling imports in git/collaboration helpers.
- Tightened workspace path handling for directory listing, tree, search, grep, explorer data, and command CWDs.
- Added smoke tests under `tests/`.

## Recommended commands

```bash
python cli.py doctor
python cli.py --json status
python cli.py init --provider g4f --model gpt-5.4-nano
python cli.py "inspect this repo and propose the safest next refactor"
python -m unittest discover -s tests
```


## Terminal UI/UX follow-up pass

A second focused pass polished the interactive terminal layer: prompt history, slash-command autocomplete, bottom toolbar, cleaner banners/help/status/tools/config tables, quieter thinking by default, opt-in `--show-thinking`, `/verbose`, workspace switching from chat, safer Rich output rendering, compact tool-call summaries, and turn timing/context summaries.


## Daily-driver pass (0.3.0)

A third pass turns the CLI into a true daily-driver that feels like Claude Code / Gemini CLI / Codex CLI.

### New commands

- `flashy session list|show|delete|export|resume` - manage saved chat sessions
- `flashy theme list|set|show` - switch between `default`, `mono`, `solarized`, `dracula`
- `flashy stats` - lifetime session stats with provider/model breakdown
- `flashy logs` - tail the rolling JSONL log, with `--path`, `--clear`, `--level` flags
- `flashy completions bash|zsh|fish|powershell` - print shell completion scripts to stdout
- `flashy config --edit` - open the active config in `$EDITOR`

### New chat flags

- `flashy chat --resume <id>` - resume a saved session by id or prefix
- `flashy chat --continue` - resume the most recent session in this workspace

### New in-chat commands

- `/save` - save the current session (auto-save runs on every turn)
- `/load <id>` - load a previous session into the running chat
- `/sessions` / `/history` - list recent sessions
- `/resume <id>` - jump into a previous session
- `/export [md|json] [path]` - export the current session
- `/copy` - copy the last assistant reply to the system clipboard
- `/init` - write a starter `AGENTS.md` rules file
- `/reset` - alias of `/clear`

### Productivity niceties

- Markdown rendering for assistant text (code blocks highlighted, lists, inline code)
- `@file` attachments in user messages - resolved against the active workspace
- Stdin / pipe support - `cat file.py | flashy "review this"`
- Auto-save on every turn so a crash never loses work
- Lazy prompt-toolkit init so piped / non-tty usage doesn't crash
- ASCII-safe JSON output for Windows consoles
- Friendly hints after errors and stats
- Internet reachability check in `doctor`
- Optional `questionary` picker for `flashy init` (no prompts when `-y`)

### Shell completions

```bash
# bash
flashy completions bash >> ~/.bashrc

# zsh
flashy completions zsh > ~/.zsh/completions/_flashy

# fish
flashy completions fish > ~/.config/fish/completions/flashy.fish

# powershell
flashy completions powershell | Out-String | Invoke-Expression
```

### Validation

```bash
python -m compileall -q cli.py flashy_cli backend
python -m unittest discover -s tests -v
python cli.py chat --help
python cli.py --json version
python cli.py doctor
```

