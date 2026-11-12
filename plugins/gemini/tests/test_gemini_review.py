import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gemini_review.py"
spec = importlib.util.spec_from_file_location("gr", SCRIPT)
gr = importlib.util.module_from_spec(spec)
sys.modules["gr"] = gr
spec.loader.exec_module(gr)


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


def test_t06_unknown_alias_exits_2(monkeypatch, capsys):
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-3.8-flash"])
    with pytest.raises(SystemExit) as e:
        gr.resolve_model("nothing", "k")
    assert e.value.code == 2
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
    assert "ok" in capsys.readouterr().out


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
    assert "test-key-123" not in out.out
    assert "test-key-123" not in out.err


def test_t11_setup_ready(monkeypatch, capsys):
    _setup_ready(monkeypatch)
    gr.main(["--setup"])
    out = capsys.readouterr()
    assert "carbon -> gemini-4-carbon, thinking high" in out.out
    assert "cli: gemini 0.35.2" in out.out
    assert "repo mode: available" in out.out
    assert "test-key-123" not in out.out


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
    assert path == gr.SETTINGS_PATH and note is None

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
    with pytest.raises(SystemExit) as e:
        gr.main(["--repo", "--brief", str(f), "--model", "gemini-4-carbon"])
    assert e.value.code == 3
    assert "workspace settings" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform != "win32", reason="Windows cwd lookup")
def test_t27_find_gemini_ignores_planted_cmd(monkeypatch, tmp_path):
    (tmp_path / "gemini.cmd").write_text("@echo off\r\necho planted\r\n", encoding="utf-8")
    monkeypatch.setenv("NoDefaultCurrentDirectoryInExePath", "0")  # restored on teardown
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    assert gr.find_gemini(tmp_path) is None
