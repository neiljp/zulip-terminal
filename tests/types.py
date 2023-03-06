from pathlib import Path
from typing import Dict, Optional, Protocol


class ZuliprcFactoryT(Protocol):
    def __call__(
        self,
        *,
        api: Optional[Dict[str, str]],
        config: Optional[Dict[str, str]],
        leading: Optional[Dict[str, str]] = None,
        mode: int = 0o600,
    ) -> Path:
        ...
