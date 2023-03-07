import stat

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
