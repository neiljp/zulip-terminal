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
    result = zuliprc_file.security_issues_present()  # type: ignore[func-returns-value]
    assert result is None
