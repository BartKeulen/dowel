"""A `dowel.logger.LogOutput` for Numpy npz files."""
import warnings
from pathlib import Path

from dowel import TabularInput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize

import numpy as np

class NpzOutput(FileOutput):
    """Numpy npz file output for logger.
    
    :param file_name:    The file this output should log to.
                           requires .npz suffix, automatically appended when omitted.
    :param save_n_steps: Save to file every n steps
    """
    
    def __init__(self, file_name, save_n_steps=1):
        file_path = Path(file_name)
        if file_path.suffix == '':
            file_path = file_path.with_suffix('.npz')
        assert file_path.suffix == '.npz'
        super(NpzOutput, self).__init__(file_path, 'wb')
        
        self._fieldnames = None
        self._shapes = {}
        self._data = {}
        self._save_n_steps = save_n_steps
        self._step = 0
        
    @property
    def types_accepted(self):
        return (TabularInput)
    
    def record(self, data, prefix=''):
        """Log tabular data to npz."""
        if isinstance(data, TabularInput):
            to_dict = data.as_dict
            
            if not to_dict.keys():
                return
            
            if not self._fieldnames:
                self._fieldnames = set(to_dict.keys())
                for key, val in to_dict.items():
                    self._data[key] = []
                    self._shapes[key] = val.shape if isinstance(val, np.ndarray) else None
                
            if set(to_dict.keys()) != self._fieldnames:
                raise ValueError('Inconsistent TabularInput keys detected. '
                                 'NpzOutput keys: {}. '
                                 'TabularInput keys: {}. '
                                 'Did you change key sets after your first '
                                 'logger.log(TabularInput)?'.format(
                                   set(self._fieldnames), set(to_dict.keys())))
            
            for key in self._fieldnames:
                val = to_dict[key]
                if self._shapes[key] is not None and val.shape != self._shapes[key]:
                    raise ValueError('Wrong shape for key: \'{}\'. Got {}, but should be {}'
                                     .format(key, val.shape, self._shapes[key]))
                self._data[key].append(to_dict[key])
            
            if self._step == 0:
                np.savez(self._log_file, **self._data)
            
            self._step = (self._step + 1) % self._save_n_steps
            
            for k in to_dict.keys():
                data.mark(k)
        else:
            raise ValueError('Unacceptable type.')
                
    def _warn(self, msg):
        """Warns the user using warnings.warn.
        The stacklevel parameter needs to be 3 to ensure the call to logger.log
        is the one printed.
        """
        if not self._disable_warnings and msg not in self._warned_once:
            warnings.warn(
                colorize(msg, 'yellow'), NpzOutputWarning, stacklevel=3)
        self._warned_once.add(msg)
        return msg
    
    def disable_warnings(self):
        """Disable logger warnings for testing."""
        self._disable_warnings = True
        
        
class NpzOutputWarning(UserWarning):
    """Warning class for NpzOutput."""

    pass