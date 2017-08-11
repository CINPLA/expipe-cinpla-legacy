import exdir
import csv
import quantities as pq
import numpy as np
import os.path as op
import os
import warnings
import glob
from expipe_io_neuro import pyopenephys
import shutil
from datetime import datetime


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
    assert grating_off[-1] < grating_on[-1], 'Inconsistency, code needs revision'
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


def read_xml(path):
    from xmljson import yahoo as yh
    from xml.etree.ElementTree import fromstring
    with open(op.join(path)) as f:
        xmldata = f.read()
        data = yh.data(fromstring(xmldata))
    return data


def list_dict_get(list_dict, name):
    assert isinstance(list_dict, list)
    result = [val['val'] for val in list_dict if val['name'] == name]
    if len(result) == 1:
        return result[0]
    elif len(result) == 0:
        return
    else:
        raise ValueError('unable to get "' + name + '"')



if __name__ == '__main__':
    exdir_path = '/media/norstore/server/malin_cobra/1871-200717-03/main.exdir'
    psyexp_path = '/home/mikkel/Dropbox/scripting/python/expipe/psychopy/psychopymalinegen/testMil.psyexp'
    parse_psychopy_openephys(exdir_path, psyexp_path, 7)
