import exdir
import csv
import quantities as pq
import numpy as np
import os.path as op
import os
import warnings
import glob
from expipe_io_neuro import pyopenephys


def csv_to_dict(fname):
    assert fname.endswith('.csv')
    with open(fname, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row_n, row in enumerate(spamreader):
            if row_n == 0:
                keys = row
                out = {key: list() for key in keys}
                continue
            for col_n, col in enumerate(row):
                if col.isnumeric():
                    if '.' in col:
                        col = float(col)
                    else:
                        col = int(col)
                out[keys[col_n]].append(col)
    return out


def read_psychopy_log(logpath, return_dict=False):
    with open(logpath, 'r') as logfile:
        grating_on = []
        grating_off = []
        trials = {}
        num_trial = -1
        for line in logfile:
            contents = line.replace('\n', '').split('\t')
            time = float(contents[0].replace(' ', ''))
            text = contents[2]
            if 'New trial' in text:
                num_trial += 1
                trial_id = 'trial_{}'.format(num_trial)
                trials[trial_id] = {}
            if 'grating: ' in text:
                if 'autoDraw = True' in text:
                    trials[trial_id]['grating_on'] = time
                    grating_on.append(time)
                if 'autoDraw = False' in text:
                    trials[trial_id]['grating_off'] = time
                    grating_off.append(time)
    start_time = min(min(grating_on), min(grating_off)) * pq.s
    grating_on = sorted(set(grating_on)) * pq.s - start_time
    grating_off = sorted(set(grating_off)) * pq.s - start_time
    if len(grating_off) == len(grating_on) - 1:
        avg_dur = np.mean(grating_off - grating_on[:-1])
        final_off = round(grating_on[-1] + avg_dur, 4)
        grating_off = np.hstack((grating_off, final_off)).magnitude * pq.s
    elif len(grating_off) == len(grating_on):
        pass
    else:
        raise ValueError('Lengths of grating onset and blank screen do not match')
    durations = grating_off - grating_on
    med_dur = np.median(durations)
    if not all([abs(dur - med_dur) <= 0.1 for dur in durations]):
        warnings.warn('Uneven durations "{}"'.format(durations))

    if return_dict:
        return trials
    else:
        return grating_on, grating_off, durations



def parse_psychopy_openephys(exdir_path, io_channel):
    exdir_object = exdir.File(exdir_path)
    session = exdir_object['acquisition'].attrs['openephys_session']
    openephys_path = op.join(str(exdir_object['acquisition'].directory),
                             session)
    psycho_paths = glob.glob(op.join(openephys_path, '*_psychopy_*'))

    psycho_path = op.splitext(psycho_paths[0])[0]
    psycho_exts = [op.splitext(path)[-1] for path in psycho_paths]
    expected_exts = ['.log', '.csv', '.psydat']
    if not set(psycho_exts) == set(expected_exts):
        missing = [ext for ext in expected_exts if not ext in psycho_exts]
        raise ValueError('Missing file types "{}" in folder'.format(missing))
    csvdata = csv_to_dict(psycho_path + '.csv')
    stim_on, stim_off, durations = read_psychopy_log(psycho_path + '.log')
    if not len(stim_on) == len(csvdata['ori']):
        raise ValueError('Inconsistency in number of orientations and ' +
                         'stimulus onsets')
    csvdata['stim_on'] = stim_on
    csvdata['stim_off'] = stim_off
    csvdata['durations'] = durations
    openephys_file = pyopenephys.File(openephys_path)
    times = openephys_file.digital_in_signals[0].times[io_channel]
    if len(times) == 0:
        raise ValueError('No recorded TTL signals on io channel ' +
                         str(io_channel))
    rel_times = times - times[0]
    if not all(abs(psy_t - oe_t) < 0.01 for psy_t, oe_t in zip(stim_on, rel_times)):
        raise ValueError('Inconsistency in timestamps from psychopy and' +
                         ' timestamps from paralell port to open ephys.')
    print(stim_on)
    print(rel_times)
    generate_epochs(exdir_path=exdir_path, times=times, durations=durations,
                    name='Psychopy', start_time=0 * pq.s,
                    stop_time=openephys_file.duration)


def generate_epochs(exdir_path, times, durations, name, **annotations):
    exdir_object = exdir.File(exdir_path)
    group = exdir_object.require_group('epochs')
    epo_group = group.require_group(name)
    epo_group.attrs['num_samples'] = len(times)
    dset = epo_group.require_dataset('timestamps', data=times)
    dset.attrs['num_samples'] = len(times)
    dset = epo_group.require_dataset('durations', data=durations)
    dset.attrs['num_samples'] = len(durations)
    attrs = epo_group.attrs.to_dict()
    if annotations:
        attrs.update(annotations)
    epo_group.attrs = attrs


if __name__ == '__main__':
    exdir_path = '/home/mikkel/Dropbox/scripting/python/expipe/psychopy/Ephys_data/\
1871-200717-03/main.exdir'
    parse_psychopy_openephys(exdir_path, 7)
