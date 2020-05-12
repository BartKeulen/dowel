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
        
        self._tmpdir = tempfile.TemporaryDirectory()
        self._tmpdir_path = Path(self._tmpdir.name)
        self._tmpfiles = {}
        self._compressed = compressed

        self._fieldnames = None
        self._shapes = {}

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
                    # Store shape of array
                    if isinstance(val, np.ndarray):
                        self._shapes[key] = val.shape

                    # Open .npy file
                    fp = open(self._tmpdir_path / '{}.npy'.format(key), 'w')
                    self._tmpfiles[key] = fp

                    # Write header
                    header_dict = np.lib.format.header_data_from_array_1_0(val) 
                    np.lib.format._write_array_header(fp, header_dict, None)


            if set(to_dict.keys()) != self._fieldnames:
                self.close()
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

                if isinstance(val, np.ndarray) and self._shapes[key] != val.shape:
                    self.close()
                    raise ValueError(
                        "Wrong shape for key: '{}'. Got {}, but should be {}".format(
                            key, val.shape, self._data[key][0].shape
                        )
                    )

                self._write_array(key, val)

            for k in to_dict.keys():
                data.mark(k)
        else:
            raise ValueError("Unacceptable type.")

    def _write_array(self, key, array):
        if array.itemsize == 0:
            buffersize = 0
        else:
            # Set buffer size to 16 MiB to hide the Python loop overhead.
            buffersize = max(16 * 1024 ** 2 // array.itemsize, 1)

        fp = self._tmpfiles[key]
        if array.flags.f_contiguous and not array.flags.c_contiguous:
            order = 'F'
        else:
            order = 'C'

        for chunk in numpy.nditer(
                array, flags=['external_loop', 'buffered', 'zerosize_ok'],
                buffersize=buffersize, order=order):
            fp.write(chunk.tobytes('C'))

    def close(self):
        for f in self._tmpfiles:
            if not f.closed:
                f.close()

    def dump(self, step=None):
        """Dump the contents of this output.
        
        :param step: The current run step.
        """
        if self._compressed:
            np.savez_compressed(self._file_path, **self._data)
        else:
            np.savez(self._file_path, **self._data)
