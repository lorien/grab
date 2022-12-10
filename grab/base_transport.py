import os
import tempfile
from abc import abstractmethod
from typing import Any, Optional

from .document import Document


class BaseTransport:
    def reset(self) -> None:
        pass

    def setup_body_file(
        self,
        storage_dir: str,
        storage_filename: Optional[str],
        create_dir: bool = False,
    ) -> str:
        if create_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        if storage_filename is None:
            file, file_path = tempfile.mkstemp(dir=storage_dir)
            os.close(file)
        else:
            file_path = os.path.join(storage_dir, storage_filename)
        return file_path  # noqa: R504

    @abstractmethod
    def prepare_response(self, grab_config: dict[str, Any]) -> Document:
        raise NotImplementedError
