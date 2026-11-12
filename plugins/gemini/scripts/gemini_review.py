"""Ask Google's Gemini for a read-only peer review or second opinion.

Standard library only. Reads the key from GEMINI_API_KEY and never prints it.
Answers go to stdout; model, thinking level, session and token usage go to stderr.

Three modes:

  File mode (Gemini sees only one self-contained file, via the REST API):
    python gemini_review.py --file review.md [--ask "focused question"]
        [--model carbon] [--thinking high] [--out answer.md]

  Setup (readiness report; exit 1 when Python or the key is missing):
    python gemini_review.py --setup

  Repo mode (Gemini CLI reads the repository in the current directory, read-only):
    python gemini_review.py --repo --brief brief.md [--resume [SESSION_ID]] [--model carbon]

  Helpers:
    --list                      print the available generateContent model ids
    --resolve-only --model X    print the resolved model id

--model takes an exact id (starts with gemini- or models/) or a short alias word
(carbon, argon, flash, pro) that resolves to the newest matching model available today.

Exit codes: 0 ok; 1 failure; 2 usage error (argparse); 3 repo mode unavailable
(the caller falls back to file mode); 4 the working tree changed during a repo-mode
run; 5 unknown model alias.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
API_BASE_URL = "https://generativelanguage.googleapis.com"
DEFAULT_MODEL = "carbon"
DEFAULT_THINKING = "high"
EXCLUDED_TOKENS = {
    "preview",
    "exp",
    "experimental",
    "tts",
    "image",
    "embedding",
    "live",
    "audio",
    "lite",
    "thinking",
}
KEY_VAR = "GEMINI_API_KEY"
TIMEOUT_S = 300
# A repo-mode run took over 9 minutes on 2026-11-11 (2 to 4 minute thinking turns), so
# skills run repo mode in background Bash, which has no 600 s foreground cap.
REPO_TIMEOUT_S = 1200
TRANSIENT = {429, 500, 502, 503, 504}

STATUS_TIMEOUT = -1

EXIT_FAIL = 1
# 2 is taken by argparse usage errors and by Python's "can't open file".
EXIT_REPO_UNAVAILABLE = 3
EXIT_TREE_CHANGED = 4
EXIT_UNKNOWN_ALIAS = 5

HERE = Path(__file__).resolve().parent
POLICY_PATH = HERE / "repo-mode-policy.toml"
SETTINGS_PATH = HERE / "repo-mode-settings.json"
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9-]+$")
SYSTEM_SETTINGS_PATHS = {
    "win32": r"C:\ProgramData\gemini-cli\settings.json",
    "darwin": "/Library/Application Support/GeminiCli/settings.json",
}
SYSTEM_SETTINGS_DEFAULT = "/etc/gemini-cli/settings.json"
CMD_METACHARACTERS = set('%"^&|<>')

PREAMBLE = (
    "You are an independent peer reviewer from outside the team that wrote this material. "
    "Be direct and specific. Disagree where you disagree; agreement is not the goal. "
    "Give numbered findings. When the material is code or a diff, give each finding a severity "
    "(P0 blocker, P1 should fix, P2 nice to have). "
    "You see only the text below, not the repository: say plainly what you cannot judge from "
    "the material alone instead of guessing."
)

# Constant on purpose: the brief travels on stdin, so argv stays short and holds no
# user text (a long argv hung a CLI on Windows, and argv passes through cmd.exe there).
REPO_PROMPT = (
    "The text above is your brief. You are an independent read-only peer reviewer. "
    "Read only the repository files the brief needs, starting with the ones it names, and stop "
    "exploring as soon as you can answer. Give numbered findings "
    "with a severity (P0 blocker, P1 should fix, P2 nice to have) and cite file paths. "
    "Disagree where you disagree. Say plainly what you could not check."
)


def fail(message: str, code: int = EXIT_FAIL) -> None:
    print(f"gemini_review: {message}", file=sys.stderr)
    sys.exit(code)


def force_utf8_output() -> None:
    """A piped stdout on Windows defaults to cp1252 and crashes on the first arrow."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


# ---------------------------------------------------------------- REST (file mode)


def _is_timeout(exc: BaseException) -> bool:
    return isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError)


def call(url: str, key: str, body: dict | None) -> tuple[int, dict]:
    """One HTTP call. Returns (status, parsed JSON).

    Status 0 is a connection-level failure worth one retry; STATUS_TIMEOUT is a read
    timeout, which is a slow thinking turn rather than a blip and is not retried.
    """
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if body is not None else "GET",
        headers={"x-goog-api-key": key, "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": {"message": raw[:600]}}
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        if _is_timeout(exc):
            return STATUS_TIMEOUT, {"error": {"message": f"no answer within {TIMEOUT_S} s"}}
        return 0, {"error": {"message": f"network error: {exc}"}}
    try:
        return status, json.loads(raw)
    except json.JSONDecodeError:
        return 0, {"error": {"message": f"unreadable response: {raw[:600]}"}}


def call_with_retry(url: str, key: str, body: dict | None) -> tuple[int, dict]:
    status, data = call(url, key, body)
    if status == 0 or status in TRANSIENT:
        print(f"gemini_review: transient failure ({status}), retrying once in 5 s", file=sys.stderr)
        time.sleep(5)
        status, data = call(url, key, body)
    return status, data


def list_models(key: str) -> list[str]:
    """All generateContent model ids (without the models/ prefix), sorted.

    A failed listing exits 1 with the HTTP error: reporting it as an unknown alias
    would hide a bad key, a quota error or a network outage.
    """
    ids: set[str] = set()
    token = ""
    while True:
        query = urllib.parse.urlencode({"pageSize": 1000, **({"pageToken": token} if token else {})})
        status, data = call_with_retry(f"{API_ROOT}/models?{query}", key, None)
        if status != 200:
            message = data.get("error", {}).get("message", str(data))[:600]
            fail(f"cannot list models: HTTP {status}: {message}")
        ids.update(
            m["name"].removeprefix("models/")
            for m in data.get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        )
        token = data.get("nextPageToken", "")
        if not token:
            break
    return sorted(ids)


def _version(model_id: str) -> tuple[int, ...]:
    match = re.match(r"gemini-(\d+(?:\.\d+)*)", model_id)
    return tuple(int(n) for n in match.group(1).split(".")) if match else ()


def pick_model(alias: str, ids: list[str]) -> str | None:
    """Newest model id whose hyphen-separated tokens include the alias, or None."""
    candidates = [
        i
        for i in ids
        if alias in i.split("-") and not ((EXCLUDED_TOKENS - {alias}) & set(i.split("-")))
    ]
    if not candidates:
        return None
    latest = f"gemini-{alias}-latest"
    if latest in candidates:
        return latest
    # Highest version first (no number sorts lowest), then shortest id, then alphabetical.
    best = max(_version(i) for i in candidates)
    top = [i for i in candidates if _version(i) == best]
    return sorted(top, key=lambda i: (len(i), i))[0]


def resolve_model(asked: str, key: str) -> str:
    if asked.startswith(("gemini-", "models/")):
        return asked.removeprefix("models/")
    ids = list_models(key)
    picked = pick_model(asked, ids)
    if picked is None:
        listing = ", ".join(ids[:30]) if ids else "(could not list models)"
        print(
            f"gemini_review: no generateContent model matches alias '{asked}'. Available: {listing}",
            file=sys.stderr,
        )
        sys.exit(EXIT_UNKNOWN_ALIAS)
    return picked


def build_body(text: str, thinking: str) -> dict:
    """Request body. The thinking level is always explicit: an unset level ran with no
    thinking on gemini-4-carbon but with full thinking on gemini-flash-latest (2026-11-11)."""
    return {
        "systemInstruction": {"parts": [{"text": PREAMBLE}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {"thinkingConfig": {"thinkingLevel": thinking}},
    }


def run_file_mode(args: argparse.Namespace, key: str) -> None:
    model = resolve_model(args.model, key)
    print(f"model: {args.model} -> {model}, thinking {args.thinking}", file=sys.stderr)
    if args.resolve_only:
        print(model)
        return
    if not args.file:
        fail("--file is required unless --setup, --repo, --list or --resolve-only is given.")
    path = Path(args.file)
    if not path.is_file():
        fail(f"file not found: {path}")

    try:
        material = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read {path} as UTF-8 text: {exc}")
    text = f"{material}\n\n## Focused ask\n\n{args.ask}" if args.ask else material
    body = build_body(text, args.thinking)
    url = f"{API_ROOT}/models/{model}:generateContent"

    status, data = call_with_retry(url, key, body)
    if status != 200:
        message = data.get("error", {}).get("message", str(data))[:600]
        if status in (400, 404) and "model" in message.lower():
            names = list_models(key)
            listing = ", ".join(names) if names else "(could not list models)"
            fail(f"model '{model}' rejected ({status}): {message}\nAvailable: {listing}")
        fail(f"HTTP {status}: {message}")

    candidates = data.get("candidates") or []
    if not candidates:
        fail(f"no candidates returned: {json.dumps(data.get('promptFeedback', data))[:600]}")
    cand = candidates[0]
    answer = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    finish = cand.get("finishReason")
    if not answer:
        fail(f"empty answer (finishReason={finish})")

    print(answer)
    if args.out:
        Path(args.out).write_text(answer + "\n", encoding="utf-8")
    usage = data.get("usageMetadata")
    print(
        f"gemini_review: mode=file model={model} thinking={args.thinking} finish={finish} usage={usage}",
        file=sys.stderr,
    )
    if finish not in (None, "STOP"):
        print(f"gemini_review: warning, answer may be cut off ({finish})", file=sys.stderr)


# ---------------------------------------------------------------- setup


def key_fix_hint(platform: str) -> str:
    if platform == "win32":
        return f'{KEY_VAR} is not set: run  setx {KEY_VAR} "<your key>"  then open a new shell.'
    return f"{KEY_VAR} is not set: add  export {KEY_VAR}=<your key>  to your shell profile, then open a new shell."


def find_tool(name: str, root: Path | None = None) -> str | None:
    """Full path of an executable, never one planted in the working tree.

    On Windows, shutil.which (and cmd.exe) look in the current directory before PATH
    unless NoDefaultCurrentDirectoryInExePath is set, so a cloned repo could ship its
    own gemini.cmd or git.exe. Bare "gemini" in argv also fails there: subprocess does
    not resolve the npm .cmd shim, shutil.which does. A result directly in the current
    directory, or anywhere inside the git root, is rejected.
    """
    os.environ["NoDefaultCurrentDirectoryInExePath"] = "1"
    exe = shutil.which(name)
    if not exe:
        return None
    resolved = Path(exe).resolve()
    if resolved.parent == Path.cwd().resolve():
        return None
    if root is not None:
        root = root.resolve()
        if resolved == root or root in resolved.parents:
            return None
    return str(resolved)


def find_gemini(root: Path | None = None) -> str | None:
    return find_tool("gemini", root)


def popen_kwargs() -> dict:
    # A new session on POSIX lets kill_tree take the CLI's relaunched child too.
    return {"start_new_session": True} if sys.platform != "win32" else {}


def kill_tree(proc: subprocess.Popen) -> None:
    """Kill the process and its children.

    Killing the .cmd shim alone leaves node.exe holding the pipes on Windows, and the
    Gemini CLI relaunches itself in a child node process on every platform.
    """
    if sys.platform == "win32":
        taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe"
        try:
            subprocess.run([str(taskkill), "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()


def run_bounded(
    cmd: list[str], timeout: float, env: dict | None = None, cwd: Path | None = None,
    stdin_text: str | None = None,
) -> tuple[int, str, str]:
    """Run a command with a timeout that holds even through a .cmd shim.

    subprocess.run(timeout=...) kills only the direct child and then waits for pipes a
    grandchild still holds. Raises OSError when the command cannot start and
    subprocess.TimeoutExpired after killing the tree.
    """
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
        errors="replace", env=env, cwd=cwd, **popen_kwargs(),
    )
    try:
        stdout, stderr = proc.communicate(input=stdin_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        try:
            proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            pass
        raise
    return proc.returncode, stdout, stderr


def repo_mode_status() -> tuple[bool, str, str | None]:
    """(available, reason when not, CLI version). A capability check, not a version guess."""
    exe = find_gemini()
    if not exe:
        return False, "gemini CLI not found on PATH (npm i -g @google/gemini-cli)", None
    try:
        _, version, _ = run_bounded([exe, "--version"], 60)
        _, helptext, _ = run_bounded([exe, "--help"], 60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"gemini CLI did not run: {exc}", None
    version = version.strip() or None
    missing = [
        need for need, ok in (
            ("--policy", "--policy" in helptext),
            ("--approval-mode plan", "--approval-mode" in helptext and '"plan"' in helptext),
        ) if not ok
    ]
    if missing:
        return False, f"gemini CLI {version} lacks {', '.join(missing)}; upgrade it", version
    return True, "", version


def run_setup(args: argparse.Namespace) -> None:
    ok = True
    py = sys.version_info
    if py >= (3, 10):
        print(f"python: {py.major}.{py.minor}.{py.micro} ok ({sys.executable})")
    else:
        print(f"python: {py.major}.{py.minor} is too old; install Python 3.10 or later")
        ok = False
    key = os.environ.get(KEY_VAR)
    if key:
        print(f"key: {KEY_VAR} set")
    else:
        print(f"key: {key_fix_hint(sys.platform)}", file=sys.stderr)
        ok = False
    if key:
        try:
            model = resolve_model(args.model, key)
            print(f"model: {args.model} -> {model}, thinking {args.thinking}")
        except SystemExit:  # the reason is already on stderr; keep reporting the rest
            print(f"model: {args.model} could not be resolved (see the error above)")
            ok = False
    available, reason, version = repo_mode_status()
    print(f"cli: gemini {version}" if version else "cli: not found (npm i -g @google/gemini-cli)")
    if available:
        source, _ = system_settings_paths(os.environ)
        user_blocker = user_settings_blocker(os.environ)
        if workspace_settings_present(Path.cwd()):
            print(
                "repo mode: unavailable here: repo carries Gemini CLI workspace settings "
                "(.gemini/settings.json); rescue uses file mode"
            )
        elif user_blocker:
            print(f"repo mode: unavailable: {user_blocker}; rescue uses file mode")
        else:
            print("repo mode: available (read-only, thinking: CLI default)")
        if source.is_file():
            print(f"system settings: {source} is kept; repo mode lays its hardening keys over it")
    else:
        print(f"repo mode: unavailable: {reason}; rescue uses file mode")
    if not ok:
        sys.exit(EXIT_FAIL)


# ---------------------------------------------------------------- repo mode


def system_settings_paths(environ: dict, platform: str | None = None) -> tuple[Path, Path]:
    """(system settings, system defaults) the Gemini CLI would read without repo mode."""
    settings = environ.get("GEMINI_CLI_SYSTEM_SETTINGS_PATH") or SYSTEM_SETTINGS_PATHS.get(
        platform or sys.platform, SYSTEM_SETTINGS_DEFAULT
    )
    defaults = environ.get("GEMINI_CLI_SYSTEM_DEFAULTS_PATH") or str(
        Path(settings).parent / "system-defaults.json"
    )
    return Path(settings), Path(defaults)


def load_settings_json(path: Path) -> dict:
    """Parse a Gemini CLI settings file; full-line // comments are allowed there."""
    text = "\n".join(
        line for line in path.read_text(encoding="utf-8-sig").splitlines()
        if not line.lstrip().startswith("//")
    )
    data = json.loads(text) if text.strip() else {}
    if not isinstance(data, dict):
        raise ValueError("top level is not an object")
    return data


def deep_merge(base: dict, over: dict) -> dict:
    """base with over laid on top; over wins on every key it sets."""
    merged = dict(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def gitignore_escape(entry: str) -> str:
    """One path from git's ignored list as an anchored, literal ignore pattern."""
    body = re.sub(r"([*?\[\\])", r"\\\1", entry)
    if body.endswith(" "):
        body = body[:-1] + "\\ "
    return "/" + body


def prepare_settings(
    environ: dict, workdir: Path, root: Path | None = None, ignored: list[str] | None = None,
) -> tuple[Path, str | None]:
    """Settings file repo mode points GEMINI_CLI_SYSTEM_SETTINGS_PATH at, plus a note.

    System scope wins the Gemini CLI settings merge, so the hardening keys (API-key
    auth, gitignore filtering on, hooks off, no GEMINI.md, no directory tree) go there.
    An existing system settings file is kept: its keys are merged under the hardening
    keys, not replaced.

    The CLI's own ignore parser reads only the .gitignore files under its working
    directory and <root>/.git/info/exclude: not the global core.excludesFile, not a
    worktree's or submodule's exclude file, and a .geminiignore with "!" lines can
    re-include files. So git's own ignored list is written to a custom ignore file,
    which the CLI applies last, above all of those.

    Raises ValueError when the existing file cannot be parsed or the ignore file
    cannot be reached by a path relative to the repository root.
    """
    source, _ = system_settings_paths(environ)
    merged = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    note = None
    if source.is_file():
        merged = deep_merge(load_settings_json(source), merged)
        note = f"kept the existing Gemini CLI system settings ({source}) under the repo-mode hardening keys"
    if root is not None and ignored:
        ignore_file = workdir / "gemini-review-ignore"
        ignore_file.write_text("\n".join(gitignore_escape(e) for e in ignored) + "\n", encoding="utf-8")
        try:
            relative = os.path.relpath(ignore_file, root)
        except ValueError as exc:  # temp folder on another drive than the repo
            raise ValueError(f"the temp folder is on another drive than the repository: {exc}") from exc
        merged.setdefault("context", {}).setdefault("fileFiltering", {})["customIgnoreFilePaths"] = [relative]
    target = workdir / "settings.json"
    target.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return target, note


def ignored_entries(root: Path) -> list[str] | None:
    """git's own list of ignored paths under root (directories end with /)."""
    out = run_git(["ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"], root, root)
    if out is None:
        return None
    return [p for p in out.decode("utf-8", errors="replace").split("\0") if p]


def _covered(rel: str, ignored: list[str]) -> bool:
    for entry in ignored:
        bare = entry.rstrip("/")
        if rel == bare or rel.startswith(bare + "/") or bare.startswith(rel + "/"):
            return True
    return False


def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path, "is_junction", lambda: False)())


def links_into_ignored(root: Path, ignored: list[str]) -> list[str]:
    """Links inside the repo whose target is, or holds, an ignored path.

    The CLI checks .gitignore against the link's own path, then reads the target.
    """
    candidates: list[str] = []
    tracked = run_git(["ls-files", "-s", "-z"], root, root) or b""
    for record in tracked.decode("utf-8", errors="replace").split("\0"):
        meta, _, name = record.partition("\t")
        if name and meta.startswith("120000"):
            candidates.append(name)
    untracked = run_git(["ls-files", "--others", "--exclude-standard", "--directory", "-z"], root, root) or b""
    for name in untracked.decode("utf-8", errors="replace").split("\0"):
        if name and _is_link(root / name.rstrip("/")):
            candidates.append(name.rstrip("/"))
    bad = []
    for name in candidates:
        try:
            target = (root / name).resolve().relative_to(root).as_posix()
        except (OSError, ValueError):
            continue  # outside the repo: the CLI's workspace check refuses it
        if _covered(target, ignored):
            bad.append(name)
    return bad


def user_settings_blocker(environ: dict) -> str | None:
    """Reason the user's own Gemini settings make repo mode unsafe, or None.

    context.includeDirectories adds folders the CLI reads without gitignore filtering,
    and it is concatenated across scopes, so system settings cannot clear it.
    """
    home = Path(environ.get("GEMINI_CLI_HOME") or Path.home())
    path = home / ".gemini" / "settings.json"
    if not path.is_file():
        return None
    try:
        data = load_settings_json(path)
    except (OSError, ValueError):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "includeDirectories" in text:
            return f"cannot parse {path} to check context.includeDirectories"
        return None
    if (data.get("context") or {}).get("includeDirectories"):
        return f"{path} sets context.includeDirectories, which the CLI reads without gitignore filtering"
    return None


def neutralize_brief(brief: str) -> str:
    """Stop the CLI's prompt processing from acting on the brief.

    In headless mode an "@path" in the prompt is read with a file tool outside the
    policy engine, and a prompt starting with "/" runs a custom command. A zero-width
    space after "@" and a fixed first line keep both from firing.
    """
    return "Brief:\n\n" + re.sub(r"@(?=\S)", "@​", brief)


def run_git(argv: list[str], cwd: Path, root: Path | None = None) -> bytes | None:
    """stdout of a git command, or None on any failure. git is resolved like gemini."""
    git = find_tool("git", root)
    if not git:
        return None
    try:
        out = subprocess.run([git, *argv], cwd=cwd, capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout if out.returncode == 0 else None


def git_root(start: Path) -> Path | None:
    out = run_git(["rev-parse", "--show-toplevel"], start)
    text = out.decode("utf-8", errors="replace").strip() if out else ""
    return Path(text).resolve() if text else None


def workspace_settings_present(cwd: Path, root: Path | None = None) -> bool:
    """True when .gemini/settings.json exists in cwd or a parent up to the git root.

    Headless Gemini CLI treats every folder as trusted, so such a file would load its
    hooks, MCP servers and tool settings. The home folder is skipped: its
    .gemini/settings.json is the user's own settings file, not a workspace file.
    """
    cwd = cwd.resolve()
    home = Path.home().resolve()
    stop = (root or git_root(cwd) or cwd).resolve()
    for folder in [cwd, *cwd.parents]:
        if folder != home and (folder / ".gemini" / "settings.json").is_file():
            return True
        if folder == stop:
            break
    return False


ENV_KEY_RE = re.compile(r"^\s*(?:export\s+)?([\w.-]+)\s*(?:=|:\s)")


def env_file_keys(cwd: Path, home: Path) -> set[str]:
    """Every variable name defined in a .env file the Gemini CLI might load.

    The CLI loads the first .gemini/.env or .env walking up from cwd, then the home
    ones, and sets each variable that is not already present. This collects names from
    all candidates, a superset, so build_repo_env can pin each one.
    """
    candidates = []
    for folder in [cwd.resolve(), *cwd.resolve().parents]:
        candidates += [folder / ".gemini" / ".env", folder / ".env"]
    candidates += [home / ".gemini" / ".env", home / ".env"]
    keys: set[str] = set()
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        keys.update(m.group(1) for m in map(ENV_KEY_RE.match, text.splitlines()) if m)
    return keys


def build_repo_command(exe: str, model_id: str, resume: str | None) -> list[str]:
    cmd = [
        exe,
        "-p", REPO_PROMPT,
        "-m", model_id,
        "--approval-mode", "plan",
        "-o", "json",
        "--policy", str(POLICY_PATH),
        "-e", "none",
        "--allowed-mcp-server-names", "gemini-review-none",
    ]
    if resume:
        cmd += ["-r", resume]
    return cmd


def build_repo_env(
    environ: dict, key: str | None = None, settings_path: Path = SETTINGS_PATH,
    env_keys: set[str] | frozenset = frozenset(),
) -> dict:
    """Child environment with every .env-supplied variable neutralised.

    The CLI loads the first .env it finds (repo .env, walking upward, then home) and
    sets only variables not already present. A repository could otherwise supply a
    different key (GOOGLE_API_KEY wins over GEMINI_API_KEY), endpoint
    (GOOGLE_GEMINI_BASE_URL), NODE_OPTIONS for the CLI's self-relaunch, GEMINI_CLI_HOME,
    GEMINI_SYSTEM_MD (any local file sent as the system prompt) or proxy settings. So
    every name defined in a candidate .env is present in the child: inherited value
    kept, otherwise empty. The relaunch is switched off as well.
    """
    env = dict(environ)
    for name in env_keys:
        env.setdefault(name, "")
    _, defaults = system_settings_paths(environ)
    env["GEMINI_CLI_NO_RELAUNCH"] = "true"
    env["GEMINI_SANDBOX"] = "false"  # an attacker-chosen container image or proxy command
    env["GEMINI_SYSTEM_MD"] = "false"  # any local file sent as the system prompt
    env["GEMINI_WRITE_SYSTEM_MD"] = "false"  # writes the system prompt to a path
    key = key or env.get(KEY_VAR, "")
    env[KEY_VAR] = key
    env["GOOGLE_API_KEY"] = key
    env["GOOGLE_GEMINI_BASE_URL"] = API_BASE_URL
    env["GOOGLE_GENAI_USE_VERTEXAI"] = "false"
    env["GEMINI_CLI_SYSTEM_SETTINGS_PATH"] = str(settings_path)
    # The CLI derives the defaults path from the settings path; keep pointing at the real one.
    env["GEMINI_CLI_SYSTEM_DEFAULTS_PATH"] = str(defaults)
    env["NoDefaultCurrentDirectoryInExePath"] = "1"
    return env


def parse_repo_output(stdout: str, model_id: str) -> tuple[str, str | None, dict, dict]:
    """(response, session_id, tokens for model_id, {tool: count}) from `-o json` output."""
    start = stdout.find("{")
    if start < 0:
        raise ValueError("no JSON object in Gemini CLI output")
    data, _ = json.JSONDecoder().raw_decode(stdout[start:])
    stats = data.get("stats") or {}
    models = stats.get("models") or {}
    if model_id in models:
        tokens = models[model_id].get("tokens") or {}
    else:
        tokens = {}
        for entry in models.values():
            for name, value in (entry.get("tokens") or {}).items():
                if isinstance(value, (int, float)):
                    tokens[name] = tokens.get(name, 0) + value
    tools = {
        name: entry.get("count", 0)
        for name, entry in ((stats.get("tools") or {}).get("byName") or {}).items()
    }
    return data.get("response") or "", data.get("session_id"), tokens, tools


def tree_fingerprint(root: Path) -> tuple[str, dict[str, str]] | None:
    """Porcelain status plus content hashes of tracked changes and untracked files.

    Porcelain alone prints the same ` M path` whether a dirty file changed again or not.
    Ignored files are not covered.
    """
    def git(*argv: str) -> bytes | None:
        return run_git(list(argv), root, root)

    status = git("status", "--porcelain", "-z", "--untracked-files=all")
    if status is None:
        return None
    hashes = {
        "<tracked diff>": hashlib.sha256(git("diff", "HEAD", "--binary") or b"").hexdigest(),
        "<HEAD>": (git("rev-parse", "HEAD") or b"").decode("ascii", errors="replace").strip(),
    }
    for raw in (git("ls-files", "--others", "--exclude-standard", "-z") or b"").split(b"\0"):
        if raw:
            name = raw.decode("utf-8", errors="replace")
            try:
                hashes[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
            except OSError:
                hashes[name] = "<unreadable>"
    return status.decode("utf-8", errors="replace"), hashes


def status_entries(status: str) -> set[str]:
    """Path entries of `git status --porcelain -z`; a rename's source is its own field."""
    fields = status.split("\0")
    entries: set[str] = set()
    i = 0
    while i < len(fields):
        entry = fields[i]
        i += 1
        if not entry:
            continue
        entries.add(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:
            if i < len(fields) and fields[i]:
                entries.add(fields[i])
            i += 1
    return entries


def changed_paths(before: tuple[str, dict], after: tuple[str, dict]) -> list[str]:
    paths = {p for p in set(before[1]) | set(after[1]) if before[1].get(p) != after[1].get(p)}
    if before[0] != after[0]:
        paths |= (status_entries(before[0]) ^ status_entries(after[0])) or {"<git status changed>"}
    return sorted(paths)


def has_previous_session(exe: str, env: dict, cwd: Path) -> bool:
    """Raises RuntimeError when the CLI cannot list sessions."""
    try:
        code, stdout, stderr = run_bounded([exe, "--list-sessions"], 120, env=env, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(str(exc)) from exc
    if code != 0:
        raise RuntimeError((stderr or stdout).strip()[-400:] or f"exit {code}")
    return "No previous sessions" not in stdout


def run_repo_mode(args: argparse.Namespace, key: str) -> None:
    available, reason, version = repo_mode_status()
    if not available:
        fail(f"repo mode unavailable: {reason}", EXIT_REPO_UNAVAILABLE)
    if not args.brief:
        fail("--brief is required with --repo.")
    brief_path = Path(args.brief)
    if not brief_path.is_file():
        fail(f"brief not found: {brief_path}")
    model = resolve_model(args.model, key)
    if not MODEL_ID_RE.match(model):
        fail(f"model id {model!r} has characters outside [A-Za-z0-9._-]")
    resume = args.resume
    if resume and resume != "latest" and not SESSION_ID_RE.match(resume):
        fail(f"session id {resume!r} has characters outside [A-Za-z0-9-]")

    cwd = Path.cwd().resolve()
    root = git_root(cwd)
    if workspace_settings_present(cwd, root):
        fail(
            "repo mode unavailable: repo carries Gemini CLI workspace settings (.gemini/settings.json), "
            "which headless Gemini CLI would trust and run",
            EXIT_REPO_UNAVAILABLE,
        )
    blocker = user_settings_blocker(os.environ)
    if blocker:
        fail(f"repo mode unavailable: {blocker}", EXIT_REPO_UNAVAILABLE)
    ignored: list[str] | None = None
    if root is not None:
        ignored = ignored_entries(root)
        if ignored is None:
            fail("repo mode unavailable: git could not list the ignored files", EXIT_REPO_UNAVAILABLE)
        links = links_into_ignored(root, ignored)
        if links:
            fail(
                "repo mode unavailable: these links point into gitignored paths, which the CLI "
                "would read through the link: " + ", ".join(links[:10]),
                EXIT_REPO_UNAVAILABLE,
            )
    try:
        brief = neutralize_brief(brief_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read the brief {brief_path} as UTF-8 text: {exc}")
    # The CLI reads .gitignore files only from its working directory down, so it runs
    # from the git root, never from a subfolder.
    workspace = root or cwd
    with tempfile.TemporaryDirectory(prefix="gemini-review-", ignore_cleanup_errors=True) as workdir:
        try:
            settings_path, note = prepare_settings(os.environ, Path(workdir), root, ignored)
        except (OSError, ValueError) as exc:
            fail(
                f"repo mode unavailable: cannot read the existing Gemini CLI system settings: {exc}",
                EXIT_REPO_UNAVAILABLE,
            )
        if note:
            print(f"gemini_review: {note}", file=sys.stderr)
        print(f"model: {args.model} -> {model} (repo mode, thinking: CLI default)", file=sys.stderr)
        env = build_repo_env(os.environ, key, settings_path, env_file_keys(workspace, Path.home()))
        run_cli(args, workspace, root, model, resume, brief, env)


def run_cli(
    args: argparse.Namespace, cwd: Path, root: Path | None, model: str, resume: str | None,
    brief: str, env: dict,
) -> None:
    exe = find_gemini(root)
    if not exe:
        fail("repo mode unavailable: gemini CLI not found outside the working tree", EXIT_REPO_UNAVAILABLE)
    cmd = build_repo_command(exe, model, resume)
    if exe.lower().endswith((".cmd", ".bat")) and any(CMD_METACHARACTERS & set(a) for a in cmd):
        fail(
            "repo mode unavailable: a path in the CLI command holds a cmd.exe metacharacter "
            f"({''.join(sorted(CMD_METACHARACTERS))}), which the gemini.cmd shim would expand",
            EXIT_REPO_UNAVAILABLE,
        )
    if resume == "latest":
        try:
            found = has_previous_session(exe, env, cwd)
        except RuntimeError as exc:
            fail(f"cannot check for a previous Gemini session: {exc}")
        if not found:
            fail("no previous Gemini session in this directory to resume")

    before = tree_fingerprint(root) if root else None
    try:
        code, stdout, stderr = run_bounded(cmd, REPO_TIMEOUT_S, env=env, cwd=cwd, stdin_text=brief)
    except subprocess.TimeoutExpired:
        fail(f"Gemini CLI timed out after {REPO_TIMEOUT_S} s and was stopped")
    except OSError as exc:
        fail(f"Gemini CLI did not start: {exc}")

    if code != 0:
        tail = stderr.strip()[-1200:] or stdout.strip()[-1200:]
        hint = ""
        if re.search(r"auth|api key|IneligibleTier|credential", tail, re.IGNORECASE):
            hint = f"\nhint: check {KEY_VAR} with /gemini:setup; repo mode forces API-key auth."
        fail(f"Gemini CLI exited {code}: {tail}{hint}")
    try:
        response, session, tokens, tools = parse_repo_output(stdout, model)
    except ValueError as exc:
        fail(f"{exc}: {stdout.strip()[:600]}")
    if not response.strip():
        fail(f"Gemini CLI returned no answer: {stdout.strip()[:600]}")

    print(response)
    if args.out:
        Path(args.out).write_text(response + "\n", encoding="utf-8")
    print(
        f"gemini_review: mode=repo model={model} session={session} tokens={tokens} tools={tools}",
        file=sys.stderr,
    )
    if before is not None:
        after = tree_fingerprint(root)
        if after is not None and after != before:
            paths = changed_paths(before, after)
            fail(
                "WARNING: the working tree changed during this read-only run: " + ", ".join(paths),
                EXIT_TREE_CHANGED,
            )


# ---------------------------------------------------------------- entry point


def main(argv: list[str] | None = None) -> None:
    force_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--file", help="file mode: self-contained material to review")
    parser.add_argument("--ask", default="", help="file mode: the one focused question (optional)")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"exact id or alias word, default {DEFAULT_MODEL}"
    )
    parser.add_argument(
        "--thinking", choices=("low", "high"), default=DEFAULT_THINKING,
        help=f"file mode thinking level, default {DEFAULT_THINKING} (repo mode uses the CLI default)",
    )
    parser.add_argument("--out", help="also save the answer to this path")
    parser.add_argument("--setup", action="store_true", help="print a readiness report")
    parser.add_argument("--repo", action="store_true", help="repo mode: Gemini CLI reads this repo")
    parser.add_argument("--brief", help="repo mode: the brief file (sent on stdin)")
    parser.add_argument(
        "--resume", nargs="?", const="latest", default=None,
        help="repo mode: continue a session (the session id printed by the last run, or latest)",
    )
    parser.add_argument("--list", action="store_true", help="list generateContent model ids and exit")
    parser.add_argument("--resolve-only", action="store_true", help="print the resolved model id and exit")
    args = parser.parse_args(argv)

    if args.setup:
        run_setup(args)
        return
    key = os.environ.get(KEY_VAR)
    if not key:
        fail(key_fix_hint(sys.platform))
    if args.list:
        print("\n".join(list_models(key)))
        return
    if args.repo:
        run_repo_mode(args, key)
        return
    run_file_mode(args, key)


if __name__ == "__main__":
    main()
