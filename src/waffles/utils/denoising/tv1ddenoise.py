import numpy as np
import ctypes
from tqdm import tqdm

from waffles.data_classes.WaveformSet import WaveformSet
from waffles.data_classes.Waveform import Waveform
import os



class Denoise:
    def __init__(self, npts = 0):
        dir_path = os.path.dirname(os.path.realpath(__file__))

        self.load_filter(dir_path)

        self.hasnptsset = False
        self.npts = npts
        if npts > 0:
            self.hasnptsset = True
            self.tv1filter.TV1D_denoise.restype = np.ctypeslib.ndpointer(dtype=np.float32, shape=(self.npts,))

        
    def apply_denoise(self, raw: Waveform.adcs, filter: float = 0) -> np.ndarray:
        if not self.hasnptsset:
            self.npts = len(raw)
            self.tv1filter.TV1D_denoise.restype = np.ctypeslib.ndpointer(dtype=np.float32, shape=(self.npts,))
        return self.tv1filter.TV1D_denoise(raw.astype(np.float32), self.npts, filter)

    def create_filtered_waveforms(self, wfset:WaveformSet, filter: float = 0, show_progress: bool = False):
        for i in tqdm(range(len(wfset.waveforms)), disable=not show_progress):
            wfset.waveforms[i].filtered = self.apply_denoise(wfset.waveforms[i].adcs, filter)


    def load_filter(self, dir_path:str):
        
        if not os.path.isfile(f'{dir_path}/tv1ddenoise.o'):
            if os.path.isfile(f'{dir_path}/tv1ddenoise.c'):
                print("Installing denoise...")
                os.system(f'g++ -shared {dir_path}/tv1ddenoise.c -o {dir_path}/tv1ddenoise.o')
            else:
                raise Exception(f"No tv1ddenoise.c found at {dir_path}")
                return

        self.tv1filter = ctypes.cdll.LoadLibrary(f"{dir_path}/tv1ddenoise.o")
        self.tv1filter.TV1D_denoise.argtypes = [ np.ctypeslib.ndpointer(dtype=np.float32), ctypes.c_int , ctypes.c_double ]

        

        











