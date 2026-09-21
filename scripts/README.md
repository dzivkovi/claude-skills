# Scripts

Repo tooling that isn't itself a skill - things the skills, or the person driving them, need to have working first.

| Script | What it does |
|---|---|
| [`build-skills.sh`](./build-skills.sh) | Packages each folder under `skills/` into a `.zip` in `releases/`, ready to upload to claude.ai. |
| [`chrome-cdp.sh`](./chrome-cdp.sh) | Starts, checks, or kills a Chrome instance dedicated to CDP browser automation, and verifies it's actually *yours* before anything trusts it. |

## chrome-cdp.sh

### Why this exists

Browser-automation tools - the `chrome-cdp` MCP server, the `agent-browser` CLI, a hand-rolled script - all work the same way: they connect to whatever Chrome process answers on a debug port (commonly `9222`). None of them can tell your intended browser apart from a stray one left running by an unrelated project. They just trust the port.

That's not hypothetical. An orphaned headless Chrome from a different project sat on port `9222` for more than a day. A naive health check (`curl the port, did it answer?`) and an agent connecting to "port 9222" both trusted it as healthy - it answered fast enough - and ended up silently driving the wrong browser: a bot-detection wall that should never have applied got blamed on the site, when the real problem was automating a headless process nobody meant to still be running.

This script's one job is closing that gap: before calling the port healthy, it fetches the actual process's command line and checks it was launched with *your* `--user-data-dir`, not just "some Chrome that happens to be listening."

### Install

Either works; pick one.

```bash
# Option A - source it, get a chrome-cdp() shell function
echo 'source "$HOME/ws/Skills/claude-skills/scripts/chrome-cdp.sh"' >> ~/.bashrc

# Option B - put scripts/ on PATH and call it as a program
export PATH="$PATH:$HOME/ws/Skills/claude-skills/scripts"
chmod +x ~/ws/Skills/claude-skills/scripts/chrome-cdp.sh
# then: chrome-cdp.sh status   (or symlink it to plain `chrome-cdp` somewhere on PATH)
```

### Usage

```bash
chrome-cdp            # start it (or report it's already up and healthy)
chrome-cdp status      # read-only: what's on the port, and is it yours?
chrome-cdp kill        # kill whatever holds the port, yours or not
chrome-cdp restart      # kill + start
```

Sample output when a stray process is squatting on the port:

```
$ chrome-cdp
chrome-cdp: port 9222 is held by something ELSE (pid 34592), not your profile:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new ... --user-data-dir=...\some-other-project\scratchpad\chrome-profile ...
chrome-cdp: run 'chrome-cdp kill' to free it, then 'chrome-cdp' again
```

That message is the entire point of this script. A liveness check alone would have just said "already up."

### Config

Override before sourcing/running if the defaults don't fit:

- `CHROME_CDP_PORT` - debug port (default `9222`)
- `CHROME_CDP_PROFILE` - dedicated `--user-data-dir` (default: `~/.config/chrome-cdp-profile` on Windows, a `chrome-cdp-profile` folder under `$TMPDIR`/`/tmp` on macOS/Linux)

### Platform status

**Windows + Git Bash (MINGW64) is the tested, primary path** - the process-identity check shells out to PowerShell (`Get-CimInstance Win32_Process`), and port discovery uses `netstat -ano`. The macOS/Linux branches (`lsof` for the port, `ps -o command=` for the identity check) are believed correct but have not been run against a real stray-process case the way the Windows path has. If you hit something on macOS/Linux, a PR is very welcome.

## The four things all named "chrome" + "cdp" (read this before you get confused)

Four different tools share this territory. They're not competitors - they're different layers - but the names collide enough that it's worth spelling out once, here, rather than everyone rediscovering it independently.

| Name | What it actually is | Layer |
|---|---|---|
| **CDP** (Chrome DevTools Protocol) | The underlying wire protocol every one of these speaks. Not a tool - the thing the tools have in common. | protocol |
| **`chrome-cdp.sh`** (this script) | A lifecycle manager: start/check/kill a specific Chrome process on a specific port, and verify it's the right one before anyone trusts it. | infrastructure - keeps the browser alive and honest |
| **the `chrome-cdp` MCP server** | An MCP server (tools like `mcp__chrome-cdp__navigate_page`, `mcp__chrome-cdp__click`, ...) that an agent calls to actually drive a page - click, type, navigate, screenshot. It connects to whatever's on the debug port; it does not manage that Chrome's lifecycle. | driver (MCP-based) |
| **`agent-browser`** | A separate, standalone CLI (Rust, installed via npm) that also drives a page over CDP, with its own command set (`open`, `click`, `snapshot`, ...) and its own way to attach to an existing browser: `agent-browser connect <port>`. Functionally overlaps with the MCP server above but is a different tool with a different interface. | driver (CLI-based) |

In short: `chrome-cdp.sh` makes sure the browser exists and is the right one. The MCP server and `agent-browser` are two different, interchangeable ways to then drive it. Neither driver checks whose browser it's talking to - that's what this script is for, run it first.

## Related

[`skills/read-along/SKILL.md`](../skills/read-along/) launches and drives its own CDP Chrome independently, with its own port-safety logic (a lighter-weight "probe the port, verify the only tab is the one you just opened" check, tuned to its one-CDP-session-per-machine assumption). It does not currently use this script - the two were written for different situations and haven't been reconciled yet. If you're touching CDP port-safety in either place, check the other.
