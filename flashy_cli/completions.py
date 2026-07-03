"""Shell completion scripts for Flashy.

Supports bash, zsh, fish, and PowerShell. Generated scripts are short, self-contained,
and don't rely on the user installing anything beyond the `flashy` command.
"""
from __future__ import annotations

from typing import Dict

COMMANDS = [
    "chat",
    "ask",
    "interactive",
    "serve",
    "start",
    "run",
    "server",
    "status",
    "config",
    "init",
    "doctor",
    "tools",
    "models",
    "session",
    "theme",
    "stats",
    "logs",
    "completions",
    "version",
    "help",
]

GLOBAL_FLAGS = ["--json", "--no-color", "-C", "--cwd", "-h", "--help", "-v", "--version"]

IN_CHAT_COMMANDS = [
    "/help",
    "/clear",
    "/reset",
    "/model",
    "/provider",
    "/thinking",
    "/verbose",
    "/thoughts",
    "/compact",
    "/status",
    "/doctor",
    "/workspace",
    "/cwd",
    "/config",
    "/tools",
    "/save",
    "/load",
    "/sessions",
    "/export",
    "/copy",
    "/exit",
    "/quit",
]


BASH_SCRIPT = r"""# bash completion for flashy
_flashy_completion() {
    local cur prev words cword
    if type _init_completion >/dev/null 2>&1; then
        _init_completion || return
    else
        COMPREPLY=()
        cur="${COMP_WORDS[COMP_CWORD]}"
        prev="${COMP_WORDS[COMP_CWORD-1]}"
    fi

    local commands="%s"
    local flags="%s"
    local in_chat="%s"

    if [[ ${cur} == /* ]]; then
        COMPREPLY=( $(compgen -W "${in_chat}" -- ${cur}) )
        return 0
    fi

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands} ${flags}" -- ${cur}) )
        return 0
    fi

    COMPREPLY=( $(compgen -W "${flags}" -- ${cur}) )
}
complete -F _flashy_completion flashy
""" % (" ".join(COMMANDS), " ".join(GLOBAL_FLAGS), " ".join(IN_CHAT_COMMANDS))


ZSH_SCRIPT = r"""#compdef flashy
# zsh completion for flashy
_flashy() {
    local -a commands flags in_chat
    commands=(
        'chat:Start an AI coding session'
        'ask:Ask a one-shot question'
        'serve:Start the Flashy web server'
        'server:Start the OpenAI-compatible provider server'
        'status:Check local server status'
        'config:View or modify CLI configuration'
        'init:Create or update Flashy config'
        'doctor:Run pre-flight diagnostics'
        'tools:List available agent tools'
        'models:List available models for a provider'
        'session:Manage chat sessions'
        'theme:List or switch themes'
        'stats:Show session statistics'
        'logs:Tail Flashy logs'
        'completions:Print shell completion scripts'
        'version:Show version and runtime info'
    )
    flags=(
        '--json' '--no-color' '--cwd:-:' '-C:-:'
    )
    in_chat=(
        '/help' '/clear' '/reset' '/model' '/provider' '/thinking' '/verbose'
        '/thoughts' '/compact' '/status' '/doctor' '/workspace' '/cwd'
        '/config' '/tools' '/save' '/load' '/sessions' '/export' '/copy'
        '/exit' '/quit'
    )
    _arguments -s \
        '1: :->cmd' \
        '*:: :->args'
    case $state in
        cmd)
            if [[ ${words[2]} == /* ]]; then
                _describe 'in-chat command' in_chat
            else
                _describe 'flashy command' commands
            fi
            ;;
    esac
}
_flashy "$@"
"""


FISH_SCRIPT = r"""# fish completion for flashy
function __flashy_complete
    set -l commands %s
    set -l flags %s
    set -l in_chat %s
    set -l tokens (commandline -opc) (commandline -ct)
    set -l cur (commandline -ct)
    if string match -q -r '^/' -- $cur
        printf "%%s\n" $in_chat
        return
    end
    if test (count $tokens) -le 2
        printf "%%s\n" $commands $flags
    else
        printf "%%s\n" $flags
    end
end
complete -c flashy -f -a "(__flashy_complete)"
""" % (" ".join(COMMANDS), " ".join(GLOBAL_FLAGS), " ".join(IN_CHAT_COMMANDS))


POWERSHELL_SCRIPT = r"""# PowerShell completion for flashy
Register-ArgumentCompleter -Native -CommandName 'flashy' -ScriptBlock {
    param($wordToComplete, $commandAst, $cursorPosition)

    $commands = @(%s)
    $flags = @(%s)
    $inChat = @(%s)

    $tokens = $commandAst.ToString() -split '\s+'
    if ($wordToComplete -like '/*') {
        $inChat | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
            [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
        }
        return
    }
    if ($tokens.Count -le 2) {
        $all = $commands + $flags
    } else {
        $all = $flags
    }
    $all | Where-Object { $_ -like "$wordToComplete*" } | ForEach-Object {
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterName', $_)
    }
}
""" % (
    ", ".join(f"'{c}'" for c in COMMANDS),
    ", ".join(f"'{f}'" for f in GLOBAL_FLAGS),
    ", ".join(f"'{c}'" for c in IN_CHAT_COMMANDS),
)


SCRIPTS: Dict[str, str] = {
    "bash": BASH_SCRIPT,
    "zsh": ZSH_SCRIPT,
    "fish": FISH_SCRIPT,
    "powershell": POWERSHELL_SCRIPT,
}


def render(shell: str) -> str:
    key = shell.lower().strip()
    aliases = {
        "ps": "powershell",
        "pwsh": "powershell",
        "sh": "bash",
    }
    key = aliases.get(key, key)
    if key not in SCRIPTS:
        raise ValueError(f"Unknown shell: {shell}. Supported: {', '.join(SCRIPTS)}")
    return SCRIPTS[key]


def all_shells() -> list[str]:
    return list(SCRIPTS.keys())

