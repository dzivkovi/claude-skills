import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gemini_review.py"
spec = importlib.util.spec_from_file_location("gr", SCRIPT)
gr = importlib.util.module_from_spec(spec)
sys.modules["gr"] = gr
spec.loader.exec_module(gr)


@pytest.fixture(autouse=True)
def _undo_find_tool_env(monkeypatch):
    # find_tool writes this variable into os.environ; start clean so monkeypatch undoes it.
    monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)


def pair(cmd, a, b):
    return any(cmd[i] == a and cmd[i + 1] == b for i in range(len(cmd) - 1))


def _ok_response():
    return (
        200,
        {
            "candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}],
            "usageMetadata": {},
        },
    )


def _setup_ready(monkeypatch, version="0.35.2"):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-4-carbon"])
    monkeypatch.setattr(gr, "repo_mode_status", lambda: (True, "", version))
    missing = Path(__file__).parent / "no-such-dir"
    monkeypatch.setattr(
        gr, "system_settings_paths",
        lambda *a, **k: (missing / "settings.json", missing / "system-defaults.json"),
    )
    monkeypatch.setattr(gr, "workspace_settings_present", lambda *a, **k: False)
    monkeypatch.setattr(gr, "user_settings_blocker", lambda *a, **k: None)
    monkeypatch.delenv("GEMINI_CLI_SYSTEM_SETTINGS_PATH", raising=False)


# ---- T1-T5: seed pick_model tests


def test_t01_carbon_picks_highest_version_and_skips_preview():
    ids = ["gemini-3-carbon", "gemini-4-carbon", "gemini-4-carbon-preview"]
    assert gr.pick_model("carbon", ids) == "gemini-4-carbon"


def test_t02_flash_prefers_latest_alias():
    ids = ["gemini-3.8-flash", "gemini-flash-latest"]
    assert gr.pick_model("flash", ids) == "gemini-flash-latest"


def test_t03_flash_picks_highest_version_and_skips_excluded_tokens():
    ids = [
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.8-flash-lite",
        "gemini-3.8-flash-preview-tts",
    ]
    assert gr.pick_model("flash", ids) == "gemini-3.8-flash"


def test_t04_unknown_alias_returns_none():
    assert gr.pick_model("nothing", ["gemini-3.8-flash"]) is None


def test_t05_lite_alias_may_match_lite_ids():
    ids = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
    assert gr.pick_model("lite", ids) == "gemini-3.8-flash-lite"


# ---- T6-T9


def test_t06_unknown_alias_exits_5(monkeypatch, capsys):
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-3.8-flash"])
    with pytest.raises(SystemExit) as e:
        gr.resolve_model("nothing", "k")
    assert e.value.code == 5
    assert "no generateContent model matches alias 'nothing'" in capsys.readouterr().err


def test_t07_rejected_model_lists_available(monkeypatch, tmp_path, capsys):
    f = tmp_path / "f.md"
    f.write_text("material", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(
        gr, "call", lambda *a, **k: (404, {"error": {"message": "models/gemini-x is not found"}})
    )
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-4-carbon"])
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(f), "--model", "gemini-x"])
    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "rejected (404)" in err
    assert "gemini-4-carbon" in err


def test_t08a_build_body_thinking_level():
    assert gr.build_body("x", "high")["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "high"
    assert gr.build_body("x", "low")["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"


def test_t08b_main_passes_thinking_level(monkeypatch, tmp_path, capsys):
    f = tmp_path / "f.md"
    f.write_text("material", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    bodies = []

    def fake_call(url, key, body):
        bodies.append(body)
        return _ok_response()

    monkeypatch.setattr(gr, "call", fake_call)
    gr.main(["--file", str(f), "--model", "gemini-4-carbon", "--thinking", "low"])
    assert bodies[-1]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"
    gr.main(["--file", str(f), "--model", "gemini-4-carbon"])
    assert bodies[-1]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "high"
    captured = capsys.readouterr()
    assert "ok" in captured.out
    assert "test-key-123" not in captured.err


def test_t09_key_fix_hint():
    win = gr.key_fix_hint("win32")
    assert "setx GEMINI_API_KEY" in win
    assert "new shell" in win
    assert "export GEMINI_API_KEY=" in gr.key_fix_hint("linux")
    assert "export GEMINI_API_KEY=" in gr.key_fix_hint("darwin")


# ---- T10-T12: setup


def test_t10_setup_without_key(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(gr, "repo_mode_status", lambda: (False, "x", None))
    with pytest.raises(SystemExit) as e:
        gr.main(["--setup"])
    assert e.value.code == 1
    out = capsys.readouterr()
    assert "GEMINI_API_KEY is not set" in out.err


def test_t11_setup_ready(monkeypatch, capsys):
    _setup_ready(monkeypatch)
    gr.main(["--setup"])
    out = capsys.readouterr()
    assert "carbon -> gemini-4-carbon, thinking high" in out.out
    assert "cli: gemini 0.35.2" in out.out
    assert "repo mode: available" in out.out
    assert "test-key-123" not in out.out
    assert "test-key-123" not in out.err


def test_t12_setup_repo_unavailable(monkeypatch, capsys):
    _setup_ready(monkeypatch)
    monkeypatch.setattr(gr, "repo_mode_status", lambda: (False, "gemini CLI not found on PATH", None))
    gr.main(["--setup"])
    out = capsys.readouterr().out
    assert "repo mode: unavailable" in out
    assert "file mode" in out


# ---- T13-T16: repo command, env, blockers


def test_t13_repo_command_flags():
    cmd = gr.build_repo_command("gemini", "gemini-4-carbon", None)
    assert pair(cmd, "--approval-mode", "plan")
    assert pair(cmd, "-o", "json")
    assert pair(cmd, "-m", "gemini-4-carbon")
    policy = cmd[cmd.index("--policy") + 1]
    assert Path(policy).exists()
    assert policy.endswith("repo-mode-policy.toml")
    assert "-r" not in cmd


def test_t14_repo_command_resume_latest():
    cmd = gr.build_repo_command("gemini", "gemini-4-carbon", "latest")
    assert pair(cmd, "-r", "latest")


def test_t15_repo_env_pins_settings(tmp_path):
    env = gr.build_repo_env({"GEMINI_API_KEY": "b"})
    path = env["GEMINI_CLI_SYSTEM_SETTINGS_PATH"]
    assert path.endswith("repo-mode-settings.json")
    assert Path(path).exists()
    assert env["GEMINI_API_KEY"] == "b"
    # The CLI derives the defaults path from the settings path; it must keep the real one.
    assert env["GEMINI_CLI_SYSTEM_DEFAULTS_PATH"].endswith("system-defaults.json")
    assert Path(env["GEMINI_CLI_SYSTEM_DEFAULTS_PATH"]).parent != gr.HERE
    merged = tmp_path / "settings.json"
    env = gr.build_repo_env({"GEMINI_API_KEY": "b"}, settings_path=merged)
    assert env["GEMINI_CLI_SYSTEM_SETTINGS_PATH"] == str(merged)


def test_t16_prepare_settings_keeps_existing_system_settings(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    path, note = gr.prepare_settings({"GEMINI_CLI_SYSTEM_SETTINGS_PATH": str(tmp_path / "none.json")}, work)
    assert path.parent == work and note is None
    assert json.loads(path.read_text(encoding="utf-8")) == json.loads(
        gr.SETTINGS_PATH.read_text(encoding="utf-8")
    )

    source = tmp_path / "system.json"
    source.write_text(
        '// admin file\n{"general": {"previewFeatures": true},'
        ' "security": {"auth": {"selectedType": "oauth-personal"}}}',
        encoding="utf-8",
    )
    path, note = gr.prepare_settings({"GEMINI_CLI_SYSTEM_SETTINGS_PATH": str(source)}, work)
    merged = json.loads(path.read_text(encoding="utf-8"))
    assert path.parent == work
    assert str(source) in note
    assert merged["general"]["previewFeatures"] is True
    assert merged["security"]["auth"]["selectedType"] == "gemini-api-key"
    assert merged["hooksConfig"]["enabled"] is False
    assert merged["context"]["fileFiltering"]["respectGitIgnore"] is True

    source.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError):
        gr.prepare_settings({"GEMINI_CLI_SYSTEM_SETTINGS_PATH": str(source)}, work)

    work2 = tmp_path / "work2"
    work2.mkdir()
    path, _ = gr.prepare_settings(
        {"GEMINI_CLI_SYSTEM_SETTINGS_PATH": str(tmp_path / "none.json")},
        work2, root=tmp_path, ignored=["secrets/", "notes.canary", "a b ", "x*[y"],
    )
    merged = json.loads(path.read_text(encoding="utf-8"))
    listed = merged["context"]["fileFiltering"]["customIgnoreFilePaths"]
    assert isinstance(listed, list) and len(listed) == 1
    ignore_file = Path(os.path.join(tmp_path, listed[0])).resolve()
    assert ignore_file.exists()
    assert ignore_file.read_text(encoding="utf-8").splitlines() == [
        "/secrets/", "/notes.canary", "/a b\\ ", "/x\\*\\[y",
    ]


# ---- T17: parse


def test_t17_parse_repo_output():
    stdout = "Warning: something\n" + json.dumps(
        {
            "session_id": "s1",
            "response": "ok",
            "stats": {
                "models": {"gemini-4-carbon": {"tokens": {"input": 10, "total": 12}}},
                "tools": {"byName": {"read_file": {"count": 2}}},
            },
        }
    )
    assert gr.parse_repo_output(stdout, "gemini-4-carbon") == (
        "ok",
        "s1",
        {"input": 10, "total": 12},
        {"read_file": 2},
    )
    with pytest.raises(ValueError):
        gr.parse_repo_output("no json here", "m")


# ---- T18-T19: repo mode gates


def test_t18_bad_model_id_blocks_before_subprocess(monkeypatch, tmp_path, capsys):
    f = tmp_path / "brief.md"
    f.write_text("brief", encoding="utf-8")
    _setup_ready(monkeypatch)
    monkeypatch.setattr(gr, "user_settings_blocker", lambda *a, **k: None)
    monkeypatch.setattr(gr, "git_root", lambda *a, **k: None)

    def no_popen(*a, **k):
        raise AssertionError("subprocess started")

    monkeypatch.setattr(gr.subprocess, "Popen", no_popen)
    with pytest.raises(SystemExit) as e:
        gr.main(["--repo", "--brief", str(f), "--model", "gemini-bad id;rm"])
    assert e.value.code == 1
    assert "gemini-bad id;rm" in capsys.readouterr().err


def test_t19_repo_unavailable_exits_3(monkeypatch, tmp_path):
    f = tmp_path / "brief.md"
    f.write_text("brief", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "repo_mode_status", lambda: (False, "gemini CLI not found on PATH", None))
    monkeypatch.setattr(gr, "user_settings_blocker", lambda *a, **k: None)
    monkeypatch.setattr(gr, "git_root", lambda *a, **k: None)
    with pytest.raises(SystemExit) as e:
        gr.main(["--repo", "--brief", str(f)])
    assert e.value.code == 3


# ---- T20: bundled policy and settings


def test_t20_policy_and_settings_files():
    tomllib = pytest.importorskip("tomllib")
    folder = SCRIPT.parent
    with open(folder / "repo-mode-policy.toml", "rb") as fh:
        data = tomllib.load(fh)
    rules = data["rule"]

    def names(rule):
        tool = rule.get("toolName")
        return [tool] if isinstance(tool, str) else list(tool or [])

    catch_all = [
        r for r in rules
        if r.get("decision") == "deny" and "toolName" not in r and "argsPattern" not in r
    ]
    assert len(catch_all) == 1

    allow_rules = [r for r in rules if r.get("decision") == "allow"]
    assert allow_rules
    allowed = set()
    for r in allow_rules:
        assert "toolName" in r
        allowed |= set(names(r))
    assert allowed == {"read_file", "list_directory", "glob"}
    assert "grep_search" not in allowed

    assert all(r["priority"] > 300 for r in rules)
    deny_patterns = [r["argsPattern"] for r in rules if r.get("decision") == "deny" and "argsPattern" in r]
    assert any("respect_git_ignore" in p for p in deny_patterns)
    assert any("respect_gemini_ignore" in p for p in deny_patterns)

    settings = json.loads((folder / "repo-mode-settings.json").read_text(encoding="utf-8"))
    assert settings["security"]["auth"]["selectedType"] == "gemini-api-key"
    assert settings["context"]["fileFiltering"]["respectGitIgnore"] is True
    assert settings["hooksConfig"]["enabled"] is False
    assert settings["context"]["fileName"] == "GEMINI_REVIEW_PLUGIN_NONE.md"
    assert settings["context"]["includeDirectoryTree"] is False
    assert any(
        r.get("decision") == "deny" and "read_file" in names(r) and "[a-z]:" in r.get("argsPattern", "")
        for r in rules
    )
    assert any(
        r.get("decision") == "deny" and "read_file" in names(r) and "tmp" in r.get("argsPattern", "")
        for r in rules
    )


# ---- T21-T27


def test_t21_cli_not_found(monkeypatch):
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: None)
    available, reason, version = gr.repo_mode_status()
    assert available is False
    assert "not found" in reason
    assert version is None


def test_t22_repo_command_hardening():
    cmd = gr.build_repo_command("gemini", "gemini-4-carbon", None)
    assert cmd.count("--policy") == 1
    assert pair(cmd, "-e", "none")
    assert pair(cmd, "--allowed-mcp-server-names", "gemini-review-none")
    assert not (set('%"^&|<>') & set(gr.REPO_PROMPT))


def test_t23_repo_command_resume_session_id():
    cmd = gr.build_repo_command("gemini", "gemini-4-carbon", "abc-123")
    assert pair(cmd, "-r", "abc-123")


def test_t24_repo_env_pins_key_and_endpoint():
    env = gr.build_repo_env({"GEMINI_API_KEY": "b", "GOOGLE_API_KEY": "a"})
    assert env["GOOGLE_API_KEY"] == "b"
    assert env["GOOGLE_GEMINI_BASE_URL"] == "https://generativelanguage.googleapis.com"
    assert env["GOOGLE_GENAI_USE_VERTEXAI"] == "false"


def test_t25_workspace_settings_present(tmp_path, tmp_path_factory):
    (tmp_path / ".gemini").mkdir()
    (tmp_path / ".gemini" / "settings.json").write_text("{}", encoding="utf-8")
    assert gr.workspace_settings_present(tmp_path, tmp_path) is True
    sub = tmp_path / "sub"
    sub.mkdir()
    assert gr.workspace_settings_present(sub, tmp_path) is True
    fresh = tmp_path_factory.mktemp("fresh")
    assert gr.workspace_settings_present(fresh, fresh) is False


def test_t26_unreadable_system_settings_block_repo_mode(monkeypatch, tmp_path, capsys):
    f = tmp_path / "brief.md"
    f.write_text("brief", encoding="utf-8")
    bad = tmp_path / "system.json"
    bad.write_text("{bad", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setenv("GEMINI_CLI_SYSTEM_SETTINGS_PATH", str(bad))
    monkeypatch.setattr(gr, "repo_mode_status", lambda: (True, "", "0.35.2"))
    monkeypatch.setattr(gr, "git_root", lambda *a, **k: None)
    monkeypatch.setattr(gr, "workspace_settings_present", lambda *a, **k: False)
    monkeypatch.setattr(gr, "user_settings_blocker", lambda *a, **k: None)
    with pytest.raises(SystemExit) as e:
        gr.main(["--repo", "--brief", str(f), "--model", "gemini-4-carbon"])
    assert e.value.code == 3
    assert "system settings" in capsys.readouterr().err


def test_t28_workspace_settings_block_repo_mode(monkeypatch, tmp_path, capsys):
    f = tmp_path / "brief.md"
    f.write_text("brief", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "repo_mode_status", lambda: (True, "", "0.35.2"))
    monkeypatch.setattr(gr, "git_root", lambda *a, **k: None)
    monkeypatch.setattr(gr, "workspace_settings_present", lambda *a, **k: True)
    monkeypatch.setattr(gr, "user_settings_blocker", lambda *a, **k: None)
    with pytest.raises(SystemExit) as e:
        gr.main(["--repo", "--brief", str(f), "--model", "gemini-4-carbon"])
    assert e.value.code == 3
    assert "workspace settings" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform != "win32", reason="Windows cwd lookup")
def test_t27_find_gemini_ignores_planted_cmd(monkeypatch, tmp_path):
    (tmp_path / "gemini.cmd").write_text("@echo off\r\necho planted\r\n", encoding="utf-8")
    monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    assert gr.find_gemini(tmp_path) is None
    assert os.environ["NoDefaultCurrentDirectoryInExePath"] == "1"


# ---- T29-T49


def _git(root, *argv):
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *argv],
        cwd=root, check=True, capture_output=True,
    )


needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def test_t29_find_tool_rejects_paths_inside_the_tree(monkeypatch, tmp_path):
    inside = tmp_path / "repo" / "bin" / "gemini"
    inside.parent.mkdir(parents=True)
    inside.write_text("x", encoding="utf-8")
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: str(inside))
    monkeypatch.chdir(tmp_path)
    assert gr.find_tool("gemini", tmp_path / "repo") is None
    outside = tmp_path / "outside" / "gemini"
    outside.parent.mkdir()
    outside.write_text("x", encoding="utf-8")
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: str(outside))
    assert gr.find_tool("gemini", tmp_path / "repo") == str(outside.resolve())


def test_t30_find_tool_rejects_result_in_cwd(monkeypatch, tmp_path):
    (tmp_path / "gemini").write_text("x", encoding="utf-8")
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: str(tmp_path / "gemini"))
    monkeypatch.chdir(tmp_path)
    assert gr.find_tool("gemini", None) is None


def test_t31_changed_paths_and_status_entries():
    same = (" M a.txt\0", {"<tracked diff>": "h1", "<HEAD>": "c1"})
    assert gr.changed_paths(same, (same[0], dict(same[1]))) == []
    after = (" M a.txt\0", {"<tracked diff>": "h2", "<HEAD>": "c1"})
    assert gr.changed_paths(same, after) == ["<tracked diff>"]
    new = (" M a.txt\0?? new.txt\0", {"<tracked diff>": "h1", "<HEAD>": "c1", "new.txt": "x"})
    assert "new.txt" in gr.changed_paths(same, new)
    assert gr.status_entries("R  new.py\0old.py\0 M z.txt\0") == {"new.py", "old.py", "z.txt"}


@needs_git
def test_t32_tree_fingerprint_sees_repeat_edits_and_commits(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-q", "-m", "init")
    (root / "a.txt").write_text("two\n", encoding="utf-8")
    fp1 = gr.tree_fingerprint(root)
    (root / "a.txt").write_text("three, different\n", encoding="utf-8")
    fp2 = gr.tree_fingerprint(root)
    assert fp1 != fp2
    assert fp1[0] == fp2[0]
    _git(root, "commit", "-q", "-a", "-m", "second")
    fp3 = gr.tree_fingerprint(root)
    assert fp3[1]["<HEAD>"] != fp2[1]["<HEAD>"]


def _cli_fakes(monkeypatch, outcome, fingerprints=None):
    """Patch run_cli's collaborators; returns the list that records run_bounded calls."""
    calls = []
    monkeypatch.setattr(gr, "find_gemini", lambda *a, **k: "C:/fake/gemini.exe")
    seq = iter(fingerprints or [("s", {"h": "1"})] * 2)
    monkeypatch.setattr(gr, "tree_fingerprint", lambda root: next(seq))

    def fake(cmd, timeout, env=None, cwd=None, stdin_text=None):
        calls.append({"cmd": cmd, "timeout": timeout, "env": env, "cwd": cwd, "stdin_text": stdin_text})
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    monkeypatch.setattr(gr, "run_bounded", fake)
    return calls


def _good_outcome():
    return (
        0,
        json.dumps(
            {
                "session_id": "s9",
                "response": "the answer",
                "stats": {
                    "models": {"gemini-4-carbon": {"tokens": {"total": 5}}},
                    "tools": {"byName": {"read_file": {"count": 1}}},
                },
            }
        ),
        "",
    )


def test_t33_run_cli_happy_path(monkeypatch, tmp_path, capsys):
    calls = _cli_fakes(monkeypatch, _good_outcome())
    args = argparse.Namespace(out=str(tmp_path / "o.md"))
    gr.run_cli(args, tmp_path, tmp_path, "gemini-4-carbon", None, "BRIEF TEXT", {"GOOGLE_API_KEY": "k"})
    captured = capsys.readouterr()
    assert "the answer" in captured.out
    assert "the answer" in (tmp_path / "o.md").read_text(encoding="utf-8")
    assert "session=s9" in captured.err
    assert calls[0]["stdin_text"] == "BRIEF TEXT"
    assert not any("BRIEF TEXT" in part for part in calls[0]["cmd"])
    assert calls[0]["cwd"] == tmp_path
    assert calls[0]["timeout"] == gr.REPO_TIMEOUT_S


def test_t34_run_cli_tree_changed_exits_4(monkeypatch, tmp_path, capsys):
    _cli_fakes(monkeypatch, _good_outcome(), [("s", {"h": "1"}), ("s", {"h": "2"})])
    args = argparse.Namespace(out=None)
    with pytest.raises(SystemExit) as e:
        gr.run_cli(args, tmp_path, tmp_path, "gemini-4-carbon", None, "b", {})
    assert e.value.code == 4
    captured = capsys.readouterr()
    assert "the answer" in captured.out
    assert "working tree changed" in captured.err
    assert "h" in captured.err


def test_t35_run_cli_auth_hint(monkeypatch, tmp_path, capsys):
    _cli_fakes(monkeypatch, (1, "", "Error: API key not valid"))
    with pytest.raises(SystemExit) as e:
        gr.run_cli(argparse.Namespace(out=None), tmp_path, tmp_path, "gemini-4-carbon", None, "b", {})
    assert e.value.code == 1
    assert "/gemini:setup" in capsys.readouterr().err


def test_t36_run_cli_timeout(monkeypatch, tmp_path, capsys):
    _cli_fakes(monkeypatch, subprocess.TimeoutExpired(cmd="x", timeout=1))
    with pytest.raises(SystemExit) as e:
        gr.run_cli(argparse.Namespace(out=None), tmp_path, tmp_path, "gemini-4-carbon", None, "b", {})
    assert e.value.code == 1
    assert "timed out" in capsys.readouterr().err


def test_t37_run_cli_empty_answer(monkeypatch, tmp_path, capsys):
    _cli_fakes(monkeypatch, (0, json.dumps({"session_id": "s", "response": ""}), ""))
    with pytest.raises(SystemExit) as e:
        gr.run_cli(argparse.Namespace(out=None), tmp_path, tmp_path, "gemini-4-carbon", None, "b", {})
    assert e.value.code == 1
    assert "no answer" in capsys.readouterr().err


def test_t38_run_cli_resume_latest_without_sessions(monkeypatch, tmp_path, capsys):
    _cli_fakes(monkeypatch, AssertionError("run_bounded must not be called"))
    args = argparse.Namespace(out=None)
    monkeypatch.setattr(gr, "has_previous_session", lambda *a, **k: False)
    with pytest.raises(SystemExit) as e:
        gr.run_cli(args, tmp_path, tmp_path, "gemini-4-carbon", "latest", "b", {})
    assert e.value.code == 1
    assert "no previous Gemini session" in capsys.readouterr().err

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(gr, "has_previous_session", boom)
    with pytest.raises(SystemExit) as e:
        gr.run_cli(args, tmp_path, tmp_path, "gemini-4-carbon", "latest", "b", {})
    assert e.value.code == 1
    assert "boom" in capsys.readouterr().err


def test_t39_run_cli_cmd_metacharacter_guard(monkeypatch, tmp_path):
    _cli_fakes(monkeypatch, AssertionError("run_bounded must not be called"))
    monkeypatch.setattr(gr, "find_gemini", lambda *a, **k: "C:/fa&ke/gemini.cmd")
    with pytest.raises(SystemExit) as e:
        gr.run_cli(argparse.Namespace(out=None), tmp_path, tmp_path, "gemini-4-carbon", None, "b", {})
    assert e.value.code == 3


def test_t40_has_previous_session(monkeypatch, tmp_path):
    monkeypatch.setattr(
        gr, "run_bounded", lambda *a, **k: (0, "No previous sessions found for this project.", "")
    )
    assert gr.has_previous_session("gemini", {}, tmp_path) is False
    monkeypatch.setattr(gr, "run_bounded", lambda *a, **k: (0, "Available sessions ... [abc]", ""))
    assert gr.has_previous_session("gemini", {}, tmp_path) is True
    monkeypatch.setattr(gr, "run_bounded", lambda *a, **k: (1, "", "bad"))
    with pytest.raises(RuntimeError):
        gr.has_previous_session("gemini", {}, tmp_path)


def test_t41_session_id_is_validated_before_launch(monkeypatch, tmp_path, capsys):
    f = tmp_path / "brief.md"
    f.write_text("brief", encoding="utf-8")
    _setup_ready(monkeypatch)

    def no_popen(*a, **k):
        raise AssertionError("subprocess started")

    monkeypatch.setattr(gr.subprocess, "Popen", no_popen)
    with pytest.raises(SystemExit) as e:
        gr.main(["--repo", "--brief", str(f), "--model", "gemini-4-carbon", "--resume", "abc&calc"])
    assert e.value.code == 1
    assert "abc&calc" in capsys.readouterr().err


def test_t42_setup_branches(monkeypatch, tmp_path, capsys):
    _setup_ready(monkeypatch)
    present = tmp_path / "settings.json"
    present.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        gr, "system_settings_paths", lambda *a, **k: (present, tmp_path / "system-defaults.json")
    )
    gr.main(["--setup"])
    out = capsys.readouterr().out
    assert "system settings:" in out
    assert "is kept" in out

    _setup_ready(monkeypatch)
    monkeypatch.setattr(gr, "workspace_settings_present", lambda *a, **k: True)
    gr.main(["--setup"])
    out = capsys.readouterr().out
    assert "repo mode: unavailable here" in out
    assert "file mode" in out
    assert "repo mode: available" not in out

    _setup_ready(monkeypatch)
    monkeypatch.setattr(
        gr, "user_settings_blocker", lambda *a, **k: "X sets context.includeDirectories"
    )
    gr.main(["--setup"])
    out = capsys.readouterr().out
    assert "includeDirectories" in out
    assert "repo mode: available" not in out


def test_t43_list_models_failure(monkeypatch, capsys):
    monkeypatch.setattr(gr.time, "sleep", lambda *a, **k: None)
    monkeypatch.setattr(gr, "call", lambda *a, **k: (403, {"error": {"message": "API key not valid"}}))
    with pytest.raises(SystemExit) as e:
        gr.list_models("k")
    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "cannot list models" in err
    assert "403" in err

    count = []

    def flaky(*a, **k):
        count.append(1)
        return 0, {"error": {"message": "network error"}}

    monkeypatch.setattr(gr, "call", flaky)
    with pytest.raises(SystemExit) as e:
        gr.list_models("k")
    assert e.value.code == 1
    assert len(count) == 2


def test_t44_call_timeout_classification(monkeypatch):
    def timed_out(*a, **k):
        raise urllib.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(gr.urllib.request, "urlopen", timed_out)
    assert gr.call("http://example.invalid/x", "k", None)[0] == gr.STATUS_TIMEOUT

    def reset(*a, **k):
        raise ConnectionResetError()

    monkeypatch.setattr(gr.urllib.request, "urlopen", reset)
    assert gr.call("http://example.invalid/x", "k", None)[0] == 0

    count = []

    def fake_call(*a, **k):
        count.append(1)
        return gr.STATUS_TIMEOUT, {}

    monkeypatch.setattr(gr, "call", fake_call)
    monkeypatch.setattr(gr.time, "sleep", lambda *a, **k: None)
    assert gr.call_with_retry("u", "k", None)[0] == gr.STATUS_TIMEOUT
    assert len(count) == 1


def test_t45_env_file_keys_and_pinning(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".gemini").mkdir(parents=True)
    (repo / ".env").write_text(
        "NODE_OPTIONS=--require ./x.js\nexport GEMINI_CLI_HOME=./h\nHTTPS_PROXY: http://p\n# COMMENTED=1\n",
        encoding="utf-8",
    )
    (repo / ".gemini" / ".env").write_text("GEMINI_SYSTEM_MD=~/.ssh/id_rsa\n", encoding="utf-8")
    keys = gr.env_file_keys(repo, tmp_path / "home")
    assert {"NODE_OPTIONS", "GEMINI_CLI_HOME", "HTTPS_PROXY", "GEMINI_SYSTEM_MD"} <= keys
    assert "COMMENTED" not in keys
    env = gr.build_repo_env({"GEMINI_API_KEY": "b", "HTTPS_PROXY": "http://mine"}, None, gr.SETTINGS_PATH, keys)
    assert env["NODE_OPTIONS"] == ""
    assert env["GEMINI_CLI_HOME"] == ""
    assert env["HTTPS_PROXY"] == "http://mine"
    assert env["GEMINI_SYSTEM_MD"] == "false"
    assert env["GEMINI_SANDBOX"] == "false"
    assert env["GEMINI_WRITE_SYSTEM_MD"] == "false"
    assert env["GEMINI_CLI_NO_RELAUNCH"] == "true"


def test_t46_workspace_settings_present_skips_home(monkeypatch, tmp_path):
    monkeypatch.setattr(gr.Path, "home", staticmethod(lambda: tmp_path))
    (tmp_path / ".gemini").mkdir()
    (tmp_path / ".gemini" / "settings.json").write_text("{}", encoding="utf-8")
    assert gr.workspace_settings_present(tmp_path, tmp_path) is False
    sub = tmp_path / "sub"
    (sub / ".gemini").mkdir(parents=True)
    (sub / ".gemini" / "settings.json").write_text("{}", encoding="utf-8")
    assert gr.workspace_settings_present(sub, tmp_path) is True


def test_t47_user_settings_blocker(tmp_path):
    environ = {"GEMINI_CLI_HOME": str(tmp_path)}
    assert gr.user_settings_blocker(environ) is None
    (tmp_path / ".gemini").mkdir()
    path = tmp_path / ".gemini" / "settings.json"
    path.write_text(json.dumps({"context": {"includeDirectories": ["C:/x"]}}), encoding="utf-8")
    assert "includeDirectories" in gr.user_settings_blocker(environ)
    path.write_text(json.dumps({"context": {}}), encoding="utf-8")
    assert gr.user_settings_blocker(environ) is None
    path.write_text("{ includeDirectories broken", encoding="utf-8")
    assert "cannot parse" in gr.user_settings_blocker(environ)


@needs_git
def test_t48_links_into_ignored(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "core.symlinks", "true")
    (root / ".gitignore").write_text("secrets/\n", encoding="utf-8")
    (root / "secrets").mkdir()
    (root / "secrets" / "s.env").write_text("K=V\n", encoding="utf-8")
    try:
        os.symlink("secrets", root / "lnk", target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"cannot create symlinks here: {exc}")
    _git(root, "add", ".gitignore", "lnk")
    _git(root, "commit", "-q", "-m", "init")
    ignored = gr.ignored_entries(root.resolve())
    assert "secrets/" in ignored
    assert gr.links_into_ignored(root.resolve(), ignored) == ["lnk"]


def test_t49_neutralize_brief():
    out = gr.neutralize_brief("see @secrets/x and a @ b")
    assert out.startswith("Brief:\n\n")
    assert "@\u200bsecrets/x" in out
    assert "a @ b" in out
    assert not gr.neutralize_brief("/cmd now").startswith("/")
