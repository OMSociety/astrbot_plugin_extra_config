import importlib.util
import shutil
import sys
import tempfile
import types
from pathlib import Path

import pytest

_CORE = Path(__file__).resolve().parents[1] / "core"


def _load_registry():
    logger_stub = types.SimpleNamespace(
        warning=lambda *args, **kwargs: None,
        info=lambda *args, **kwargs: None,
    )
    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    api.logger = logger_stub
    astrbot.api = api
    sys.modules.setdefault("astrbot", astrbot)
    sys.modules.setdefault("astrbot.api", api)
    spec = importlib.util.spec_from_file_location(
        "registry_under_test", _CORE / "registry.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


registry = _load_registry()


@pytest.fixture()
def workdir():
    path = Path(tempfile.mkdtemp(prefix="extra-config-test-"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


def _config(path):
    return types.SimpleNamespace(config_path=str(path))


def test_creates_backup_next_to_config(workdir):
    config_path = workdir / "cmd_config.json"
    config_path.write_text("{}", encoding="utf-8-sig")

    registry.backup_config(_config(config_path))

    backups = list(workdir.glob("cmd_config.json.bak-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8-sig") == "{}"


def test_keeps_only_latest_five_backups(workdir):
    config_path = workdir / "cmd_config.json"
    config_path.write_text("{}", encoding="utf-8-sig")
    for index in range(7):
        (workdir / f"cmd_config.json.bak-20260101-00000{index}").write_text(
            "{}", encoding="utf-8"
        )

    registry.backup_config(_config(config_path))

    names = sorted(path.name for path in workdir.glob("cmd_config.json.bak-*"))
    assert len(names) == 5
    assert names[0] == "cmd_config.json.bak-20260101-000003"


def test_leaves_unrelated_files_alone(workdir):
    config_path = workdir / "cmd_config.json"
    config_path.write_text("{}", encoding="utf-8-sig")
    for index in range(6):
        (workdir / f"cmd_config.json.bak-20260101-00000{index}").write_text(
            "{}", encoding="utf-8"
        )
    keep = workdir / "other.json.bak-20260101-000000"
    keep.write_text("{}", encoding="utf-8")

    registry.backup_config(_config(config_path))

    assert keep.exists()
    assert len(list(workdir.glob("other.json.bak-*"))) == 1
    assert len(list(workdir.glob("cmd_config.json.bak-*"))) == 5


def test_skips_without_config_path(workdir):
    registry.backup_config(types.SimpleNamespace())

    assert list(workdir.iterdir()) == []
