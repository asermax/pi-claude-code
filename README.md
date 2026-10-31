# pi-claude-code

This is a fork of [earendil-works/pi-claude-code](https://github.com/earendil-works/pi-claude-code),
which has not merged a fix since 2026-10-12. It carries the fixes that live in
other forks and unmerged pull requests, plus one for the warm-process failure in
issue #16:

| Problem | Fix source |
| --- | --- |
| Fable 5.1 returns 400 "A maximum of 4 blocks with cache_control" after a tool result | #10, #11 (jdbrew88) |
| Lost upstream stream or 5xx ends the turn instead of being retried | #8, #4 (series-phil), #9 (B0und) |
| Warm continuation fails in milliseconds with "assistant, message_stop and one result required" | #16, this fork |
| Switching from Codex or GPT to Claude fails 400 on tool-call IDs containing `\|` | #3, #6 (adstastic), #7 |
| Thinking signatures issued by another provider are replayed and rejected | Stratinator |
| `thinking.type: disabled` rejected by Opus 5.5 and Sonnet 5.5 | #2, #13 (panchogn) |
| Thinking text never shown, because adaptive thinking asked for no display | #17 (hanselime) |
| A tool name Claude invents fails the whole turn | #14 (series-phil, getpaperplane) |
| Auth inside `~/.claude/settings.json` is ignored | #15 (arhen) |
| A `ttl=1h` breakpoint placed after Claude Code's 5m one returns 400 | #15 (arhen) |
| An inherited `ANTHROPIC_API_KEY` blocks the subscription provider | #5 (adstastic) |
| Nested `null` schema variants dropped, so the model sends the string `"null"` | Stratinator |
| Claude Code runs in the wrong directory when the host names one in metadata | Stratinator |
| Request-rewrite failures show as a lost connection and are retried | ioanlucut |
| A first user message sent as a string aborts the turn | ioanlucut |

The test script uses `tsx`, because Node 26 removed
`--experimental-transform-types`.

This Pi extension lets you use your Claude Pro or Max subscription in Pi by
routing all Claude model requests through the official Claude Code CLI.

Pi still handles conversation history, approvals, compaction, and tool
execution. Claude Code only talks to the model. It never runs tools itself.

> [!WARNING]
> **The future of this extension is uncertain.** Right now it works by running
> Pi's requests through the official Claude Code CLI in non-interactive mode
> (`claude -p`), and that usage counts against your normal Claude subscription
> limits. In May 2026 Anthropic
> [announced](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan)
> that `claude -p`, Agent SDK, and third-party usage would move to a separate,
> smaller "Agent SDK credit" billed at API rates. Anthropic has since put that
> change on hold and says it will give advance notice before any future change.
>
> Until then the extension keeps working as described here, but that could
> change at any time. If Anthropic changes how `claude -p` usage is billed, this
> extension may cost more, stop drawing from your subscription, or stop working
> altogether. See Zed's
> [write-up](https://zed.dev/blog/anthropic-subscription-changes) for more
> background.

## Requirements

- Pi
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code), installed and
  on your `PATH`:

  ```sh
  npm install -g @anthropic-ai/claude-code
  ```

- A Claude subscription that you are logged into with Claude Code

## Installation

```sh
pi install https://github.com/earendil-works/pi-claude-code
```

Then pick a model from the **Claude Code Subscription (Experimental)** provider
in Pi.

## Login and logout

Claude Code handles authentication. Log in and out with the Claude Code CLI:

```sh
claude auth login
claude auth logout
```

The extension uses whatever login Claude Code currently has. You don't need
Pi's `/login` or `/logout` for this provider. The extension doesn't read, copy,
or store your Claude Code credentials.

Run `/claude-code-status` in Pi to check that Claude Code is installed and
logged in.

## Configuration

These environment variables are optional:

- `PI_CLAUDE_CODE_COMMAND`: path or name of the Claude Code executable
  (default: `claude`).
- `PI_CLAUDE_CODE_CONFIG_DIR`: Claude Code config directory to use. The
  extension passes it to Claude Code as `CLAUDE_CONFIG_DIR`.
- `PI_CLAUDE_CODE_INHERIT_SETTINGS_AUTH`: when set to a truthy value, pass
  `env.ANTHROPIC_AUTH_TOKEN` or `env.ANTHROPIC_API_KEY` from Claude Code's own
  `settings.json` / `settings.local.json` to the Claude Code process. The
  extension runs Claude Code with its settings disabled so user hooks and
  skills never change Pi turns, and that also hides logins stored in those
  files (for example a `claude setup-token` value). Enable this only when the
  token is your Claude subscription token; a token already present in Pi's
  environment is still rejected so billing cannot change silently.

Spawned Claude Code processes always receive `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, overriding inherited values, so Claude Code's automatic memory does not add duplicate context.

## Usage and billing

Requests made through this extension count against your Claude subscription's
usage quota and rate limits, the same as any other Claude Code usage. The
extension does not give you separate or unlimited usage.

The extension ignores `ANTHROPIC_API_KEY` in Claude Code child processes without
changing your environment. To avoid silently changing how you're authenticated
or billed, it still rejects auth-token, proxy, Bedrock, Vertex, or Foundry
overrides for Claude Code.

## Limitations

- The extension is experimental.
- Logins stored in Claude Code's `settings.json` are invisible to the extension
  unless `PI_CLAUDE_CODE_INHERIT_SETTINGS_AUTH` is set, because turns run with
  Claude Code's settings disabled. A login created by `claude auth login` works
  without that flag.
- Branching, editing earlier messages, or changing settings mid-conversation
  starts a fresh Claude Code process that replays the conversation. The first
  response after that can be slower and may use more quota.
- Top-level composition in a tool schema (`oneOf`, `allOf`, `anyOf`) is
  removed before Claude sees it; nested schemas, nullable ones included, pass
  unchanged.
- Adding or removing tools in the middle of a conversation keeps the prompt
  cache only on supported models. On other models it may use more quota.

For details on how the extension works internally, see
[ARCHITECTURE.md](ARCHITECTURE.md).
