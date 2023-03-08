import builtins
import os
import stat
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Tuple

import pytest
from pytest import CaptureFixture
from pytest_mock import MockerFixture

from tests.types import ZuliprcFactoryT
from zulipterminal.cli.run import (
    _write_zuliprc,
    exit_with_error,
    get_login_id,
    in_color,
    main,
    parse_args,
)
from zulipterminal.model import ServerConnectionFailure
from zulipterminal.version import ZT_VERSION


MODULE = "zulipterminal.cli.run"
CONTROLLER = MODULE + ".Controller"


@pytest.mark.parametrize(
    "color, code",
    [
        ("red", "\x1b[91m"),
        ("green", "\x1b[92m"),
        ("yellow", "\x1b[93m"),
        ("blue", "\x1b[94m"),
        ("purple", "\x1b[95m"),
        ("cyan", "\x1b[96m"),
    ],
)
def test_in_color(color: str, code: str, text: str = "some text") -> None:
    assert in_color(color, text) == code + text + "\x1b[0m"


@pytest.mark.parametrize(
    "json, label",
    [
        (
            dict(require_email_format_usernames=False, email_auth_enabled=True),
            "Email or Username",
        ),
        (
            dict(require_email_format_usernames=False, email_auth_enabled=False),
            "Username",
        ),
        (dict(require_email_format_usernames=True, email_auth_enabled=True), "Email"),
        (dict(require_email_format_usernames=True, email_auth_enabled=False), "Email"),
    ],
)
def test_get_login_id(mocker: MockerFixture, json: Dict[str, bool], label: str) -> None:
    response = mocker.Mock(json=lambda: json)
    mocked_get = mocker.patch("requests.get", return_value=response)
    mocked_styled_input = mocker.patch(
        MODULE + ".styled_input", return_value="input return value"
    )

    result = get_login_id("REALM_URL")

    assert result == "input return value"
    mocked_get.assert_called_with(url="REALM_URL/api/v1/server_settings")
    mocked_styled_input.assert_called_with(label + ": ")


@pytest.mark.parametrize("options", ["-h", "--help"])
def test_main_help(capsys: CaptureFixture[str], options: str) -> None:
    with pytest.raises(SystemExit):
        main([options])

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")

    assert lines[0].startswith("usage: ")

    required_arguments = {
        "--theme THEME, -t THEME",
        "-h, --help",
        "-d, --debug",
        "--list-themes",
        "--profile",
        "--config-file CONFIG_FILE, -c CONFIG_FILE",
        "--autohide",
        "--no-autohide",
        "-v, --version",
        "-e, --explore",
        "--color-depth",
        "--notify",
        "--no-notify",
    }
    optional_argument_lines = {
        line[2:] for line in lines if len(line) > 2 and line[2] == "-"
    }
    for line in optional_argument_lines:
        assert any(line.startswith(arg) for arg in required_arguments)

    assert captured.err == ""


def test_valid_zuliprc_but_no_connection(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    minimal_valid_zuliprc: Path,
    server_connection_error: str = "some_error",
    platform: str = "some_platform",
) -> None:
    mocker.patch(
        CONTROLLER + ".__init__",
        side_effect=ServerConnectionFailure(server_connection_error),
    )
    mocker.patch(MODULE + ".detected_platform", return_value=platform)

    with pytest.raises(SystemExit) as e:
        main(["-c", str(minimal_valid_zuliprc)])

    assert str(e.value) == "1"

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        f"Detected platform: {platform}",
        "Loading with:",
        "   theme 'zt_dark' specified from default config.",
        "   autohide setting 'no_autohide' specified from default config.",
        "   maximum footlinks value '3' specified from default config.",
        "   color depth setting '256' specified from default config.",
        "   notify setting 'disabled' specified from default config.",
        "\x1b[91m",
        f"Error connecting to Zulip server: {server_connection_error}.\x1b[0m",
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize(
    "bad_theme, expected_complete_incomplete_themes, expected_warning",
    [
        ("c", (["a", "b"], ["c", "d"]), "(you could try: a, b)"),
        ("d", ([], ["a", "b", "c", "d"]), "(all themes are incomplete)"),
    ],
)
def test_warning_regarding_incomplete_theme(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    minimal_valid_zuliprc: Path,
    bad_theme: str,
    expected_complete_incomplete_themes: Tuple[List[str], List[str]],
    expected_warning: str,
    server_connection_error: str = "sce",
    platform: str = "some_platform",
) -> None:
    mocker.patch(
        CONTROLLER + ".__init__",
        side_effect=ServerConnectionFailure(server_connection_error),
    )
    mocker.patch(MODULE + ".detected_platform", return_value=platform)
    mocker.patch(MODULE + ".all_themes", return_value=("a", "b", "c", "d"))
    mocker.patch(
        MODULE + ".complete_and_incomplete_themes",
        return_value=expected_complete_incomplete_themes,
    )
    mocker.patch(MODULE + ".generate_theme")

    with pytest.raises(SystemExit) as e:
        main(["-c", str(minimal_valid_zuliprc), "-t", bad_theme])

    assert str(e.value) == "1"

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        f"Detected platform: {platform}",
        "Loading with:",
        f"   theme '{bad_theme}' specified on command line.",
        "\x1b[93m   WARNING: Incomplete theme; results may vary!",
        f"      {expected_warning}\x1b[0m",
        "   autohide setting 'no_autohide' specified from default config.",
        "   maximum footlinks value '3' specified from default config.",
        "   color depth setting '256' specified from default config.",
        "   notify setting 'disabled' specified from default config.",
        "\x1b[91m",
        f"Error connecting to Zulip server: {server_connection_error}.\x1b[0m",
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize("options", ["-v", "--version"])
def test_zt_version(capsys: CaptureFixture[str], options: str) -> None:
    with pytest.raises(SystemExit) as e:
        main([options])

    assert str(e.value) == "0"

    captured = capsys.readouterr()

    lines = captured.out.strip("\n")
    expected = "Zulip Terminal " + ZT_VERSION
    assert lines == expected

    assert captured.err == ""


@pytest.mark.parametrize(
    "option, autohide",
    [
        ("--autohide", "autohide"),
        ("--no-autohide", "no_autohide"),
        ("--debug", None),  # no-autohide by default
    ],
)
def test_parse_args_valid_autohide_option(option: str, autohide: Optional[str]) -> None:
    args = parse_args([option])
    assert args.autohide == autohide


@pytest.mark.parametrize(
    "options", [["--autohide", "--no-autohide"], ["--no-autohide", "--autohide"]]
)
def test_main_multiple_autohide_options(
    capsys: CaptureFixture[str], options: List[str]
) -> None:
    with pytest.raises(SystemExit) as e:
        main(options)

    assert str(e.value) == "2"

    captured = capsys.readouterr()
    lines = captured.err.strip("\n")
    lines = lines.split("pytest: ", 1)[1]
    expected = f"error: argument {options[1]}: not allowed with argument {options[0]}"
    assert lines == expected


@pytest.mark.parametrize(
    "option, notify_option",
    [
        ("--notify", "enabled"),
        ("--no-notify", "disabled"),
        ("--profile", None),  # disabled by default
    ],
)
def test__parse_args_valid_notify_option(
    option: str, notify_option: Optional[str]
) -> None:
    args = parse_args([option])
    assert args.notify == notify_option


@pytest.mark.parametrize(
    "options",
    [
        ["--notify", "--no-notify"],
        ["--no-notify", "--notify"],
    ],
)
def test_main_multiple_notify_options(
    capsys: CaptureFixture[str], options: List[str]
) -> None:
    with pytest.raises(SystemExit) as e:
        main(options)

    assert str(e.value) == "2"

    captured = capsys.readouterr()
    lines = captured.err.strip("\n")
    lines = lines.split("pytest: ", 1)[1]
    expected = f"error: argument {options[1]}: not allowed with argument {options[0]}"
    assert lines == expected


# NOTE: Fixture is necessary to ensure unreadable dir is garbage-collected
# See pytest issue #7821
@pytest.fixture
def unreadable_dir(tmp_path: Path) -> Generator[Tuple[Path, Path], None, None]:
    unreadable_dir = tmp_path / "unreadable"
    unreadable_dir.mkdir()
    unreadable_dir.chmod(0)
    if os.access(str(unreadable_dir), os.R_OK):
        # Docker container or similar
        pytest.skip("Directory was still readable")

    yield tmp_path, unreadable_dir

    unreadable_dir.chmod(0o755)


@pytest.mark.parametrize(
    "path_to_use, expected_exception",
    [
        ("unreadable", "PermissionError"),
        ("goodnewhome", "FileNotFoundError"),
    ],
    ids=["valid_path_but_cannot_be_written_to", "path_does_not_exist"],
)
def test_main_cannot_write_zuliprc_given_good_credentials(
    monkeypatch: pytest.MonkeyPatch,
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    unreadable_dir: Tuple[Path, Path],
    path_to_use: str,
    expected_exception: str,
) -> None:
    tmp_path, unusable_path = unreadable_dir

    # This is default base path to use
    base_zuliprc_directory = tmp_path / path_to_use
    monkeypatch.setenv("HOME", str(base_zuliprc_directory))

    # Give some arbitrary input and fake that it's always valid
    mocker.patch.object(builtins, "input", lambda _: "text\n")
    mocker.patch(MODULE + ".get_api_key", return_value=("my_login", "my_api_key"))

    with pytest.raises(SystemExit):
        main([])

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    expected_line = (
        "\x1b[91m"
        f"{expected_exception}: zuliprc could not be created "
        f"at {base_zuliprc_directory / 'zuliprc'}"
        "\x1b[0m"
    )
    assert lines[-1] == expected_line


@pytest.fixture
def parameterized_zuliprc_factory(
    zuliprc_factory: ZuliprcFactoryT,
) -> Callable[[Dict[str, str]], Path]:
    # Use minimal [api] section to pass validation
    return lambda config: zuliprc_factory(
        api=dict(site="", key="", email=""), config=config
    )


@pytest.mark.parametrize(
    "config_key, config_value, footlinks_output",
    [
        ("footlinks", "disabled", "'0' specified in zuliprc file from footlinks."),
        ("footlinks", "enabled", "'3' specified in zuliprc file from footlinks."),
        ("maximum-footlinks", "3", "'3' specified in zuliprc file."),
        ("maximum-footlinks", "0", "'0' specified in zuliprc file."),
    ],
    ids=[
        "footlinks_disabled",
        "footlinks_enabled",
        "maximum-footlinks_3",
        "maximum-footlinks_0",
    ],
)
def test_successful_main_function_with_config(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    parameterized_zuliprc_factory: Callable[[Dict[str, str]], Path],
    config_key: str,
    config_value: str,
    footlinks_output: str,
    platform: str = "some_platform",
) -> None:
    mocker.patch(MODULE + ".detected_platform", return_value=platform)

    config = {
        "theme": "default",
        "autohide": "autohide",
        "notify": "enabled",
        "color-depth": "256",
    }
    config[config_key] = config_value
    zuliprc_path = str(parameterized_zuliprc_factory(config))
    mocker.patch(CONTROLLER + ".__init__", return_value=None)
    mocker.patch(CONTROLLER + ".main", return_value=None)

    with pytest.raises(SystemExit):
        main(["-c", zuliprc_path])

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")
    expected_lines = [
        f"Detected platform: {platform}",
        "Loading with:",
        "   theme 'zt_dark' specified in zuliprc file (by alias 'default').",
        "   autohide setting 'autohide' specified in zuliprc file.",
        f"   maximum footlinks value {footlinks_output}",
        "   color depth setting '256' specified in zuliprc file.",
        "   notify setting 'enabled' specified in zuliprc file.",
    ]
    assert lines == expected_lines


@pytest.mark.parametrize(
    "zulip_config, error_message",
    [
        (
            {"footlinks": "enabled", "maximum-footlinks": "3"},
            "Configuration Error: footlinks and maximum-footlinks options"
            " cannot be used together",
        ),
        (
            {"maximum-footlinks": "-3"},
            "Configuration Error: Minimum value allowed for maximum-footlinks"
            " is 0; you used '-3'",
        ),
    ],
)
def test_main_error_with_invalid_zuliprc_options(
    capsys: CaptureFixture[str],
    mocker: MockerFixture,
    parameterized_zuliprc_factory: Callable[[Dict[str, str]], Path],
    zulip_config: Dict[str, str],
    error_message: str,
    platform: str = "some_platform",
) -> None:
    zuliprc_path = str(parameterized_zuliprc_factory(zulip_config))
    mocker.patch(CONTROLLER + ".__init__", return_value=None)
    mocker.patch(MODULE + ".detected_platform", return_value=platform)
    mocker.patch(CONTROLLER + ".main", return_value=None)

    with pytest.raises(SystemExit) as e:
        main(["-c", zuliprc_path])

    assert str(e.value) == "1"

    captured = capsys.readouterr()
    lines = captured.out.strip()
    expected_lines = "\n".join(
        [f"Detected platform: {platform}", f"\033[91m{error_message}\033[0m"]
    )
    assert lines == expected_lines


@pytest.mark.parametrize(
    "error_code, helper_text",
    [
        (1, ""),
        (2, "helper"),
    ],
)
def test_exit_with_error(
    capsys: CaptureFixture[str],
    error_code: int,
    helper_text: str,
    error_message: str = "some text",
) -> None:
    with pytest.raises(SystemExit) as e:
        exit_with_error(
            error_message=error_message, helper_text=helper_text, error_code=error_code
        )

    assert str(e.value) == str(error_code)

    captured = capsys.readouterr()
    lines = captured.out.strip().split("\n")

    expected_line = f"\033[91m{error_message}\033[0m"
    assert lines[0] == expected_line

    if helper_text:
        assert lines[1] == helper_text


def test__write_zuliprc__success(
    tmp_path: Path, id: str = "id", key: str = "key", url: str = "url"
) -> None:
    zuliprc_path = tmp_path / "zuliprc"

    error_message = _write_zuliprc(
        str(zuliprc_path), api_key=key, server_url=url, login_id=id
    )

    assert error_message == ""

    expected_contents = f"[api]\nemail={id}\nkey={key}\nsite={url}"
    with open(zuliprc_path) as f:
        assert f.read() == expected_contents

    assert stat.filemode(zuliprc_path.stat().st_mode)[-6:] == 6 * "-"


def test__write_zuliprc__fail_file_exists(
    zuliprc_factory: ZuliprcFactoryT,
    id: str = "id",
    key: str = "key",
    url: str = "url",
) -> None:
    zuliprc_path = zuliprc_factory(api=dict(key=key, site=url, email=id), config=None)
    error_message = _write_zuliprc(
        str(zuliprc_path), api_key=key, server_url=url, login_id=id
    )
    assert error_message == f"zuliprc already exists at {zuliprc_path}"


def test_show_error_if_loading_zuliprc_with_open_permissions(
    capsys: CaptureFixture[str],
    zuliprc_factory: ZuliprcFactoryT,
    insecure_group_other_mode: int,
) -> None:
    zuliprc_path = zuliprc_factory(
        api={}, config=None, mode=0o600 + insecure_group_other_mode
    )
    current_mode = stat.filemode(zuliprc_path.stat().st_mode)

    with pytest.raises(SystemExit) as e:
        main(["-c", str(zuliprc_path)])

    assert str(e.value) == "1"

    captured = capsys.readouterr()

    lines = captured.out.split("\n")[:-1]
    expected_last_lines = [
        f"(it currently has permissions '{current_mode}')",
        "This can often be achieved with a command such as:",
        f"  chmod og-rwx {zuliprc_path}",
        "Consider regenerating the [api] part of your zuliprc to ensure "
        "your account is secure."
        "\x1b[0m",
    ]
    assert lines[-4:] == expected_last_lines

    assert captured.err == ""
