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

Exit codes: 0 ok; 1 failure; 2 unknown model alias; 3 repo mode unavailable
(the caller falls back to file mode); 4 the working tree changed during a repo-mode run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
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

EXIT_FAIL = 1
EXIT_UNKNOWN_ALIAS = 2
EXIT_REPO_UNAVAILABLE = 3
EXIT_TREE_CHANGED = 4

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


def call(url: str, key: str, body: dict | None) -> tuple[int, dict]:
    """One HTTP call. Returns (status, parsed JSON). Network errors return status 0."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if body is not None else "GET",
        headers={"x-goog-api-key": key, "content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"error": {"message": raw[:600]}}
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, {"error": {"message": f"network error: {exc}"}}


def list_models(key: str) -> list[str]:
    """All generateContent model ids (without the models/ prefix), sorted."""
    ids: set[str] = set()
    token = ""
    while True:
        url = f"{API_ROOT}/models?pageSize=1000" + (f"&pageToken={token}" if token else "")
        status, data = call(url, key, None)
        if status != 200:
            break
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

    material = path.read_text(encoding="utf-8")
    text = f"{material}\n\n## Focused ask\n\n{args.ask}" if args.ask else material
    body = build_body(text, args.thinking)
    url = f"{API_ROOT}/models/{model}:generateContent"

    status, data = call(url, key, body)
    if status == 0 or status in TRANSIENT:
        print(f"gemini_review: transient failure ({status}), retrying once in 5 s", file=sys.stderr)
        time.sleep(5)
        status, data = call(url, key, body)

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


def find_gemini(cwd: Path | None = None) -> str | None:
    """Full path of the Gemini CLI, never one planted in the working tree.

    On Windows, shutil.which (and cmd.exe) look in the current directory before PATH
    unless NoDefaultCurrentDirectoryInExePath is set, so a cloned repo could ship its
    own gemini.cmd. Bare "gemini" in argv also fails there: subprocess does not resolve
    the npm .cmd shim, shutil.which does.
    """
    os.environ["NoDefaultCurrentDirectoryInExePath"] = "1"
    exe = shutil.which("gemini")
    if not exe:
        return None
    resolved = Path(exe).resolve()
    tree = (cwd or Path.cwd()).resolve()
    if resolved == tree or tree in resolved.parents:
        return None
    return str(resolved)


def repo_mode_status() -> tuple[bool, str, str | None]:
    """(available, reason when not, CLI version). A capability check, not a version guess."""
    exe = find_gemini()
    if not exe:
        return False, "gemini CLI not found on PATH (npm i -g @google/gemini-cli)", None
    try:
        version = subprocess.run(
            [exe, "--version"], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60, stdin=subprocess.DEVNULL,
        ).stdout.strip() or None
        helptext = subprocess.run(
            [exe, "--help"], capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60, stdin=subprocess.DEVNULL,
        ).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"gemini CLI did not run: {exc}", None
    missing = [flag for flag in ("--policy", "plan") if flag not in helptext]
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
        model = resolve_model(args.model, key)
        print(f"model: {args.model} -> {model}, thinking {args.thinking}")
    available, reason, version = repo_mode_status()
    print(f"cli: gemini {version}" if version else "cli: not found (npm i -g @google/gemini-cli)")
    if available:
        source, _ = system_settings_paths(os.environ)
        if workspace_settings_present(Path.cwd()):
            print(
                "repo mode: unavailable here: repo carries Gemini CLI workspace settings "
                "(.gemini/settings.json); rescue uses file mode"
            )
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


def prepare_settings(environ: dict, workdir: Path) -> tuple[Path, str | None]:
    """Settings file repo mode points GEMINI_CLI_SYSTEM_SETTINGS_PATH at, plus a note.

    System scope wins the Gemini CLI settings merge, so the hardening keys (API-key
    auth, gitignore filtering on, hooks off, no GEMINI.md) go there. An existing system
    settings file is kept: its keys are merged under the hardening keys, not replaced.
    Raises ValueError when that file cannot be parsed.
    """
    source, _ = system_settings_paths(environ)
    if not source.is_file():
        return SETTINGS_PATH, None
    hardening = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    merged = deep_merge(load_settings_json(source), hardening)
    target = workdir / "settings.json"
    target.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return target, f"kept the existing Gemini CLI system settings ({source}) under the repo-mode hardening keys"


def git_root(start: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=start, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return Path(out.stdout.strip()).resolve() if out.returncode == 0 and out.stdout.strip() else None


def workspace_settings_present(cwd: Path, root: Path | None = None) -> bool:
    """True when .gemini/settings.json exists in cwd or a parent up to the git root.

    Headless Gemini CLI treats every folder as trusted, so such a file would load its
    hooks, MCP servers and tool settings.
    """
    cwd = cwd.resolve()
    stop = (root or git_root(cwd) or cwd).resolve()
    for folder in [cwd, *cwd.parents]:
        if (folder / ".gemini" / "settings.json").is_file():
            return True
        if folder == stop:
            break
    return False


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


def build_repo_env(environ: dict, key: str | None = None, settings_path: Path = SETTINGS_PATH) -> dict:
    """Child environment with the key, endpoint and settings pinned.

    The CLI loads the first .env it finds (repo .env, walking upward, then home) and
    sets only variables not already present, so anything left unset could be supplied
    by the repository: a different key (GOOGLE_API_KEY wins over GEMINI_API_KEY) or a
    different endpoint (GOOGLE_GEMINI_BASE_URL).
    """
    env = dict(environ)
    _, defaults = system_settings_paths(environ)
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
        try:
            out = subprocess.run(["git", *argv], cwd=root, capture_output=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return out.stdout if out.returncode == 0 else None

    status = git("status", "--porcelain", "-z", "--untracked-files=all")
    if status is None:
        return None
    hashes = {"<tracked diff>": hashlib.sha256(git("diff", "HEAD", "--binary") or b"").hexdigest()}
    for raw in (git("ls-files", "--others", "--exclude-standard", "-z") or b"").split(b"\0"):
        if raw:
            name = raw.decode("utf-8", errors="replace")
            try:
                hashes[name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
            except OSError:
                hashes[name] = "<unreadable>"
    return status.decode("utf-8", errors="replace"), hashes


def changed_paths(before: tuple[str, dict], after: tuple[str, dict]) -> list[str]:
    paths = {p for p in set(before[1]) | set(after[1]) if before[1].get(p) != after[1].get(p)}
    if before[0] != after[0]:
        entries = {e[3:] for e in before[0].split("\0") if e} ^ {e[3:] for e in after[0].split("\0") if e}
        paths |= entries or {"<git status changed>"}
    return sorted(paths)


def kill_tree(proc: subprocess.Popen) -> None:
    """Killing the .cmd shim alone leaves node.exe holding the pipes on Windows."""
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def has_previous_session(exe: str, env: dict) -> bool:
    out = subprocess.run(
        [exe, "--list-sessions"], capture_output=True, text=True, encoding="utf-8",
        errors="replace", env=env, timeout=120, stdin=subprocess.DEVNULL,
    )
    return out.returncode == 0 and "No previous sessions" not in out.stdout


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
    with tempfile.TemporaryDirectory(prefix="gemini-review-") as workdir:
        try:
            settings_path, note = prepare_settings(os.environ, Path(workdir))
        except (OSError, ValueError) as exc:
            fail(
                f"repo mode unavailable: cannot read the existing Gemini CLI system settings: {exc}",
                EXIT_REPO_UNAVAILABLE,
            )
        if note:
            print(f"gemini_review: {note}", file=sys.stderr)
        print(f"model: {args.model} -> {model} (repo mode, thinking: CLI default)", file=sys.stderr)
        run_cli(args, cwd, root, model, resume, brief_path, build_repo_env(os.environ, key, settings_path))


def run_cli(
    args: argparse.Namespace, cwd: Path, root: Path | None, model: str, resume: str | None,
    brief_path: Path, env: dict,
) -> None:
    exe = find_gemini(cwd)
    if not exe:
        fail("repo mode unavailable: gemini CLI not found", EXIT_REPO_UNAVAILABLE)
    if resume == "latest" and not has_previous_session(exe, env):
        fail("no previous Gemini session in this directory to resume")

    before = tree_fingerprint(root) if root else None
    cmd = build_repo_command(exe, model, resume)
    brief = brief_path.read_text(encoding="utf-8")
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", env=env, cwd=cwd,
    )
    try:
        stdout, stderr = proc.communicate(input=brief, timeout=REPO_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        proc.communicate()
        fail(f"Gemini CLI timed out after {REPO_TIMEOUT_S} s")

    if proc.returncode != 0:
        tail = stderr.strip()[-1200:] or stdout.strip()[-1200:]
        hint = ""
        if re.search(r"auth|api key|IneligibleTier|credential", tail, re.IGNORECASE):
            hint = f"\nhint: check {KEY_VAR} with /gemini:setup; repo mode forces API-key auth."
        fail(f"Gemini CLI exited {proc.returncode}: {tail}{hint}")
    try:
        response, session, tokens, tools = parse_repo_output(stdout, model)
    except ValueError as exc:
        fail(f"{exc}: {stdout.strip()[:600]}")

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
