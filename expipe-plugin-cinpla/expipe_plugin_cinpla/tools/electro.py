from expipe_plugin_cinpla.imports import *


def generate_epochs(exdir_path, triggers, trigger_params, channel_params, stim_signals, **annotations):
    exdir_object = exdir.File(exdir_path)
    group = exdir_object.require_group('epochs')
    epo_group = group.require_group('ElectricalStimulation')
    epo_group.attrs['num_samples'] = len(triggers)
    epo_group.attrs['active-electrodes'] = channel_params['active-electrodes']
    epo_group.attrs['trigger_params'] = trigger_params
    dset = epo_group.require_dataset('timestamps', data=triggers)
    dset.attrs['num_samples'] = len(triggers)
    dset = epo_group.require_dataset('stimulus', data=stim_signals)
    for i, ch in enumerate(channel_params['active-electrodes']):
        attr = dict()
        attr['amplitudes'] = channel_params['amplitudes'][i]
        attr['phases'] = channel_params['phases'][i]
        dset.attrs['electrode'+str(ch)] = attr
    attrs = epo_group.attrs.to_dict()
    if annotations:
        attrs.update(annotations)
    epo_group.attrs = attrs


def populate_modules(action, params):
    name = [n for n in action.modules.keys() if 'pulse_pal_settings' in n]
    assert len(name) == 1
    name = name[0]
    pulse_dict = action.require_module(name=name).to_dict()

    pulse_dict['pulse_period'] = int(params['pulsepal-info']['phase'])*pq.ms.rescale('s')
    pulse_dict['pulse_phase_duration'] = int(params['pulsepal-info']['trainduration'])*pq.ms.rescale('s')
    pulse_dict['pulse_repetitions'] = int(params['pulsepal-info']['repetitions'])
    pulse_dict['pulse_frequency'] = float(params['pulsepal-info']['freq'])*pq.Hz
    pulse_dict['pulse_sd'] = float(params['pulsepal-info']['sd'])
    pulse_dict['pulse_voltage'] = float(params['pulsepal-info']['voltage'])*pq.V
    pulse_dict['uniform-gaussian'] = bool(params['pulsepal-info']['uniform-gaussian'])
    pulse_dict['trigger_software']['value'] = 'Openephys'
    action.require_module(name=name, contents=pulse_dict,
                          overwrite=True)

    name = [n for n in action.modules.keys() if 'electrical_stimulation' in n]
    assert len(name) == 1
    name = name[0]
    elec_dict = action.require_module(name=name).to_dict()
    elec_dict['active-electrodes'] = params['active-electrodes']
    elec_dict['intensity']['value'] = dict()
    elec_dict['phase']['value'] = dict()
    elec_dict['intensity']['value'].update(params['amplitudes'])
    elec_dict['phase']['value'].update(params['phases'])
    action.require_module(name=name, contents=elec_dict,
                          overwrite=True)

    name = [n for n in action.modules.keys() if 'positions' in n]
    assert len(name) == 1
    name = name[0]
    pos_dict = action.require_module(name=name).to_dict()
    pos_dict['circles'] = params['circles-info']
    action.require_module(name=name, contents=pos_dict,
                          overwrite=True)


def generate_electrical_info(exdir_path, intan_file, openephys_file, stim_chan, stim_trigger='dig'):
    trigger_param = dict()

    if stim_trigger == 'dig':
        triggers = intan_file.digital_in_signals[0].times[stim_chan]
    elif stim_trigger == 'adc':
        triggers = pyintan.extract_sync_times(intan_file.adc_signals[0].signal[stim_chan],
                                                                      intan_file.times)
    else:
        raise ValueError('Unsupported trigger modality: adc or dig only')
    if len(triggers) == 0:
        raise ValueError('No recorded TTL signals on io channel ' +
                         str(stim_chan))

    trigger_param['intan-chan'] = stim_chan
    trigger_param['intan-mod'] = stim_trigger

    if openephys_file.track_stim:
        trigger_param['pulsepal-chan'] = openephys_file.track_stimInfo['output']['channel']
        chan = 'Chan_' + str(int(openephys_file.track_stimInfo['output']['channel']) + 1)
        trigger_param['pulsepal-info'] = openephys_file.track_stimInfo['channels'][chan]
        trigger_param['circles-info'] = openephys_file.track_stimInfo['circles']
        trigger_param['frequency'] = openephys_file.track_stimInfo['channels'][chan]['freq']

    if len(intan_file.stimulation[0].stim_signal) != 0:
        stim_chan = intan_file.stimulation[0].stim_channels
        stim_signals = intan_file.stimulation[0].stim_signal * pq.uA
    else:
        raise ModuleNotFoundError('Stimulation info is missing')

    channel_param=dict()
    channel_param['active-electrodes'] = stim_chan
    stim_wave, curr, phase = sig_tools.extract_stimulation_waveform(stim_signals, triggers, intan_file.times)

    channel_param['amplitudes'] = curr
    channel_param['phases'] = phase

    generate_epochs(exdir_path=exdir_path,
                    triggers=triggers,
                    trigger_params=trigger_param,
                    channel_params=channel_param,
                    stim_signals=stim_wave,
                    start_time=0 * pq.s,
                    stop_time=intan_file.duration)

    channel_param['amplitudes'] = dict()
    channel_param['phases'] = dict()
    for i, ch in enumerate(channel_param['active-electrodes']):
        channel_param['amplitudes'][str(i)] = curr[i]
        channel_param['phases'][str(i)] = phase[i]

    return trigger_param, channel_param
