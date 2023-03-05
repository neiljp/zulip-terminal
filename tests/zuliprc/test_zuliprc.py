import stat
from typing import Dict, Optional, Set

import pytest

from tests.types import ZuliprcFactoryT
from zulipterminal.zuliprc import ZuliprcFile


def test_init__with_path(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(api=None, config=None)
    ZuliprcFile(zuliprc_path)


def test_init__with_string(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(api=None, config=None)
    ZuliprcFile(str(zuliprc_path))


def test_security_issues_present__return_None(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(api=None, config=None)
    zuliprc_file = ZuliprcFile(zuliprc_path)
    assert zuliprc_file.security_issues_present() is None


def test_security_issues_present__return_current_permissions_str(
    zuliprc_factory: ZuliprcFactoryT,
    insecure_group_other_mode: int,
) -> None:
    zuliprc_path = zuliprc_factory(
        api=None, config=None, mode=0o600 + insecure_group_other_mode
    )
    zuliprc_file = ZuliprcFile(zuliprc_path)

    expected_text = stat.filemode(zuliprc_path.stat().st_mode)
    assert zuliprc_file.security_issues_present() == expected_text


def test_validate_structure__no_errors(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(
        api={"email": "", "key": "", "site": ""}, config=None
    )
    zuliprc_file = ZuliprcFile(zuliprc_path)
    assert zuliprc_file.validate_structure() == []


def test_validate_structure__file_missing(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(
        api={"email": "", "key": "", "site": ""}, config=None
    )
    bad_path = zuliprc_path.parent / "zuliprc2"
    zuliprc_file = ZuliprcFile(bad_path)
    assert zuliprc_file.validate_structure() == [f"Failed to load '{bad_path}'"]


@pytest.mark.parametrize("with_api_section_present", [True, False])
def test_validate_structure__keys_not_in_section(
    zuliprc_factory: ZuliprcFactoryT, with_api_section_present: bool
) -> None:
    api_section: Optional[Dict[str, str]] = {} if with_api_section_present else None
    zuliprc_path = zuliprc_factory(api=api_section, config=None, leading={"key": "x"})
    zuliprc_file = ZuliprcFile(zuliprc_path)
    assert zuliprc_file.validate_structure() == [
        "No section header found in file (eg. [api])"
    ]


def test_validate_structure__parse_error(
    zuliprc_factory: ZuliprcFactoryT,
) -> None:
    zuliprc_path = zuliprc_factory(api={"": ""}, config=None)
    zuliprc_file = ZuliprcFile(zuliprc_path)
    assert zuliprc_file.validate_structure() == ["Could not parse file"]


@pytest.mark.parametrize(
    "api, expected_errors",
    [
        (None, {"No [api] section in file"}),
        ({"email": "", "key": ""}, {"No 'site' key in [api] section"}),
        ({"email": "", "site": ""}, {"No 'key' key in [api] section"}),
        ({"key": "", "site": ""}, {"No 'email' key in [api] section"}),
        (
            {"key": ""},
            {"No 'email' key in [api] section", "No 'site' key in [api] section"},
        ),
        (
            {"email": ""},
            {"No 'key' key in [api] section", "No 'site' key in [api] section"},
        ),
        (
            {"site": ""},
            {"No 'key' key in [api] section", "No 'email' key in [api] section"},
        ),
        (
            {},
            {
                "No 'key' key in [api] section",
                "No 'email' key in [api] section",
                "No 'site' key in [api] section",
            },
        ),
    ],
)
def test_validate_structure__api_section_invalid(
    zuliprc_factory: ZuliprcFactoryT,
    api: Optional[Dict[str, str]],
    expected_errors: Set[str],
) -> None:
    zuliprc_path = zuliprc_factory(api=api, config=None)
    zuliprc_file = ZuliprcFile(zuliprc_path)
    assert set(zuliprc_file.validate_structure()) == expected_errors
