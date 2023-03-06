"""
Defines ZuliprcFile class to work with zuliprc files (holding login details & settings)
"""
from pathlib import Path
from typing import Union


class ZuliprcFile:
    def __init__(self, zuliprc_path: Union[str, Path]) -> None:
        """Initialize with the path to the zuliprc file to work with."""
        self._zuliprc_path: Path = Path(zuliprc_path)

    def security_issues_present(self) -> None:
        """Determine if any security issues are present."""
        return None
