import os
import os.path as op
import numpy as np
from datetime import datetime
import quantities as pq


def apply_CAR(anas, channels=None, car_type='mean', split_probe=None, copy_signal=True):
    """Removes noise by Common Average or Median Reference.

    Parameters
    ----------
    anas : np.array
           2d array of analog signals
    channels : list
               list of good channels to perform CAR/CMR with
    car_type : string
               'mean' or 'median'
    split_probe : int
                  splits anas into different probes to apply
                  car/cmr to each probe separately

    Returns
    -------
    anas_car : cleaned analog signals
    avg_ref : reference removed from signals
    """
    from copy import copy
    if channels is None:
        channels = np.arange(anas.shape[0])
    if copy_signal:
        anas_car = copy(anas)
    else:
        anas_car = anas
    anas_car = np.array(anas_car, dtype=np.float32)

    if car_type is 'mean':
        print('Applying CAR')
        if split_probe is not None:
            avg_ref = np.mean(anas_car[:split_probe], axis=0)
            anas_car[:split_probe] -= avg_ref
            avg_ref = np.mean(anas_car[split_probe:], axis=0)
            anas_car[split_probe:] -= avg_ref
        else:
            avg_ref = np.mean(anas_car[channels], axis=0)
            anas_car[channels] -= avg_ref
    elif car_type is 'median':
        print('Applying CMR')
        if split_probe is not None:
            avg_ref_1 = np.median(anas_car[:split_probe], axis=0)
            anas_car[:split_probe] -= avg_ref_1
            avg_ref_2 = np.median(anas_car[split_probe:], axis=0)
            anas_car[split_probe:] -= avg_ref_2
            avg_ref = np.array([avg_ref_1, avg_ref_2])
        else:
            avg_ref = np.median(anas_car[channels], axis=0)
            anas_car[channels] -= avg_ref
    else:
        raise AttributeError("'type must be 'mean' or 'median'")

    return anas_car, avg_ref


def ground_bad_channels(anas, bad_channels, copy_signal=True):
    """Grounds selected noisy channels.

    Parameters
    ----------
    anas : np.array
           2d array of analog signals
    bad_channels : list
                   list of channels to be grounded
    copy_signal : bool
                  copy signals or not

    Returns
    -------
    anas_zeros : analog signals with grounded channels
    """
    print('Grounding channels: ', bad_channels, '...')

    from copy import copy
    nsamples = anas.shape[1]
    if copy_signal:
        anas_zeros = copy(anas)
    else:
        anas_zeros = anas
    if type(bad_channels) is not list:
        bad_channels = [bad_channels]

    for i, ana in enumerate(anas_zeros):
        if i in bad_channels:
            anas_zeros[i] = np.zeros(nsamples)

    return anas_zeros


def duplicate_bad_channels(anas, bad_channels, probefile, copy_signal=True):
    """Duplicate selected noisy channels with channels in
    the same channel group.

    Parameters
    ----------
    anas : np.array
           2d array of analog signals
    bad_channels : list
                   list of channels to be grounded
    probefile : string
                absolute path to klusta-like probe file
    copy_signal : bool
                  copy signals or not

    Returns
    -------
    anas_dup : analog signals with duplicated channels
    """
    print('Duplicating good channels on channels: ', bad_channels, '...')

    def _select_rnd_chan_in_group(channel_map, ch_idx):
        for group_idx, group in channel_map.items():
            if ch_idx in group['channels']:
                gr = np.array(group['channels'])
                rnd_idx = np.random.choice(gr[gr != ch_idx])
                return rnd_idx

    def _read_python(path):
        from six import exec_
        path = op.realpath(op.expanduser(path))
        assert op.exists(path)
        with open(path, 'r') as f:
            contents = f.read()
        metadata = {}
        exec_(contents, {}, metadata)
        metadata = {k.lower(): v for (k, v) in metadata.items()}
        return metadata

    probefile_ch_mapping = _read_python(probefile)['channel_groups']

    from copy import copy
    nsamples = anas.shape[1]
    if copy_signal:
        anas_dup = copy(anas)
    else:
        anas_dup = anas
    if type(bad_channels) is not list:
        bad_channels = [bad_channels]

    for i, ana in enumerate(anas_dup):
        if i in bad_channels:
            rnd = _select_rnd_chan_in_group(probefile_ch_mapping, i)
            anas_dup[i] = anas[rnd]

    return anas_dup

def save_binary_format(filename, signal, spikesorter='klusta'):
    """Saves analog signals into klusta (time x chan) or spyking
    circus (chan x time) binary format (.dat)

    Parameters
    ----------
    filename : string
               absolute path (_klusta.dat or _spycircus.dat are appended)
    signal : np.array
             2d array of analog signals
    spikesorter : string
                  'klusta' or 'spykingcircus'

    Returns
    -------
    """
    if spikesorter is 'klusta':
        fdat = filename + '_klusta.dat'
        print('Saving ', fdat)
        with open(fdat, 'wb') as f:
            np.transpose(np.array(signal, dtype='float32')).tofile(f)
    elif spikesorter is 'spykingcircus':
        fdat = filename + '_spycircus.dat'
        print('Saving ', fdat)
        with open(fdat, 'wb') as f:
            np.array(signal, dtype='float32').tofile(f)


def create_klusta_prm(pathname, prb_path, nchan=32, fs=30000,
                      klusta_filter=True, filter_low=300, filter_high=6000):
    """Creates klusta .prm files, with spikesorting parameters

    Parameters
    ----------
    pathname : string
               absolute path (_klusta.dat or _spycircus.dat are appended)
    prbpath : np.array
              2d array of analog signals
    nchan : int
            number of channels
    fs: float
        sampling frequency
    klusta_filter : bool
        filter with klusta or not
    filter_low: float
                low cutoff frequency (if klusta_filter is True)
    filter_high : float
                  high cutoff frequency (if klusta_filter is True)
    Returns
    -------
    full_filename : absolute path of .prm file
    """
    assert pathname is not None
    abspath = op.abspath(pathname)
    assert prb_path is not None
    prb_path = op.abspath(prb_path)
    full_filename = abspath + '.prm'
    print('Saving ', full_filename)
    with open(full_filename, 'w') as f:
        f.write('\n')
        f.write('experiment_name = ' + "r'" + abspath + '_klusta' + "'" + '\n')
        f.write('prb_file = ' + "r'" + prb_path + "'")
        f.write('\n')
        f.write('\n')
        f.write("traces = dict(\n\traw_data_files=[experiment_name + '.dat'],\n\tvoltage_gain=1.,"
                "\n\tsample_rate="+str(fs)+",\n\tn_channels="+str(nchan)+",\n\tdtype='float32',\n)")
        f.write('\n')
        f.write('\n')
        f.write("spikedetekt = dict(")
        if klusta_filter:
            f.write("\n\tfilter_low="+str(filter_low)+",\n\tfilter_high="+str(filter_high)+","
                    "\n\tfilter_butter_order=3,\n\tfilter_lfp_low=0,\n\tfilter_lfp_high=300,\n")
        f.write("\n\tchunk_size_seconds=1,\n\tchunk_overlap_seconds=.015,\n"
                "\n\tn_excerpts=50,\n\texcerpt_size_seconds=1,"
                "\n\tthreshold_strong_std_factor=4.5,\n\tthreshold_weak_std_factor=2,\n\tdetect_spikes='negative',"
                "\n\n\tconnected_component_join_size=1,\n"
                "\n\textract_s_before=16,\n\textract_s_after=48,\n"
                "\n\tn_features_per_channel=3,\n\tpca_n_waveforms_max=10000,\n)")
        f.write('\n')
        f.write('\n')
        f.write("klustakwik2 = dict(\n\tnum_starting_clusters=50,\n)")
                # "\n\tnum_cpus=4,)")
    return full_filename
