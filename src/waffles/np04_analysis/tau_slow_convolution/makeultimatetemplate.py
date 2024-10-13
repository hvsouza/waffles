# IMPORT ALL THE LIBRARIES USED IN THE NOTEBOOK

from waffles.data_classes.WaveformSet import WaveformSet
from waffles.data_classes.Waveform import Waveform
from waffles.input.pickle_file_to_WaveformSet import pickle_file_to_WaveformSet
from extract_selection import Extractor
import argparse
import numpy as np
import pandas as pd
import pickle



class Filter:
    def __init__(self):
        self.is_first = True

    def get_only_one_wvf(self, waveform: Waveform) -> bool:
        if self.is_first:
            self.is_first = False
            return True
        else:
            return False
        return False
    
if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("-ch","--channels", type=int, nargs="+", help="List of channels", default=[11225])
    args = vars(parse.parse_args())
    channels = args['channels']

    filelist = f"/eos/home-h/hvieirad/waffles/analysis/runlists/purity_runs.csv"
    runnumbers = np.unique(pd.read_csv(filelist)["Run LED"].to_numpy())

    for ch in channels:
        allwvfs = []
        ft = Filter()
        wfout:WaveformSet = None
        for run in runnumbers:
            if run==29177:# and ch//100 == 112:
                continue
            print(f'run {run}', end=' ')
            wfset:WaveformSet
            try:
                wfset = pickle_file_to_WaveformSet(f"/eos/home-h/hvieirad/waffles/analysis/templates/template_run0{run}_ch{ch}.pkl")
            except:
                print('nope...')
                continue

            try:
                wfout = WaveformSet.from_filtered_WaveformSet( wfset, ft.get_only_one_wvf)
            except:
                pass
            first = False
            print(f'total: {len(wfset.waveforms)}')
            allwvfs += [(waveform.adcs.astype(np.float32) - waveform.baseline)*-1 for waveform in wfset.waveforms]

        allwvfs = np.array(allwvfs)
        print('Total waveforms for master template:', len(allwvfs))
        avgwvf = np.mean(allwvfs, axis=0)
        
        extractor = Extractor("template")
        extractor.baseliner.binsbase = np.linspace(-20,20,500)
        res0, status = extractor.baseliner.compute_baseline(avgwvf)
        avgwvf-=res0
        wfout.avgwvf = avgwvf
        wfout.nselected = len(allwvfs)
        print(f'\t {ch}: {len(allwvfs)}')
        pickleselecname = f'templates/template_run00_ch{ch}.pkl'
        pickleavgname = f'templates/template_run00_ch{ch}_avg.pkl'
        with open(pickleselecname, "wb") as f:
            pickle.dump(wfout, f)

        output = np.array([wfout.avgwvf, wfout.waveforms[0].timestamp, wfout.nselected], dtype=object)
        with open(pickleavgname, "wb") as f:
            pickle.dump(output, f)
        print('Saved... ')
