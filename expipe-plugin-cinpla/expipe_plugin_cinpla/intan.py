import expipe
import expipe.io
import os
import os.path as op
from expipecli.utils import IPlugin
import click
from expipe_io_neuro import pyopenephys, openephys, pyintan, intan, axona
from .action_tools import generate_templates, _get_local_path, GIT_NOTE
from .signal_tools import (create_klusta_prm, save_binary_format, apply_CAR,
                           filter_analog_signals, ground_bad_channels,
                           remove_stimulation_artifacts, _get_probe_file)
import quantities as pq
import shutil
import sys
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import (user_params, templates, unit_info,
                               possible_locations)

DTIME_FORMAT = expipe.io.core.datetime_format


class IntanPlugin(IPlugin):
    """Create the `expipe parse-axona` command for neuro recordings."""
    def attach_to_cli(self, cli):
        @cli.command('klusta-intan')
        @click.argument('action-id', type=click.STRING)
        @click.option('--prb-path',
                      type=click.STRING,
                      help='Path to probefile, assumed to be in expipe config directory by default.',
                      )
        @click.option('--intan-fullpath',
                      type=click.STRING,
                      help='Path to dir, if none it is deduced from action id.',
                      )
        @click.option('--exdir-path',
                      type=click.STRING,
                      help='Path to desired exdir directory, if none it is deduced from action id.',
                      )
        @click.option('--nchan',
                      type=click.INT,
                      default=32,
                      help='Number of channels. Default = 32',
                      )
        @click.option('--klusta-filter',
                      is_flag=True,
                      help='Let klusta filter or not. Default = True',
                      )
        @click.option('--pre-filter',
                      is_flag=True,
                      help='Pre filter or not, replaces klusta filter. Default = False',
                      )
        @click.option('--filter-low',
                      type=click.INT,
                      default=300,
                      help='Low cut off frequencey. Default = 300 Hz',
                      )
        @click.option('--filter-high',
                      type=click.INT,
                      default=6000,
                      help='High cut off frequencey. Default = 6000 Hz',
                      )
        @click.option('--common-ref',
                      type=click.Choice(['car', 'cmr', 'none']),
                      default='none',
                      help='Apply Common average/median referencing. Default is none')
        @click.option('--split-probe',
                      type=click.INT,
                      default=None,
                      help='Splits referencing in 2 at selected channel (for CAR/CMR). Default is None',
                      )
        @click.option('--ground', '-g',
                      multiple=True,
                      help='Ground selected channels')
        @click.option('--run',
                      is_flag=True,
                      help='Run klusta on dataset.',
                      )
        @click.option('--convert',
                      is_flag=True,
                      help='Convert to exdir.',
                      )
        @click.option('--temp',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )

        def generate_klusta_intan(action_id, prb_path, pre_filter,
                                  klusta_filter, filter_low,
                                  filter_high, nchan, common_ref, ground,
                                  split_probe, run, temp, convert, intan_fullpath,
                                  exdir_path):
            """Generate an klusta dat and prm files from intan file.

            COMMAND: action-id"""
            import numpy as np
            if intan_fullpath is None:
                import exdir
                project = expipe.io.get_project(user_params['project_id'])
                action = project.require_action(action_id)
                fr = action.require_filerecord()
                if temp:
                    exdir_path = _get_local_path(fr)
                else:
                    exdir_path = fr.local_path
                exdir_file = exdir.File(exdir_path)
                acquisition = exdir_file["acquisition"]
                if acquisition.attrs['acquisition_system'] != 'OpenEphys' and acquisition.attrs['acquisition_system'] != 'Intan':
                    raise ValueError('No Open Ephys or Intan aquisition system ' +
                                     'related to this action')
                if acquisition.attrs["openephys_session"]:
                    intan_session = acquisition.attrs["openephys_session"]
                elif acquisition.attrs["intan_session"]:
                    intan_session = acquisition.attrs["intan_session"]
                intan_path = op.join(acquisition.directory, intan_session)
                rhs_file = [f for f in os.listdir(intan_path) if f.endswith('.rhs')][0]
                intan_fullpath = op.join(intan_path, rhs_file)
            if not pre_filter and not klusta_filter:
                klusta_filter = True
            elif pre_filter and klusta_filter:
                raise IOError('Choose either klusta-filter or pre-filter.')
            prb_path = prb_path or _get_probe_file('intan', nchan=nchan,
                                                   spikesorter='klusta')
            f = pyintan.File(intan_fullpath, prb_path)
            anas = f.analog_signals[0].signal
            fs = f.sample_rate.magnitude
            nchan = anas.shape[0]
            fname = intan_fullpath[:-4]  # remove .rhs
            klusta_prm = create_klusta_prm(fname, prb_path, nchan, fs=fs,
                                           klusta_filter=klusta_filter,
                                           filter_low=filter_low,
                                           filter_high=filter_high)
            if pre_filter:
                anas = filter_analog_signals(anas, freq=[filter_low, filter_high],
                                             fs=fs, filter_type='bandpass')

            if len(ground) != 0:
                ground = [int(g) for g in ground]
                print('Grounding channels: ', ground)
                anas = ground_bad_channels(anas, ground)
            if split_probe is not None:
                split_chans = np.arange(nchan)
                if split_probe != nchan / 2:
                    warnings.warn('The split probe is not dividing the number' +
                                  ' of channels in two')
                print('Splitting probe in channels \n"' +
                      str(split_chans[:split_probe]) + '"\nand\n"' +
                      str(split_chans[split_probe:]) + '"')
            if common_ref == 'car':
                anas, _ = apply_CAR(anas, car_type='mean', split_probe=split_probe)
            elif common_ref == 'cmr':
                anas, _ = apply_CAR(anas, car_type='median', split_probe=split_probe)

            fname = intan_fullpath[:-4]  # remove .rhs
            save_binary_format(fname, anas)
            if run:
                print('Running klusta')
                import subprocess
                try:
                    subprocess.check_output(['klusta', klusta_prm, '--overwrite'])
                except subprocess.CalledProcessError as e:
                    raise Exception(e.output)
                # subprocess.run(['klusta', klusta_prm, '--overwrite'])
            if convert and exdir_path is not None:
                print('Converting to exdir')
                openephys.generate_spike_trains(exdir_path, openephys_file,
                                                source='klusta')

        @cli.command('register-intan')
        @click.argument('intan-filepath', type=click.Path(exists=True))
        @click.option('--user',
                      required=True,
                      type=click.STRING,
                      help='The experimenter performing the recording.',
                      )
        @click.option('--left',
                      required=True,
                      type=click.FLOAT,
                      help='The depth on left side in "mm".',
                      )
        @click.option('--right',
                      required=True,
                      type=click.FLOAT,
                      help='The depth on right side in "mm".',
                      )
        @click.option('--location',
                      required=True,
                      type=click.STRING,
                      help='The location of the recording, i.e. "room_1".',
                      )
        @click.option('--session',
                      type=click.STRING,
                      help='Session number, assumed to be in end of filename by default',
                      )
        @click.option('--action-id',
                      type=click.STRING,
                      help=('Desired action id for this action, if none' +
                            ', it is generated from intan-filepath.'),
                      )
        @click.option('--temp',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--no-files',
                      is_flag=True,
                      help='Generate action without storing files.',
                      )
        @click.option('--no-modules',
                      is_flag=True,
                      help='Generate action without storing modules.',
                      )
        @click.option('--rat-id',
                      type=click.STRING,
                      help='The id number of the rat.',
                      )
        @click.option('--prb-path',
                      type=click.STRING,
                      help='Path to probefile, assumed to be in expipe config directory by default.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--nchan',
                      type=click.INT,
                      default=32,
                      help='Number of channels. Default = 32',
                      )
        def generate_intan_action(action_id, intan_filepath, temp, left,
                                  right, overwrite, no_files, no_modules,
                                  rat_id, user, prb_path, session, nchan,
                                  location):
            """Generate an intan recording-action to database.

            COMMAND: intan-filename"""
            from expipe_io_neuro import pyintan
            import quantities as pq
            import shutil
            from datetime import datetime
            intan_path = op.abspath(intan_filepath)
            intan_fullname = intan_path.split(os.sep)[-1]
            intan_filename = intan_path.split(os.sep)[-1][:-4] # get rid of .rhs
            project = expipe.io.get_project(user_params['project_id'])
            prb_path = prb_path or _get_probe_file(system='intan', nchan=nchan,
                                                   spikesorter='klusta')
            if prb_path is None:
                raise IOError('No probefile found in expipe config directory,' +
                              ' please provide one')
            intan_file = pyintan.File(intan_path, prb_path)
            rat_id = rat_id or intan_filename.split('_')[0]
            session = session or intan_filename.split('_')[-1]
            if session.isdigit():
                session = int(session)
            else:
                raise ValueError('Did not find valid session number "' +
                                 session + '"')
            if action_id is None:
                session_dtime = datetime.strftime(intan_file.datetime,
                                                  '%d%m%y')
                action_id = rat_id + '-' + session_dtime + '-%.2d' % session
            print('Generating action', action_id)
            action = project.require_action(action_id)
            action.datetime = intan_file.datetime
            action.type = 'Recording'
            action.tags = {'intan': 'true'}
            action.subjects = {rat_id: 'true'}
            headstage = action.require_module(name='intan_headstage').to_dict()
            headstage['model']['value'] = 'RHS2132'
            action.require_module(name='intan_headstage', contents=headstage)
            action.users = {user: 'true'}
            action.location = location

            if not no_modules:
                if 'intan' not in templates:
                    raise ValueError('Could not find "intan" in ' +
                                     'expipe_params.py templates: "' +
                                     '{}"'.format(templates.keys()))
                generate_templates(action, templates['intan'], overwrite,
                                   git_note=GIT_NOTE)
                L = action.require_module('electrophysiology_L').to_dict()
                L['depth'] = left * pq.mm
                print('Registering depth left = ', L['depth'])
                action.require_module('electrophysiology_L', contents=L,
                                      overwrite=True)
                R = action.require_module('electrophysiology_R').to_dict()
                R['depth'] = right * pq.mm
                print('Registering depth right = ', R['depth'])
                action.require_module('electrophysiology_R', contents=R,
                                      overwrite=True)
            fr = action.require_filerecord()
            if temp:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.local_path
            if not no_files:
                if op.exists(exdir_path):
                    if overwrite:
                        shutil.rmtree(exdir_path)
                    else:
                        raise FileExistsError('The exdir path to this action "' +
                                              exdir_path + '" exists, use ' +
                                              'overwrite flag')
                intan.convert(intan_file,
                              exdir_path=exdir_path,
                              probefile=prb_path)
                intan.generate_lfp(exdir_path, intan_file)
                intan.generate_spike_trains(exdir_path)


        @cli.command('register-intan-ephys')
        @click.argument('intan-ephys-path', type=click.Path(exists=True))
        @click.option('--user',
                      required=True,
                      type=click.STRING,
                      help='The experimenter performing the recording.',
                      )
        @click.option('--left',
                      required=True,
                      type=click.FLOAT,
                      help='The depth on left side in "mm".',
                      )
        @click.option('--right',
                      required=True,
                      type=click.FLOAT,
                      help='The depth on right side in "mm".',
                      )
        @click.option('--location',
                      required=True,
                      type=click.STRING,
                      help='The location of the recording, i.e. "room_1".',
                      default='room_1'
                      )
        @click.option('--session',
                      type=click.STRING,
                      help='Session number, assumed to be in end of filename by default',
                      )
        @click.option('--action-id',
                      type=click.STRING,
                      help=('Desired action id for this action, if none' +
                            ', it is generated from open-ephys-path.'),
                      )
        @click.option('--temp',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--no-files',
                      is_flag=True,
                      help='Generate action without storing files.',
                      )
        @click.option('--no-modules',
                      is_flag=True,
                      help='Generate action without storing modules.',
                      )
        @click.option('--intan-sync',
                      type=click.STRING,
                      help='Sync source of Intan. e.g. adc-1, dig-0',
                      default='adc-0'
                      )
        @click.option('--ephys-sync',
                      type=click.STRING,
                      help='Sync source of Open Ephys. e.g. dig-0, sync-0',
                      default='sync-0'
                      )
        @click.option('--shutter-events',
                      type=click.STRING,
                      help='Camera shutter TTL source. e.g. intan-adc-0, ephys-dig-1',
                      )
        @click.option('--rat-id',
                      type=click.STRING,
                      help='The id number of the rat.',
                      )
        @click.option('--prb-path',
                      type=click.STRING,
                      help='Path to probefile, assumed to be in expipe config directory by default.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--nchan',
                      type=click.INT,
                      default=32,
                      help='Number of channels. Default = 32',
                      )
        def generate_intan_ephys_action(action_id, intan_ephys_path, temp, left,
                                        right, overwrite, no_files, no_modules,
                                        intan_sync, ephys_sync, shutter_events,
                                        rat_id, user, prb_path, session, nchan,
                                        location):
            """Generate an intan (ephys) open-ephys (tracking) recording-action to database.

            COMMAND: intan-ephys-path"""
            from expipe_io_neuro import pyopenephys, pyintan
            from datetime import datetime
            intan_ephys_path = op.abspath(intan_ephys_path)
            intan_ephys_dir = intan_ephys_path.split(os.sep)[-1]
            rhs_file = [f for f in os.listdir(intan_ephys_path) if f.endswith('.rhs')][0]
            rhs_path = op.join(intan_ephys_path, rhs_file)
            project = expipe.io.get_project(user_params['project_id'])
            prb_path = prb_path or _get_probe_file(system='intan', nchan=nchan,
                                                   spikesorter='klusta')
            if prb_path is None:
                raise IOError('No probefile found in expipe config directory,' +
                              ' please provide one')
            openephys_file = pyopenephys.File(intan_ephys_path)
            intan_file = pyintan.File(rhs_path, prb_path)

            # clip and sync
            print('Pre-clip durations: Intan - ', intan_file.duration, ' Open Ephys - ', openephys_file.duration)
            if intan_sync and intan_sync != 'none':
                intan_sync = intan_sync.split('-')
                assert len(intan_sync) == 2
                intan_chan = int(intan_sync[1])
                if intan_sync[0] == 'adc':
                    intan_clip_times = pyintan.extract_sync_times(intan_file.adc_signals[0].signal[intan_chan],
                                                                  intan_file.times)
                elif intan_sync[0] == 'dig':
                    intan_clip_times = intan_file.digital_in_signals[0].times[intan_chan]
                else:
                    intan_clip_times = None
                intan_file.clip_recording(intan_clip_times)

            if ephys_sync and ephys_sync != 'none':
                ephys_sync = ephys_sync.split('-')
                assert len(ephys_sync) == 2
                ephys_chan = int(ephys_sync[1])
                if ephys_sync[0] == 'sync':
                    ephys_clip_times = openephys_file.sync_signals[0].times[ephys_chan]
                elif intan_sync[0] == 'dig':
                    ephys_clip_times = openephys_file.digital_in_signals[0].times[intan_chan]
                else:
                    ephys_clip_times = None
                openephys_file.clip_recording(ephys_clip_times)

            # Check duration
            if round(openephys_file.duration, 1) != round(intan_file.duration, 1):
                if round(openephys_file.duration, 1) < round(intan_file.duration, 1):
                    intan_file.clip_recording([openephys_file.duration], start_end='end')
                else:
                    openephys_file.clip_recording([intan_file.duration], start_end='end')

            print('Post-clip durations: Intan - ', intan_file.duration, ' Open Ephys - ', openephys_file.duration)

            if shutter_events:
                shutter_events = shutter_events.split('-')
                assert len(shutter_events) == 3
                shutter_sys = shutter_events[0]
                shutter_sig = shutter_events[1]
                shutter_chan = int(shutter_events[2])

                if shutter_sys == 'intan':
                    if shutter_sig == 'adc':
                        shutter_ttl = pyintan.extract_sync_times(intan_file.adc_signals[0].signal[shutter_chan],
                                                                      intan_file.times)
                    elif shutter_sig == 'dig':
                        shutter_ttl = intan_file.digital_in_signals[0].times[shutter_chan]
                elif shutter_sys == 'ephys':
                    if shutter_sig == 'dig':
                        shutter_ttl = openephys_file.digital_in_signals[0].times[shutter_chan]
                else:
                    shutter_ttl = []
                openephys_file.sync_tracking_from_events(shutter_ttl)

            rat_id = rat_id or intan_ephys_dir.split('_')[0]
            session = session or intan_ephys_dir.split('_')[-1]
            if session.isdigit():
                session = int(session)
            else:
                raise ValueError('Did not find valid session number "' +
                                 session + '"')
            if action_id is None:
                session_dtime = datetime.strftime(openephys_file.datetime,
                                                  '%d%m%y')
                action_id = rat_id + '-' + session_dtime + '-%.2d' % session
            print('Generating action', action_id)
            action = project.require_action(action_id)
            action.datetime = openephys_file.datetime
            action.type = 'Recording'
            action.tags = {'open-ephys': 'true'}
            action.subjects = {rat_id: 'true'}
            headstage = action.require_module(name='intan_headstage').to_dict()
            headstage['model']['value'] = 'RHS2132'
            action.require_module(name='intan_headstage', contents=headstage,
                                  overwrite=True)
            action.users = {user: 'true'}
            action.location = location

            if not no_modules:
                if 'intanopenephys' not in templates:
                    raise ValueError('Could not find "intanopenephys" in ' +
                                     'expipe_params.py templates: "' +
                                     '{}"'.format(templates.keys()))
                generate_templates(action, templates['intanopenephys'], overwrite,
                                   git_note=GIT_NOTE)
                L = action.require_module('electrophysiology_L').to_dict()
                L['depth'] = left * pq.mm
                print('Registering depth left = ', L['depth'])
                action.require_module('electrophysiology_L', contents=L,
                                      overwrite=True)
                R = action.require_module('electrophysiology_R').to_dict()
                R['depth'] = right * pq.mm
                print('Registering depth right = ', R['depth'])
                action.require_module('electrophysiology_R', contents=R,
                                      overwrite=True)
            fr = action.require_filerecord()
            if temp:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.local_path
            if not no_files:
                if op.exists(exdir_path):
                    if overwrite:
                        shutil.rmtree(exdir_path)
                    else:
                        raise FileExistsError('The exdir path to this action "' +
                                              exdir_path + '" exists, use ' +
                                              'overwrite flag')
                # this will copy the entire folder containing the intan file as well
                openephys.convert(openephys_file,
                                  exdir_path=exdir_path)
                intan.convert(intan_file,
                              exdir_path=exdir_path,
                              copyfiles=False)
                intan.generate_lfp(exdir_path, intan_file)
                openephys.generate_spike_trains(exdir_path, openephys_file)
                openephys.generate_tracking(exdir_path, openephys_file)

        @cli.command('register-spikesort-intan-ephys')
        @click.argument('intan-ephys-path', type=click.Path(exists=True))
        @click.option('--user',
                      type=click.STRING,
                      help='The experimenter performing the recording.',
                      )
        @click.option('--left',
                      type=click.FLOAT,
                      help='The depth on left side in "mm".',
                      )
        @click.option('--right',
                      type=click.FLOAT,
                      help='The depth on right side in "mm".',
                      )
        @click.option('--location',
                      required=True,
                      type=click.STRING,
                      help='The location of the recording, i.e. "room_1".',
                      default='room_1'
                      )
        @click.option('--session',
                      type=click.STRING,
                      help='Session number, assumed to be in end of filename by default',
                      )
        @click.option('--action-id',
                      type=click.STRING,
                      help=('Desired action id for this action, if none' +
                            ', it is generated from open-ephys-path.'),
                      )
        @click.option('--no-temp',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--no-files',
                      is_flag=True,
                      help='Generate action without storing files.',
                      )
        @click.option('--no-modules',
                      is_flag=True,
                      help='Generate action without storing modules.',
                      )
        @click.option('--intan-sync',
                      type=click.STRING,
                      help='Sync source of Intan. e.g. adc-1, dig-0',
                      default='adc-0'
                      )
        @click.option('--ephys-sync',
                      type=click.STRING,
                      help='Sync source of Open Ephys. e.g. dig-0, sync-0',
                      default='sync-0'
                      )
        @click.option('--shutter-events',
                      type=click.STRING,
                      help='Camera shutter TTL source. e.g. intan-adc-0, ephys-dig-1',
                      )
        @click.option('--remove-artifacts',
                      type=click.STRING,
                      help='TTL source for stimulation triggers. e.g. intan-adc-0, ephys-dig-1',
                      )
        @click.option('--rat-id',
                      type=click.STRING,
                      help='The id number of the rat.',
                      )
        @click.option('--prb-path',
                      type=click.STRING,
                      help='Path to probefile, assumed to be in expipe config directory by default.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--nchan',
                      type=click.INT,
                      default=32,
                      help='Number of channels. Default = 32',
                      )
        @click.option('--klusta-filter',
                      is_flag=True,
                      help='Let klusta filter or not. Default = True',
                      )
        @click.option('--pre-filter',
                      is_flag=True,
                      help='Pre filter or not, replaces klusta filter. Default = False',
                      )
        @click.option('--filter-low',
                      type=click.INT,
                      default=300,
                      help='Low cut off frequencey. Default = 300 Hz',
                      )
        @click.option('--filter-high',
                      type=click.INT,
                      default=6000,
                      help='High cut off frequencey. Default = 6000 Hz',
                      )
        @click.option('--common-ref',
                      type=click.Choice(['car', 'cmr', 'none']),
                      default='none',
                      help='Apply Common average/median referencing. Default is none')
        @click.option('--split-probe',
                      type=click.INT,
                      default=None,
                      help='Splits referencing in 2 at selected channel (for CAR/CMR). Default is None',
                      )
        @click.option('--ground', '-g',
                      multiple=True,
                      help='Ground selected channels')
        @click.option('--no-run',
                      is_flag=True,
                      help='Run klusta on dataset.',
                      )
        @click.option('--note',
                      type=click.STRING,
                      help='Add note, use "text here" for sentences.',
                      )
        def generate_intan_ephys_action(action_id, intan_ephys_path, no_temp, left,
                                        right, overwrite, no_files, no_modules,
                                        intan_sync, ephys_sync, shutter_events,
                                        rat_id, user, prb_path, session, nchan,
                                        location, pre_filter, remove_artifacts,
                                        klusta_filter, filter_low,
                                        filter_high, common_ref, ground, note,
                                        split_probe, no_run,):
            """Generate an intan (ephys) open-ephys (tracking) recording-action to database.

            COMMAND: intan-ephys-path"""
            from expipe_io_neuro import pyopenephys, pyintan
            from datetime import datetime
            import numpy as np
            from .action_tools import register_depth
            intan_ephys_path = op.abspath(intan_ephys_path)
            intan_ephys_dir = intan_ephys_path.split(os.sep)[-1]
            rhs_file = [f for f in os.listdir(intan_ephys_path) if f.endswith('.rhs')][0]
            rhs_path = op.join(intan_ephys_path, rhs_file)
            project = expipe.io.get_project(user_params['project_id'])
            prb_path = prb_path or _get_probe_file(system='intan', nchan=nchan,
                                                   spikesorter='klusta')
            if prb_path is None:
                raise IOError('No probefile found in expipe config directory,' +
                              ' please provide one')
            openephys_file = pyopenephys.File(intan_ephys_path)
            intan_file = pyintan.File(rhs_path, prb_path)

            # clip and sync
            print('Pre-clip durations: Intan - ', intan_file.duration, ' Open Ephys - ', openephys_file.duration)
            if intan_sync and intan_sync != 'none':
                intan_sync = intan_sync.split('-')
                assert len(intan_sync) == 2
                intan_chan = int(intan_sync[1])
                if intan_sync[0] == 'adc':
                    intan_clip_times = pyintan.extract_sync_times(intan_file.adc_signals[0].signal[intan_chan],
                                                                  intan_file.times)
                elif intan_sync[0] == 'dig':
                    intan_clip_times = intan_file.digital_in_signals[0].times[intan_chan]
                else:
                    intan_clip_times = None
                print('Intan clip times: ', intan_clip_times)
                intan_file.clip_recording(intan_clip_times)

            if ephys_sync and ephys_sync != 'none':
                ephys_sync = ephys_sync.split('-')
                assert len(ephys_sync) == 2
                ephys_chan = int(ephys_sync[1])
                if ephys_sync[0] == 'sync':
                    ephys_clip_times = openephys_file.sync_signals[0].times[ephys_chan]
                elif intan_sync[0] == 'dig':
                    ephys_clip_times = openephys_file.digital_in_signals[0].times[intan_chan]
                else:
                    ephys_clip_times = None
                print('Openephys clip times: ', ephys_clip_times)
                openephys_file.clip_recording(ephys_clip_times)

            # Check duration
            if round(openephys_file.duration, 1) != round(intan_file.duration, 1):
                if round(openephys_file.duration, 1) < round(intan_file.duration, 1):
                    intan_file.clip_recording([openephys_file.duration], start_end='end')
                else:
                    openephys_file.clip_recording([intan_file.duration], start_end='end')

            print('Post-clip durations: Intan - ', intan_file.duration, ' Open Ephys - ', openephys_file.duration)

            if shutter_events:
                shutter_events = shutter_events.split('-')
                assert len(shutter_events) == 3
                shutter_sys = shutter_events[0]
                shutter_sig = shutter_events[1]
                shutter_chan = int(shutter_events[2])

                if shutter_sys == 'intan':
                    if shutter_sig == 'adc':
                        shutter_ttl = pyintan.extract_sync_times(intan_file.adc_signals[0].signal[shutter_chan],
                                                                 intan_file.times)
                    elif shutter_sig == 'dig':
                        shutter_ttl = intan_file.digital_in_signals[0].times[shutter_chan]
                elif shutter_sys == 'ephys':
                    if shutter_sig == 'dig':
                        shutter_ttl = openephys_file.digital_in_signals[0].times[shutter_chan]
                else:
                    shutter_ttl = []
                openephys_file.sync_tracking_from_events(shutter_ttl)

            rat_id = rat_id or intan_ephys_dir.split('_')[0]
            session = session or intan_ephys_dir.split('_')[-1]
            if session.isdigit():
                session = int(session)
            else:
                raise ValueError('Did not find valid session number "' +
                                 session + '"')

            if action_id is None:
                session_dtime = datetime.strftime(openephys_file.datetime,
                                                  '%d%m%y')
                action_id = rat_id + '-' + session_dtime + '-%.2d' % session
            print('Generating action', action_id)
            action = project.require_action(action_id)
            action.datetime = openephys_file.datetime
            action.type = 'Recording'
            action.tags = {'open-ephys': 'true'}
            print('Registering rat id ' + rat_id)
            action.subjects = {rat_id: 'true'}
            user = user or user_params['user_name']
            print('Registering user ' + user)
            action.users = {user: 'true'}
            location = location or user_params['location']
            assert location in possible_locations
            print('Registering location ' + location)
            action.location = location


            if not no_modules:
                if 'intanopenephys' not in templates:
                    raise ValueError('Could not find "intanopenephys" in ' +
                                     'expipe_params.py templates: "' +
                                     '{}"'.format(templates.keys()))
                generate_templates(action, templates['intanopenephys'], overwrite,
                                   git_note=GIT_NOTE)
                headstage = action.require_module(name='intan_headstage').to_dict()
                headstage['model']['value'] = 'RHS2132'
                action.require_module(name='intan_headstage', contents=headstage,
                                      overwrite=True)
                register_depth(project, action, left, right)

                if len(openephys_file.messages) != 0:
                    notes = {}
                    for idx, message in enumerate(openephys_file.messages):
                        notes['note_{}'.format(idx)] = {
                            'time': message['time'],
                            'value': message['message']
                        }
                    if note is not None:
                        notes['register_note'] = {'value': note}
                    action.require_module(name='notes', contents=notes,
                                          overwrite=True)
            fr = action.require_filerecord()
            if not no_temp:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.local_path

            anas = intan_file.analog_signals[0].signal
            fs = intan_file.sample_rate.magnitude
            nchan = anas.shape[0]
            fname = op.join(intan_ephys_path, intan_ephys_dir)
            klusta_prm = create_klusta_prm(fname, prb_path, nchan, fs=fs,
                                           klusta_filter=klusta_filter,
                                           filter_low=filter_low,
                                           filter_high=filter_high)
            if pre_filter:
                anas = filter_analog_signals(anas, freq=[filter_low, filter_high],
                                             fs=fs, filter_type='bandpass')

            if len(ground) != 0:
                ground = [int(g) for g in ground]
                print('Grounding channels: ', ground)
                anas = ground_bad_channels(anas, ground)
            if split_probe is not None:
                split_chans = np.arange(nchan)
                if split_probe != nchan / 2:
                    warnings.warn('The split probe is not dividing the number' +
                                  ' of channels in two')
                print('Splitting probe in channels \n"' +
                      str(split_chans[:split_probe]) + '"\nand\n"' +
                      str(split_chans[split_probe:]) + '"')
            else:
                split_chans = np.arange(nchan)
                split_probe = None

            if remove_artifacts:
                remove_artifacts = remove_artifacts.split('-')
                assert len(remove_artifacts) == 3
                trigger_sys = remove_artifacts[0]
                trigger_sig = remove_artifacts[1]
                trigger_chan = int(remove_artifacts[2])

                if trigger_sys == 'intan':
                    if trigger_sig == 'adc':
                        trigger_ttl = pyintan.extract_sync_times(intan_file.adc_signals[0].signal[trigger_chan],
                                                                 intan_file.times)
                    elif trigger_sig == 'dig':
                        trigger_ttl = intan_file.digital_in_signals[0].times[trigger_chan]
                elif trigger_sys == 'ephys':
                    if trigger_sig == 'dig':
                        trigger_ttl = openephys_file.digital_in_signals[0].times[trigger_chan]
                else:
                    trigger_ttl = []
                anas, _ = remove_stimulation_artifacts(anas, intan_file.times, trigger_ttl, mode='zero')

            if common_ref == 'car':
                anas, _ = apply_CAR(anas, car_type='mean', split_probe=split_probe)
            elif common_ref == 'cmr':
                anas, _ = apply_CAR(anas, car_type='median', split_probe=split_probe)

            if action is not None:
                prepro = {
                    'common_ref': common_ref,
                    'filter': {
                        'pre_filter': pre_filter,
                        'klusta_filter': klusta_filter,
                        'filter_low': filter_low,
                        'filter_high': filter_high,
                    },
                    'grounded_channels': ground,
                    'probe_split': (str(split_chans[:split_probe]) +
                                    str(split_chans[split_probe:]))
                }
                action.require_module(name='preprocessing', contents=prepro,
                                      overwrite=True)

            save_binary_format(fname, anas)


            if not no_run:
                print('Running klusta')
                import subprocess
                try:
                    subprocess.check_output(['klusta', klusta_prm, '--overwrite'])
                except subprocess.CalledProcessError as e:
                    raise Exception(e.output)

            if not no_files:
                if op.exists(exdir_path):
                    if overwrite:
                        shutil.rmtree(exdir_path)
                    else:
                        raise FileExistsError('The exdir path to this action "' +
                                              exdir_path + '" exists, use ' +
                                              'overwrite flag')
                # this will copy the entire folder containing the intan file as well
                openephys.convert(openephys_file,
                                  exdir_path=exdir_path)
                intan.convert(intan_file,
                              exdir_path=exdir_path,
                              copyfiles=False)
                intan.generate_lfp(exdir_path, intan_file)
                openephys.generate_spike_trains(exdir_path, openephys_file)
                openephys.generate_tracking(exdir_path, openephys_file)
