import expipe.io
import os
import os.path as op
import shutil
import json
import numpy as np
import exdir
import quantities as pq
import argparse
from datetime import datetime
import expipe
import platform
from .action_tools import generate_templates
from expipe_io_neuro import pyopenephys
import glob
import sys; sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use ' +
          '"expipe copy-to-config expipe_params.py"')
else:
    from expipe_params import USER_PARAMS


def generate_axona_opto(exdir_path, io_channel=8, **annotations):
    exdir_object = exdir.File(exdir_path)
    session = exdir_object['acquisition'].attrs['axona_session']
    param = extract_laser_pulse(op.join(str(exdir_object['acquisition'].directory),
                                        session))
    if annotations:
        param.update(annotations)
    # get the data
    elphys = exdir_object['processing']['electrophysiology']
    group = elphys['channel_group_{}'.format(io_channel)]
    timeseries = group['EventWaveform']['waveform_timeseries']
    times = pq.Quantity(timeseries['timestamps'].data,
                        timeseries['timestamps'].attrs['unit'])
    durations = pq.Quantity(np.array([param['pulse_phasedur']] * len(times)),
                            param['pulse_phasedur'].units)
    generate_epochs(exdir_path=exdir_path, times=times, durations=durations,
                    start_time=timeseries.attrs['start_time'],
                    stop_time=timeseries.attrs['stop_time'])
    return param


def generate_openephys_opto(exdir_path, io_channel, **attrs):
    exdir_object = exdir.File(exdir_path)
    session = exdir_object['acquisition'].attrs['openephys_session']
    openephys_path = op.join(str(exdir_object['acquisition'].directory), session)
    param = extract_laser_pulse(openephys_path)
    openephys_file = pyopenephys.File(openephys_path)
    if attrs:
        param.update(attrs)
    times = openephys_file.digital_in_signals[0].times[io_channel]
    if len(times) == 0:
        raise ValueError('No recorded TTL signals on io channel ' +
                         str(io_channel))
    durations = pq.Quantity(np.array([param['pulse_phasedur']] * len(times)),
                            param['pulse_phasedur'].units)
    generate_epochs(exdir_path=exdir_path, times=times, durations=durations,
                    start_time=0 * pq.s,
                    stop_time=openephys_file.duration)
    return param


def populate_modules(action, params):
    name = [n for n in action.modules.keys() if 'pulse_pal_settings' in n]
    assert len(name) == 1
    name = name[0]
    pulse_dict = action.require_module(name=name).to_dict()
    pulse_dict['stimulus_file_url']['value'] = '/'.join(params['pulse_url'].split('/')[4:])
    pulse_dict['pulse_period'] = params['pulse_period']
    pulse_dict['pulse_phase_duration'] = params['pulse_phasedur']
    pulse_dict['pulse_frequency'] = params['pulse_freq']
    pulse_dict['trigger_software']['value'] = params['trigger_software']
    action.require_module(name=name, contents=pulse_dict,
                          overwrite=True)

    name = [n for n in action.modules.keys() if 'laser_settings' in n]
    assert len(name) == 1
    name = name[0]
    laser_dict = action.require_module(name=name).to_dict()
    laser_dict['intensity_file_url']['value'] = '/'.join(params['laser_url'].split('/')[4:])
    laser_mask = params['laser_intensity'] > .1 * pq.mW
    avg = params['laser_intensity'][laser_mask].mean().rescale('mW')
    std = params['laser_intensity'][laser_mask].std().rescale('mW')
    laser_dict['intensity'] = pq.UncertainQuantity(avg, uncertainty=std)
    timestring = datetime.strftime(params['laser_dtime'],
                                   expipe.io.core.datetime_format)
    laser_dict['intensity_date_time']['value'] = timestring
    laser_dict['intensity_info']['value'] = params['laser_info']
    action.require_module(name=name, contents=laser_dict, overwrite=True)

    name = [n for n in action.modules.keys()
            if 'optogenetics_anatomical_location' in n]
    assert len(name) == 1
    name = name[0]
    loc_mod = action.require_module(name=name)
    loc_dict = loc_mod.to_dict()
    loc_dict['location']['value'] = params['location']
    action.require_module(name=name, contents=loc_dict, overwrite=True)

    name = [n for n in action.modules.keys() if 'optogenetics_paradigm' in n]
    assert len(name) == 1
    name = name[0]
    paradigm = action.require_module(name=name).to_dict()
    if params['trigger_software'].lower() == 'openephys': # TODO what if we start using other stim in oe
        paradigm['stimulus_type']['value'] = 'positional'
    if params['trigger_software'].lower() == 'matlab':
        paradigm['stimulus_type']['value'] = 'train'
    action.require_module(name=name, contents=paradigm, overwrite=True)


def extract_laser_pulse(acquisition_directory):
    paths = glob.glob(op.join(acquisition_directory, 'PulsePalProgram*'))
    if len(paths) == 0:
        raise ValueError('No Pulse Pal program found.')
    if len(paths) > 1:
        raise ValueError('Multiple Pulse Pal programs found.')
    pulsepalpath = paths[0]
    # laserpath
    paths = glob.glob(op.join(acquisition_directory, 'PM100*'))
    if len(paths) == 0:
        raise ValueError('No laser intensity file found.')
    if len(paths) > 1:
        raise ValueError('Multiple laser intensity files found.')
    pm100path = paths[0]
    # load data
    par = {}
    if pulsepalpath.endswith('.xml'):
        xml_par = read_pulse_pal_xml(pulsepalpath)['CHANNELS']
        par['pulse_phasedur'] = float(xml_par['Chan_1']['phase'][0]) * pq.ms
        par['pulse_freq'] = float(xml_par['Chan_1']['freq'][0]) * pq.Hz
        par['pulse_period'] = 1 / par['pulse_freq']
        par['pulse_traindur'] = ""
        par['trigger_software'] = "OpenEphys"
    elif pulsepalpath.endswith('.mat'):
        mat_par, _ = read_pulse_pal_mat(pulsepalpath)
        par['pulse_phasedur'] = float(mat_par['Phase1Duration']['Channel 1'][0]) * pq.s
        par['pulse_period'] = float(mat_par['Inter-pulse Interval']['Channel 1'][0]) * pq.s
        par['pulse_freq'] = 1 / par['pulse_period']
        par['pulse_traindur'] = float(mat_par['Stimulus Train Duration']['Channel 1'][0]) *pq.s
        par['trigger_software'] = "MATLAB"
    par['pulse_url'] = pulsepalpath
    intensity, dtime, device_info = read_laser_intensity(pm100path)
    par['laser_intensity'] = intensity
    par['laser_dtime'] = dtime
    par['laser_info'] = device_info
    par['laser_url'] = pm100path
    return par


def generate_epochs(exdir_path, times, durations, **annotations):
    exdir_object = exdir.File(exdir_path)
    group = exdir_object.require_group('epochs')
    epo_group = group.require_group('Optogenetics')
    epo_group.attrs['num_samples'] = len(times)
    dset = epo_group.require_dataset('timestamps', data=times)
    dset.attrs['num_samples'] = len(times)
    dset = epo_group.require_dataset('durations', data=durations)
    dset.attrs['num_samples'] = len(durations)
    attrs = epo_group.attrs.to_dict()
    if annotations:
        attrs.update(annotations)
    epo_group.attrs = attrs


def is_num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def read_laser_intensity(fname):
    '''
    reads laser intensity from thor labs PM100D
    '''
    import csv
    import numpy as np
    import quantities as pq
    pq_symbols = [foo.symbol for _, foo in pq.units.__dict__.items()
                  if isinstance(foo, pq.Quantity)]
    data = []
    units = []
    device_info = []
    with open(fname) as tsv:
        for idx, line in enumerate(csv.reader(tsv, dialect="excel-tab")):
            if len(line) > 2:
                if is_num(line[1].replace(',', '.')) and line[2] in pq_symbols:
                    units.append(line[2])
                    data.append(float(line[1].replace(',', '.')))
            else:
                device_info.extend(line)
    assert np.array_equal(np.array(units), np.array(units))
    data = pq.Quantity(data, units[0])
    dtime = datetime.strptime(line[0][:19], '%d.%m.%Y %H:%M:%S')
    device_info = ' '.join(info for info in device_info)
    return data, dtime, device_info


def read_pulse_pal_xml(fname):
    '''
    reads pulse duration, period and position from spatial stimulation gui
    in Open Ephys
    '''
    import xml.etree.ElementTree as ET
    from xmljson import yahoo as yh
    with open(fname) as f:
        xmldata = f.read()
    return yh.data(ET.fromstring(xmldata))['TRACKERSTIMULATOR']


def read_pulse_pal_mat(fname):
    '''
    reads pulse duration, and period from settings .mat file from matlab
    gui of Pulse Pal
    '''
    import scipy.io
    mat = scipy.io.loadmat(fname)
    par = mat['ParameterMatrix']
    output_params = {name[0][0]: dict() for name in par[1:]}
    trigger_params = {name[6][0]: dict() for name in par if name[6].size > 0}

    for i, row in enumerate(par[1:]):
        for j, col in enumerate(row[:]):
            chan_val = col
            chan = par[0][j]
            if j < 5:
                name = row[0]
                output_params[name[0]][chan[0]] = chan_val[0]
            elif j > 6:
                name = row[6]
                if name.size > 0:
                    trigger_params[name[0]][chan[0]] = chan_val[0]
    return output_params, trigger_params
