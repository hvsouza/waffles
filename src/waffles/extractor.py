from hdf5libs import HDF5RawDataFile

import daqdataformats
import detdataformats
from daqdataformats import FragmentType
from rawdatautils.unpack.daphne import *

import click
import numpy as np
import os
from rich.progress  import track
from uproot import recreate as rc

def find_endpoint(map_id, target_value):
    for key, value_list in map_id.items():
        if target_value in value_list:
            return key

def extract_fragment_info(frag):
    frag_id = str(frag).split(' ')[3][:-1]
    fragType = frag.get_header().fragment_type
    
    if fragType == FragmentType.kDAPHNE.value:  # For self trigger
        trigger = 'self_trigger'
        timestamps = np_array_timestamp(frag)
        adcs = np_array_adc(frag)
        channels = np_array_channels(frag)
    elif fragType == 13:  # For full_stream
        trigger = 'full_stream'
        timestamps = np_array_timestamp_stream(frag)
        adcs = np_array_adc_stream(frag)
        channels = np_array_channels_stream(frag)[0]
    
    return trigger, frag_id, channels, adcs, timestamps

@click.command()
@click.option("--path", '-p', default = '/eos/experiment/neutplatform/protodune/experiments/ProtoDUNE-II/PDS_Commissioning/waffles/', help="Insert the run number, ex: 026102")
@click.option("--run" , '-r', default = None, help="Insert the run number, ex: 026102")

def main(path, run):
    
    ## Check if the run number is provided ##
    if run is None: 
        print("\033[35mPlease provide a run(s) number(s) to be analysed, separated by commas:)\033[0m")
        run = [int(input("Run(s) number(s): "))]
    if len(run)!=1: runs_list = list(map(int, list(run.split(","))))
    else: runs_list = run

    map_id = {'104': [1, 2, 3, 4], '105': [5, 6, 7, 8], '107': [9, 10], '109': [11], '111': [12], '112': [13], '113': [14]}
    for run in runs_list:
        run = str(run).zfill(6) # check if run have 6 digits and fill with zeros if not
        det         = 'HD_PDS'
        run_path    = f'{path}/1_rucio_paths/{run}.txt'
        path_root   = f'{path}/2_daq_root/run_{run}'
        os.mkdir(path_root)
        
        with open(f'{run_path}', "r") as run_list:
            run_paths = run_list.readlines()
        files = [run_path.rstrip('\n') for run_path in run_paths]
        
        for raw_file in files:
            # print(f'Reading {raw_file}...')
            h5_file   = HDF5RawDataFile(raw_file)
            run_id    = raw_file.split('_')[3]
            root_file = rc(f'{path_root}/{run}_{run_id}.root')
            records   = h5_file.get_all_record_ids()
            tr_ref    = None
            
            # Iterate through records 
            for r in track(records, description=f'Dumping {raw_file.split("/")[-1]} ...'):     
                pds_geo_ids = list(h5_file.get_geo_ids_for_subdetector(r, detdataformats.DetID.string_to_subdetector(det)))
                
                # Iterate through geo_ids
                for gid in pds_geo_ids:
                    frag = h5_file.get_frag(r, gid)
                    
                    tr_header = frag.get_header().trigger_timestamp
                    scr_id    = frag.get_header().element_id.id

                    # Filtering data with different timestamp on the header
                    if tr_header != tr_ref:
            
                        trigger, frag_id, channels, adcs, timestamps = extract_fragment_info(frag)
                        
                        endpoint = int(find_endpoint(map_id, scr_id))
                        channels = 100*int(endpoint) + channels   

                        if trigger == 'full_stream': adcs = adcs.transpose()
                    
                        if tr_ref is None:
                            root_file[f'waveform_primitive']       = ({'channel': channels,'adcs': np.array(adcs)})
                            root_file[f'timestamps']               = ({'timestamps': timestamps})
                        else:
                            root_file[f'waveform_primitive'].extend({'channel': channels,'adcs': np.array(adcs)})
                            root_file[f'timestamps'].extend ({'timestamps': timestamps})            
                            
                    tr_ref = tr_header
                    
if __name__ == "__main__":
    main()
