"""A `dowel.logger.LogOutput` for Numpy npz files."""
import warnings
from pathlib import Path

from dowel import TabularInput
from dowel.logger import LogOutput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize

import numpy as np


class NpzOutput(LogOutput):
    """Numpy npz file output for logger.

    Standard numpy arrays are saved uncompressed. To save disk space `np.savez_compressed` can be used. Note however that this is computationally more intensive.
    
    :param file_name:    The file this output should log to (requires .npz suffix, automatically appended when omitted).
    :param compressed:   Use `np.savez_compressed or `np.savez` (default)
    """

    def __init__(self, file_name, compressed=False):
        file_path = Path(file_name)
        if file_path.suffix == "":
            file_path = file_path.with_suffix(".npz")
        assert file_path.suffix == ".npz"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        self._file_path = file_path
        
        self._fieldnames = None
        self._shapes = {}
        self._data = {}
        self._compressed = compressed

    @property
    def types_accepted(self):
        return TabularInput

    def record(self, data, prefix=""):
        """Log tabular data to npz."""
        if isinstance(data, TabularInput):
            to_dict = data.as_dict

            if not to_dict.keys():
                return

            if not self._fieldnames:
                self._fieldnames = set(to_dict.keys())
                for key, val in to_dict.items():
                    self._data[key] = []
                    self._shapes[key] = (
                        val.shape if isinstance(val, np.ndarray) else None
                    )

            if set(to_dict.keys()) != self._fieldnames:
                raise ValueError(
                    "Inconsistent TabularInput keys detected. "
                    "NpzOutput keys: {}. "
                    "TabularInput keys: {}. "
                    "Did you change key sets after your first "
                    "logger.log(TabularInput)?".format(
                        set(self._fieldnames), set(to_dict.keys())
                    )
                )

            for key in self._fieldnames:
                val = to_dict[key]
                if (
                    self._shapes[key] is not None
                    and val.shape != self._shapes[key]
                ):
                    raise ValueError(
                        "Wrong shape for key: '{}'. Got {}, but should be {}".format(
                            key, val.shape, self._shapes[key]
                        )
                    )
                self._data[key].append(to_dict[key])

            for k in to_dict.keys():
                data.mark(k)
        else:
            raise ValueError("Unacceptable type.")

    def dump(self, step=None):
        """Dump the contents of this output.
        
        :param step: The current run step.
        """
        if self._compressed:
            np.savez_compressed(self._file_path, **self._data)
        else:
            np.savez(self._file_path, **self._data)
