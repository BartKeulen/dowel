"""A `dowel.logger.LogOutput` for Numpy npz files."""
import warnings
from pathlib import Path
import zipfile
import tempfile

from dowel import TabularInput
from dowel.logger import LogOutput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize

import numpy as np
try:
    import torch
except ImportError:
    torch = None
try:
    import tensorflow as tf
except ImportError:
    tf = None

"""TODO

File handling is not done properly, system can quickly throw an error that to many files are open.
Implement system underlying numpy savez system and store data incrementally:

  - Write each numpy array (incrementally?) to a `.npy` tempfile.
  - During dumping, current `.npy` files are written to the desired `.npz` file.

This means that for N numpy arrays there will be N+1 file objects.

Incrementally writing might be done using numpy.nditer. May need to wrap current appended val in an extra dimension, 
such that final array is [val, val, val]. See:
  
  https://github.com/numpy/numpy/blob/91118b3363b636f932f7ff6748d8259e9eb2c23a/numpy/lib/format.py#L677
"""

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
        
        # self._tmpdir = tempfile.TemporaryDirectory()
        # self._tmpdir_path = Path(self._tmpdir.name)
        # self._tmpfiles = {}
        self._compressed = compressed

        self._fieldnames = None
        self._data = {}

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
                for key, val in sorted(to_dict.items()):
                    self._data[key] = []


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

                if torch and torch.is_tensor(val):
                    val = val.detach().numpy()
                    
                if tf and tf.is_tensor(val):
                    self.close()
                    raise NotImplementedError()

                if isinstance(val, np.ndarray) and len(self._data[key]) > 0 and self._data[key][0].shape != val.shape:
                    raise ValueError(
                        "Wrong shape for key: '{}'. Got {}, but should be {}".format(
                            key, val.shape, self._data[key][0].shape
                        )
                    )

                self._data[key].append(val)

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
