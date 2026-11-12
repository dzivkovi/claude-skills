import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gemini_review.py"
spec = importlib.util.spec_from_file_location("gr", SCRIPT)
gr = importlib.util.module_from_spec(spec)
sys.modules["gr"] = gr
spec.loader.exec_module(gr)


@pytest.fixture(autouse=True)
def _undo_find_git_env(monkeypatch):
    # find_git writes this variable into os.environ; start clean so monkeypatch undoes it.
    monkeypatch.delenv("NoDefaultCurrentDirectoryInExePath", raising=False)


class Repo:
    def __init__(self, path: Path):
        self.path = path

    def g(self, *args):
        return subprocess.run(["git", *args], cwd=self.path, check=True, capture_output=True)

    def write(self, rel, content="x = 1\n"):
        p = self.path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return p

    def commit(self, *paths, force=False):
        self.g("add", *(["-f"] if force else []), *(paths or ["-A"]))
        self.g("-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false",
               "commit", "-q", "-m", "c")


@pytest.fixture
def git_repo(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("git not available")
    path = tmp_path / "repo"
    path.mkdir()
    repo = Repo(path)
    repo.g("init", "-q")
    return repo


@pytest.fixture
def brief(tmp_path):
    p = tmp_path / "brief.md"
    p.write_text("BRIEF TEXT", encoding="utf-8")
    return p


def no_network(*a, **k):
    raise AssertionError("network attempted")


def dry_run(monkeypatch, repo, brief, paths, extra=()):
    monkeypatch.chdir(repo.path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(gr, "call", no_network)
    gr.main(["--file", str(brief), "--repo", *paths, *extra, "--dry-run"])


def refused(monkeypatch, repo, brief, paths, extra=()):
    with pytest.raises(SystemExit) as e:
        dry_run(monkeypatch, repo, brief, paths, extra)
    assert e.value.code == 3


# ---- A: model resolution


def test_a1_carbon_picks_highest_version_and_skips_preview():
    ids = ["gemini-3-carbon", "gemini-4-carbon", "gemini-4-carbon-preview"]
    assert gr.pick_model("carbon", ids) == "gemini-4-carbon"


def test_a2_flash_prefers_latest_alias():
    ids = ["gemini-3.8-flash", "gemini-flash-latest"]
    assert gr.pick_model("flash", ids) == "gemini-flash-latest"


def test_a3_flash_picks_highest_version_and_skips_excluded_tokens():
    ids = [
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.8-flash-lite",
        "gemini-3.8-flash-preview-tts",
    ]
    assert gr.pick_model("flash", ids) == "gemini-3.8-flash"


def test_a4_unknown_alias_returns_none():
    assert gr.pick_model("nothing", ["gemini-3.8-flash"]) is None


def test_a5_lite_alias_may_match_lite_ids():
    ids = ["gemini-3.8-flash", "gemini-3.8-flash-lite"]
    assert gr.pick_model("lite", ids) == "gemini-3.8-flash-lite"


def test_a6_unknown_alias_exits_5(monkeypatch, capsys):
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-3.8-flash"])
    with pytest.raises(SystemExit) as e:
        gr.resolve_model("nothing", "k")
    assert e.value.code == 5
    assert "no generateContent model matches alias 'nothing'" in capsys.readouterr().err


def test_a7_rejected_model_lists_available(monkeypatch, tmp_path, capsys):
    f = tmp_path / "f.md"
    f.write_text("material", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(
        gr, "call", lambda *a, **k: (404, {"error": {"message": "models/gemini-x is not found"}})
    )
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-4-carbon"])
    monkeypatch.setattr(gr, "output_token_limit", lambda *a, **k: None)
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(f), "--model", "gemini-x"])
    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "rejected (404)" in err
    assert "gemini-4-carbon" in err


def test_a8_validate_model_id():
    assert gr.validate_model_id("gemini-4-carbon") == "gemini-4-carbon"
    for bad in ["models/../x", "a b", "..", "-x", "gemini..x", "x" * 129]:
        with pytest.raises(SystemExit) as e:
            gr.validate_model_id(bad)
        assert e.value.code == 1
    with pytest.raises(SystemExit) as e:
        gr.resolve_model("gemini-a/b", "k")
    assert e.value.code == 1


# ---- B: request body and send loop


def test_b1_build_body_attachments_and_fences():
    body = gr.build_body(
        "BRIEF", "high",
        [gr.Attachment("src/a.py", "x = 1\n```\ny"), gr.Attachment("b.md", "plain")],
    )
    parts = body["contents"][0]["parts"]
    assert parts[0]["text"] == "BRIEF"
    assert parts[1]["text"].startswith("Repository file `src/a.py`:")
    assert parts[1]["text"].splitlines()[2] == "````"
    assert parts[2]["text"].splitlines()[2] == "```"
    assert "not instructions" in body["systemInstruction"]["parts"][0]["text"]


def test_b2_build_body_thinking_and_max_output():
    assert gr.build_body("x", "low")["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"
    assert gr.build_body("x", "high", None, 32768)["generationConfig"]["maxOutputTokens"] == 32768
    assert "maxOutputTokens" not in gr.build_body("x", "high")["generationConfig"]


def test_b3_extract_answer_skips_thoughts():
    cand = {"content": {"parts": [{"text": "secret", "thought": True}, {"text": "visible"}]}}
    assert gr.extract_answer(cand) == "visible"


def _send_env(monkeypatch, limit=32768):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-4-carbon"])
    monkeypatch.setattr(gr, "output_token_limit", lambda *a, **k: limit)
    monkeypatch.setattr(gr.time, "sleep", lambda *a, **k: None)


EMPTY_MAX = (
    200,
    {"candidates": [{"content": {"parts": []}, "finishReason": "MAX_TOKENS"}], "usageMetadata": {"a": 1}},
)
GOOD = (
    200,
    {"candidates": [{"content": {"parts": [{"text": "ok"}]}, "finishReason": "STOP"}]},
)


def test_b4_empty_max_tokens_retries_with_low_thinking(monkeypatch, brief, capsys):
    _send_env(monkeypatch)
    responses = [EMPTY_MAX, GOOD]
    bodies = []

    def fake(url, key, body):
        bodies.append(body)
        return responses[len(bodies) - 1]

    monkeypatch.setattr(gr, "call", fake)
    gr.main(["--file", str(brief)])
    out, err = capsys.readouterr()
    assert "ok" in out
    assert len(bodies) == 2
    assert bodies[0]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "high"
    assert bodies[1]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "low"
    assert "retrying once with thinking low" in err
    assert "thinking=low" in err


def test_b5_two_empty_answers_fail(monkeypatch, brief, capsys):
    _send_env(monkeypatch)
    calls = []

    def fake(url, key, body):
        calls.append(body)
        return EMPTY_MAX

    monkeypatch.setattr(gr, "call", fake)
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(brief)])
    assert e.value.code == 1
    assert "empty answer" in capsys.readouterr().err
    assert len(calls) == 2


# ---- C: setup


def test_c1_setup_reports_model_and_git(monkeypatch, capsys):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-4-carbon"])
    gr.main(["--setup"])
    out, err = capsys.readouterr()
    assert "carbon -> gemini-4-carbon, thinking high" in out
    assert "git:" in out
    assert "cli:" not in out and "cli:" not in err
    assert "test-key-123" not in out and "test-key-123" not in err


def test_c2_setup_without_key_fails(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as e:
        gr.main(["--setup"])
    assert e.value.code == 1
    assert "GEMINI_API_KEY is not set" in capsys.readouterr().err


def test_c3_setup_unknown_alias_exits_5(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-3.8-flash"])
    with pytest.raises(SystemExit) as e:
        gr.main(["--setup"])
    assert e.value.code == 5


# ---- D: repo gate (dry runs: no key, no network)


def test_d1_tracked_file_is_attached(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py")
    git_repo.commit()
    dry_run(monkeypatch, git_repo, brief, ["src/a.py"])
    err = capsys.readouterr().err
    assert "attaching 1 files" in err
    assert "src/a.py" in err


def test_d2_ignored_untracked_file_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write(".gitignore", "secrets/\n")
    git_repo.write("secrets/s.env", "K=1\n")
    refused(monkeypatch, git_repo, brief, ["secrets/s.env"])
    err = capsys.readouterr().err
    assert "nothing sent" in err
    assert "secrets/s.env" in err


def test_d3_force_added_ignored_file_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write(".gitignore", "*.canary\n")
    git_repo.write("notes.canary", "hello\n")
    git_repo.commit(".gitignore")
    git_repo.commit("notes.canary", force=True)
    refused(monkeypatch, git_repo, brief, ["notes.canary"])
    assert "check-ignore" in capsys.readouterr().err


def test_d4_core_excludes_file_refused(monkeypatch, git_repo, brief, tmp_path):
    excludes = tmp_path / "global-excludes"
    excludes.write_text("excluded.txt\n", encoding="utf-8")
    git_repo.g("config", "core.excludesFile", excludes.as_posix())
    git_repo.write("excluded.txt", "data\n")
    refused(monkeypatch, git_repo, brief, ["excluded.txt"])


def test_d5_secret_names_refused_but_example_allowed(monkeypatch, git_repo, brief, capsys):
    git_repo.write(".env", "K=1\n")
    git_repo.write("config/id_rsa", "key\n")
    git_repo.write(".env.example", "K=\n")
    git_repo.commit(force=True)
    for name in (".env", "config/id_rsa"):
        refused(monkeypatch, git_repo, brief, [name])
        assert "secret file name" in capsys.readouterr().err
    dry_run(monkeypatch, git_repo, brief, [".env.example"])
    assert "attaching 1 files" in capsys.readouterr().err


def test_d6_skip_worktree_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("local.cfg", "a=1\n")
    git_repo.commit()
    git_repo.g("update-index", "--skip-worktree", "local.cfg")
    refused(monkeypatch, git_repo, brief, ["local.cfg"])
    assert "skip-worktree" in capsys.readouterr().err


def test_d7_untracked_not_ignored_file_allowed(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py")
    git_repo.commit()
    git_repo.write("src/draft.py", "y = 2\n")
    dry_run(monkeypatch, git_repo, brief, ["src/draft.py"])
    assert "attaching 1 files" in capsys.readouterr().err


def test_d8_folder_expands_to_tracked_files_in_order(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py")
    git_repo.write("src/b.py")
    git_repo.commit()
    git_repo.write("src/c.py")
    dry_run(monkeypatch, git_repo, brief, ["src"])
    err = capsys.readouterr().err
    assert err.index("src/a.py") < err.index("src/b.py")
    assert "src/c.py" not in err


def test_d9_symlinked_directory_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py")
    git_repo.commit()
    try:
        os.symlink("src", git_repo.path / "lnk", target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"cannot create symlink: {exc}")
    refused(monkeypatch, git_repo, brief, ["lnk/a.py"])
    assert "link" in capsys.readouterr().err


def test_d10_outside_and_missing_paths_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["../outside.txt"])
    assert "outside the repository" in capsys.readouterr().err
    refused(monkeypatch, git_repo, brief, ["missing.py"])


def test_d11_binary_file_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("bin.dat", b"\x00\x01")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["bin.dat"])
    assert "binary" in capsys.readouterr().err


def test_d12_over_max_bytes_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("big.txt", "a" * 2000)
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["big.txt"], extra=["--max-bytes", "1000"])
    err = capsys.readouterr().err
    assert "over --max-bytes" in err
    assert "big.txt" in err


def test_d13_not_a_repository_refused(monkeypatch, tmp_path, brief):
    notrepo = tmp_path / "notrepo"
    notrepo.mkdir()
    monkeypatch.chdir(notrepo)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(gr, "call", no_network)
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(brief), "--repo", "x.py", "--dry-run"])
    assert e.value.code == 3


def test_d14_one_refused_path_stops_everything(monkeypatch, git_repo, brief, capsys):
    git_repo.write(".gitignore", "secrets/\n")
    git_repo.write("src/a.py")
    git_repo.commit()
    git_repo.write("secrets/s.env", "K=1\n")
    calls = []
    monkeypatch.chdir(git_repo.path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "call", lambda *a, **k: calls.append(a) or no_network())
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: calls.append(a) or no_network())
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(brief), "--repo", "src/a.py", "secrets/s.env"])
    assert e.value.code == 3
    assert calls == []
    assert "nothing sent" in capsys.readouterr().err


def test_d15_save_request_holds_brief_and_file(monkeypatch, git_repo, brief, tmp_path):
    git_repo.write("src/a.py", "VISIBLE_TEXT")
    git_repo.commit()
    monkeypatch.chdir(git_repo.path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["gemini-4-carbon"])
    monkeypatch.setattr(gr, "output_token_limit", lambda *a, **k: None)
    monkeypatch.setattr(gr, "call", lambda *a, **k: GOOD)
    req = tmp_path / "req.json"
    gr.main(["--file", str(brief), "--repo", "src/a.py", "--save-request", str(req)])
    text = req.read_text(encoding="utf-8")
    assert "VISIBLE_TEXT" in text
    assert "Repository file `src/a.py`" in text
    parts = json.loads(text)["contents"][0]["parts"]
    assert parts[0]["text"] == "BRIEF TEXT"


def test_d16_encrypting_filter_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write(".gitattributes", "*.secret filter=git-crypt diff=git-crypt\n")
    git_repo.write("x.secret", "data\n")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["x.secret"])
    assert "encrypting" in capsys.readouterr().err


# ---- E: usage errors and helpers


def test_e1_usage_errors_exit_2(tmp_path):
    f = tmp_path / "f.md"
    f.write_text("m", encoding="utf-8")
    for argv in (["--file", str(f), "--repo"], ["--brief", str(f)], ["--file", str(f), "--dry-run"]):
        with pytest.raises(SystemExit) as e:
            gr.main(argv)
        assert e.value.code == 2


@pytest.mark.skipif(sys.platform != "win32", reason="NTFS junctions are Windows-only")
def test_d9b_junction_into_ignored_folder_refused(monkeypatch, git_repo, brief, capsys):
    # git lists lnk/s.env as untracked-not-ignored: the reparse-point check is the only guard.
    import _winapi
    git_repo.write(".gitignore", "secrets/\n")
    git_repo.write("secrets/s.env", "TOKEN=1\n")
    git_repo.commit(".gitignore")
    _winapi.CreateJunction(str(git_repo.path / "secrets"), str(git_repo.path / "lnk"))
    refused(monkeypatch, git_repo, brief, ["lnk/s.env"])
    assert "link" in capsys.readouterr().err
    refused(monkeypatch, git_repo, brief, ["lnk"])


def test_d16b_any_content_filter_refused_but_lfs_allowed(monkeypatch, git_repo, brief, capsys):
    # transcrypt uses filter=crypt, git-crypt with a named key uses git-crypt-<key>.
    git_repo.write(".gitattributes", "*.t filter=crypt\n*.bin2 filter=lfs\n")
    git_repo.write("x.t", "plain\n")
    git_repo.write("y.bin2", "plain\n")
    git_repo.commit(".gitattributes", "x.t", "y.bin2")
    refused(monkeypatch, git_repo, brief, ["x.t"])
    assert "content filter" in capsys.readouterr().err
    dry_run(monkeypatch, git_repo, brief, ["y.bin2"])


def test_d17_folder_member_binary_is_omitted_not_fatal(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py", "x = 1\n")
    git_repo.write("src/logo.png", b"\x89PNG\x00\x00")
    git_repo.commit()
    dry_run(monkeypatch, git_repo, brief, ["src"])
    err = capsys.readouterr().err
    assert "omitted src/logo.png" in err and "attaching 1 files" in err


def test_d18_dry_run_save_request_writes_body_without_network(monkeypatch, git_repo, brief, tmp_path):
    git_repo.write("src/a.py", "VISIBLE_TEXT\n")
    git_repo.commit()
    out = tmp_path / "req.json"
    dry_run(monkeypatch, git_repo, brief, ["src/a.py"], ["--save-request", str(out)])
    body = json.loads(out.read_text(encoding="utf-8"))
    assert body["contents"][0]["parts"][0]["text"] == "BRIEF TEXT"
    assert "VISIBLE_TEXT" in body["contents"][0]["parts"][1]["text"]


def test_d19_inherited_git_dir_is_ignored(monkeypatch, git_repo, brief, tmp_path, capsys):
    git_repo.write("src/a.py")
    git_repo.commit()
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "elsewhere"))
    dry_run(monkeypatch, git_repo, brief, ["src/a.py"])
    assert "attaching 1 files" in capsys.readouterr().err


def test_d20_empty_filter_value_does_not_shift_the_crypt_check(monkeypatch, git_repo, brief, capsys):
    # `filter=` prints an empty value; dropping it once shifted later triples and let z.txt through.
    git_repo.write(".gitattributes", "a.txt filter=\nz.txt filter=git-crypt\n")
    git_repo.write("a.txt", "a\n")
    git_repo.write("z.txt", "z\n")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["z.txt"])
    assert "content filter" in capsys.readouterr().err


def test_d21_explicit_binary_aborts_even_after_its_folder(monkeypatch, git_repo, brief, capsys):
    git_repo.write("sub/a.py", "x = 1\n")
    git_repo.write("sub/s.bin", b"\x00\x01")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["sub", "sub/s.bin"])
    refused(monkeypatch, git_repo, brief, ["sub/s.bin", "sub"])


def test_d22_large_binary_under_folder_is_omitted_not_a_size_overflow(monkeypatch, git_repo, brief, capsys):
    git_repo.write("docs/readme.md", "hello\n")
    git_repo.write("docs/big.png", b"\x89PNG\x00" + b"\x01" * 3000)
    git_repo.commit()
    dry_run(monkeypatch, git_repo, brief, ["docs"], ["--max-bytes", "1000"])
    err = capsys.readouterr().err
    assert "omitted docs/big.png" in err and "attaching 1 files" in err


@pytest.mark.skipif(sys.platform != "win32", reason="case-insensitive paths are a Windows behavior")
def test_d23_folder_name_case_is_folded_on_windows(monkeypatch, git_repo, brief, capsys):
    git_repo.write("sub/a.py")
    git_repo.commit()
    dry_run(monkeypatch, git_repo, brief, ["SUB"])
    assert "sub/a.py" in capsys.readouterr().err


def test_d24_dry_run_checks_the_brief(monkeypatch, git_repo, tmp_path):
    git_repo.write("src/a.py")
    git_repo.commit()
    with pytest.raises(SystemExit) as e:
        dry_run(monkeypatch, git_repo, tmp_path / "missing.md", ["src/a.py"])
    assert e.value.code == 1


def test_d25_hardlink_is_refused(monkeypatch, git_repo, brief, tmp_path, capsys):
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("TOPSECRET\n", encoding="utf-8")
    git_repo.write("README.md", "hi\n")
    git_repo.commit()
    try:
        os.link(outside, git_repo.path / "notes.txt")
    except OSError as exc:
        pytest.skip(f"cannot create a hard link: {exc}")
    refused(monkeypatch, git_repo, brief, ["notes.txt"])
    assert "hard link" in capsys.readouterr().err


def test_d26_directory_symlink_elsewhere_does_not_break_other_files(monkeypatch, git_repo, brief, capsys):
    git_repo.write("d/inner.txt", "x\n")
    git_repo.write("ok.py", "y = 1\n")
    git_repo.commit()
    shutil.rmtree(git_repo.path / "d")
    try:
        os.symlink(str(git_repo.path), git_repo.path / "d", target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"cannot create symlink: {exc}")
    dry_run(monkeypatch, git_repo, brief, ["ok.py"])
    assert "attaching 1 files" in capsys.readouterr().err


def diff_repo(git_repo):
    git_repo.write(".gitignore", "private/\n")
    git_repo.write("src/a.py", "x = 1\n")
    git_repo.write("private/notes.md", "old\n")
    git_repo.write(".env", "TOKEN=old\n")
    git_repo.commit(".gitignore", "src/a.py")
    git_repo.commit("private/notes.md", ".env", force=True)
    git_repo.write("src/a.py", "x = 2\n")
    git_repo.write("private/notes.md", "TOPSECRET_DIFF\n")
    git_repo.write(".env", "TOKEN=TOPSECRET_ENV\n")


def test_d27_diff_leaves_out_refused_files(monkeypatch, git_repo, brief, tmp_path, capsys):
    diff_repo(git_repo)
    out = tmp_path / "req.json"
    monkeypatch.chdir(git_repo.path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(gr, "call", no_network)
    gr.main(["--file", str(brief), "--diff", "--dry-run", "--save-request", str(out)])
    sent = out.read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "x = 2" in sent
    assert "TOPSECRET" not in sent
    assert "left out of the diff: private/notes.md" in err
    assert "left out of the diff: .env" in err


def test_d28_diff_with_nothing_allowed_is_refused(monkeypatch, git_repo, brief):
    diff_repo(git_repo)
    git_repo.g("checkout", "--", "src/a.py")
    monkeypatch.chdir(git_repo.path)
    monkeypatch.setattr(gr, "call", no_network)
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(brief), "--diff", "--dry-run"])
    assert e.value.code == 3


def test_d29_diff_base_must_be_a_plain_ref(monkeypatch, git_repo, brief):
    monkeypatch.chdir(git_repo.path)
    with pytest.raises(SystemExit) as e:
        gr.main(["--file", str(brief), "--diff", "main;rm -rf", "--dry-run"])
    assert e.value.code == 1


def test_e3_more_secret_names():
    for name in (".envrc", ".git-credentials", "credentials.json", "service-account-prod.json",
                 "prod.tfvars", "k.ppk", "store.jks"):
        assert gr.secret_name(name), name


def test_d6b_assume_unchanged_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("local.cfg", "a\n")
    git_repo.commit()
    git_repo.g("update-index", "--assume-unchanged", "local.cfg")
    git_repo.write("local.cfg", "SECRET\n")
    refused(monkeypatch, git_repo, brief, ["local.cfg"])
    assert "assume-unchanged" in capsys.readouterr().err


def test_d9c_tracked_folder_swapped_for_link_refused(monkeypatch, git_repo, brief, tmp_path, capsys):
    git_repo.write(".gitignore", "secrets/\n")
    git_repo.write("src/a.py", "x = 1\n")
    git_repo.commit()
    git_repo.write("secrets/a.py", "MARKER_X")
    shutil.rmtree(git_repo.path / "src")
    try:
        if sys.platform == "win32":
            import _winapi
            _winapi.CreateJunction(str(git_repo.path / "secrets"), str(git_repo.path / "src"))
        else:
            os.symlink("secrets", git_repo.path / "src", target_is_directory=True)
    except OSError:
        pytest.skip("cannot create a directory link here")
    out = tmp_path / "req.json"
    refused(monkeypatch, git_repo, brief, ["src"], ["--save-request", str(out)])
    assert "link on its path" in capsys.readouterr().err
    assert not out.exists() or "MARKER_X" not in out.read_text(encoding="utf-8")
    refused(monkeypatch, git_repo, brief, ["src/a.py"])


def test_f1_find_git_rejects_git_inside_repo(monkeypatch, git_repo, tmp_path):
    inside = git_repo.write("tools/git.exe", "fake")
    monkeypatch.chdir(git_repo.path)
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: str(inside))
    assert gr.find_git(git_repo.path) is None
    top = git_repo.write("git.exe", "fake")
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: str(top))
    assert gr.find_git(git_repo.path) is None
    outside = tmp_path / "bin" / "git.exe"
    outside.parent.mkdir()
    outside.write_text("fake")
    monkeypatch.setattr(gr.shutil, "which", lambda *a, **k: str(outside))
    assert gr.find_git(git_repo.path) == str(outside.resolve())


def test_f2_load_gate_rejects_git_under_root(monkeypatch, git_repo):
    fake = git_repo.path / "tools" / "git.exe"
    monkeypatch.setattr(gr, "find_git", lambda *a, **k: str(fake))
    monkeypatch.setattr(
        gr, "run_git",
        lambda git, args, *a, **k: (str(git_repo.path) + "\n").encode() if args[0] == "rev-parse" else b"",
    )
    with pytest.raises(RuntimeError) as e:
        gr.load_gate(git_repo.path)
    assert "inside this repository" in str(e.value)


def test_d11b_explicit_binary_next_to_good_file_aborts(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py", "x = 1\n")
    git_repo.write("bin.dat", b"\x00\x01")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["src/a.py", "bin.dat"])
    err = capsys.readouterr().err
    assert "nothing sent" in err and "omitted bin.dat" not in err


def test_d10b_outside_reason_is_specific(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/a.py")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["../outside.txt"])
    assert "../outside.txt: outside the repository" in capsys.readouterr().err


def test_d30_non_utf8_text_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("latin.txt", b"caf\xe9\n")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["latin.txt"])
    assert "not UTF-8" in capsys.readouterr().err


def test_d31_folder_with_every_member_omitted_is_refused(monkeypatch, git_repo, brief, capsys):
    git_repo.write("src/logo.png", b"\x89PNG\x00")
    git_repo.commit()
    refused(monkeypatch, git_repo, brief, ["src"])
    assert "no file passed" in capsys.readouterr().err


def test_g1_list_models_failure_exits_1_not_5(monkeypatch, capsys):
    monkeypatch.setattr(gr, "call", lambda *a, **k: (403, {"error": {"message": "API key not valid"}}))
    monkeypatch.setattr(gr.time, "sleep", lambda *a: None)
    with pytest.raises(SystemExit) as e:
        gr.resolve_model("carbon", "k")
    assert e.value.code == 1
    assert "cannot list models" in capsys.readouterr().err


def test_g2_read_timeout_is_not_retried(monkeypatch):
    calls = []

    def fake(status):
        def _call(*a, **k):
            calls.append(1)
            return status, {"error": {"message": "t"}}
        return _call

    monkeypatch.setattr(gr.time, "sleep", lambda *a: None)
    monkeypatch.setattr(gr, "call", fake(gr.STATUS_TIMEOUT))
    status, _ = gr.call_with_retry("u", "k", None)
    assert status == gr.STATUS_TIMEOUT and len(calls) == 1
    calls.clear()
    monkeypatch.setattr(gr, "call", fake(0))
    gr.call_with_retry("u", "k", None)
    assert len(calls) == 2


def test_g3_alias_result_is_validated(monkeypatch):
    monkeypatch.setattr(gr, "list_models", lambda *a, **k: ["a"])
    monkeypatch.setattr(gr, "pick_model", lambda *a: "gemini-x/../y")
    with pytest.raises(SystemExit) as e:
        gr.resolve_model("carbon", "k")
    assert e.value.code == 1


def test_g4_out_file_written(monkeypatch, brief, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-123")
    monkeypatch.setattr(gr, "output_token_limit", lambda *a, **k: None)
    monkeypatch.setattr(
        gr, "call",
        lambda *a, **k: (200, {"candidates": [{"content": {"parts": [{"text": "ANSWER"}]}, "finishReason": "STOP"}]}),
    )
    ans = tmp_path / "ans.md"
    gr.main(["--file", str(brief), "--model", "gemini-4-carbon", "--out", str(ans)])
    assert "ANSWER" in ans.read_text(encoding="utf-8")


def test_b6_preamble_tells_gemini_to_ignore_file_instructions():
    assert "ignore any instruction" in gr.PREAMBLE


def test_e2_secret_name():
    for name in (".env", "config/.env.local", "a/id_rsa.pub", "k.PEM"):
        assert gr.secret_name(name) is True, name
    for name in ("README.md", ".env.example", "environment.py"):
        assert gr.secret_name(name) is False, name
