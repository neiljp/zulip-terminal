"""
Defines ZuliprcFile class to work with zuliprc files (holding login details & settings)
"""
import configparser
import stat
from pathlib import Path
from typing import List, Optional, Union


class ZuliprcFile:
    def __init__(self, zuliprc_path: Union[str, Path]) -> None:
        """Initialize with the path to the zuliprc file to work with."""
        self._zuliprc_path: Path = Path(zuliprc_path)

    def security_issues_present(self) -> Optional[str]:
        """Return security issues present as permissions, or None otherwise."""
        mode = self._zuliprc_path.stat().st_mode
        is_readable_by_group_or_others = mode & (stat.S_IRWXG | stat.S_IRWXO)
        if is_readable_by_group_or_others:
            return stat.filemode(mode)
        return None

    def validate_structure(self) -> List[str]:
        """Returns list of any errors detected in file as strings"""
        config = configparser.ConfigParser()
        try:
            files_read = config.read([self._zuliprc_path])
        except configparser.MissingSectionHeaderError:
            return ["No section header found in file (eg. [api])"]
        except configparser.ParsingError:
            return ["Could not parse file"]
        except configparser.DuplicateOptionError as exc:
            return [f"Duplicate keys in [{exc.section}] section"]
        if len(files_read) == 0:
            return [f"Failed to load '{self._zuliprc_path}'"]
        if not config.has_section("api"):
            return ["No [api] section in file"]
        api_section = config["api"]
        errors = []
        for key in ["site", "key", "email"]:
            if key not in api_section:
                errors.append(f"No '{key}' key in [api] section")
        return errors
