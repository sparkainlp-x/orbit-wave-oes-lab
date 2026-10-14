import json

from orbit_wave_oes_lab.pipeline import run_demo


def test_demo_builds_passport_and_marks_analog_capture_missing(tmp_path):
    result = run_demo(tmp_path / "run", seed=20261011, steps=40, with_oes=False)
    assert result["status"] == "completed"
    assert result["evidence_class"] == "SYNTHETIC"
    assert (tmp_path / "run" / "orbit_payload_timeline.csv").is_file()
    assert (tmp_path / "run" / "binaural_calibration_reference.wav").is_file()
    assert not (tmp_path / "run" / "capture.wav").exists()
    assert (tmp_path / "run" / "evidence-passport" / "synthetic-orbit-wave-demo.html").is_file()
    passport = json.loads((tmp_path / "run" / "evidence-passport" / "synthetic-orbit-wave-demo.normalized.json").read_text())
    assert passport["evidence_class"] == "synthetic"
    assert passport["integrity"]["bundle_consistent"] is True
    assert len(passport["integrity"]["files"]) == 8
    assert "not authenticated" in " ".join(passport["limitations"]).lower() or "not authenticated" in " ".join(result["limitations"]).lower()


def test_manifest_source_url_and_commit_shape(tmp_path):
    from orbit_wave_oes_lab.pipeline import REPOSITORY_URL, _git_commit

    assert REPOSITORY_URL == "https://github.com/sparkainlp-x/orbit-wave-oes-lab"
    sha = _git_commit()
    assert sha is None or (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha))


def _init_repo(path, pyproject_text):
    import shutil
    import subprocess

    git = shutil.which("git")
    path.mkdir()
    if pyproject_text is not None:
        (path / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "PATH": "/usr/bin:/bin"}
    for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "--allow-empty", "-m", "x"]):
        subprocess.run([git, *args], cwd=path, env=env, check=True, capture_output=True)  # noqa: S603
    out = subprocess.run([git, "rev-parse", "HEAD"], cwd=path, env=env, check=True, capture_output=True, text=True)  # noqa: S603
    return out.stdout.strip()


def test_git_commit_only_for_this_project_work_tree(tmp_path):
    import shutil

    import pytest

    from orbit_wave_oes_lab.pipeline import _git_commit

    if shutil.which("git") is None:
        pytest.skip("git not available")
    other = tmp_path / "other"
    _init_repo(other, '[project]\nname = "something-else"\n')
    assert _git_commit(other) is None
    bare = tmp_path / "bare"
    _init_repo(bare, None)
    assert _git_commit(bare) is None
    ours = tmp_path / "ours"
    sha = _init_repo(ours, '[project]\nname = "orbit-wave-oes-lab"\n')
    assert _git_commit(ours) == sha
    assert _git_commit(tmp_path) is None  # not inside any work tree
