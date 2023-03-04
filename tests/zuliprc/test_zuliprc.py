from tests.types import ZuliprcFactoryT
from zulipterminal.zuliprc import ZuliprcFile


def test_init__with_path(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(api=None, config=None)
    ZuliprcFile(zuliprc_path)


def test_init__with_string(zuliprc_factory: ZuliprcFactoryT) -> None:
    zuliprc_path = zuliprc_factory(api=None, config=None)
    ZuliprcFile(str(zuliprc_path))
