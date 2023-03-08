import stat

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


@pytest.mark.parametrize(
    "mode",
    [
        # Avoid reformatting to retain readability of grid of values
        # fmt:off
        0o77, 0o70, 0o07,
        0o66, 0o60, 0o06,
        0o55, 0o50, 0o05,
        0o44, 0o40, 0o04,
        0o33, 0o30, 0o03,
        0o22, 0o20, 0o02,
        0o11, 0o10, 0o01,
        # fmt:on
    ],
)
def test_security_issues_present__return_current_permissions_str(
    zuliprc_factory: ZuliprcFactoryT,
    mode: int,
) -> None:
    zuliprc_path = zuliprc_factory(api=None, config=None, mode=mode + 0o600)
    zuliprc_file = ZuliprcFile(zuliprc_path)

    expected_text = stat.filemode(zuliprc_path.stat().st_mode)
    assert zuliprc_file.security_issues_present() == expected_text
