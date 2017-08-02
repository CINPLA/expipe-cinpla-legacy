import expipe
import expipe.io
import os
import os.path as op
from expipecli.utils import IPlugin
import click
import sys
from expipe_io_neuro import pyopenephys, openephys
from .action_tools import (generate_templates, _get_local_path,
                           _get_probe_file, GIT_NOTE)
from exana.misc.signal_tools import (create_klusta_prm, save_binary_format,
                                     apply_CAR, filter_analog_signals,
                                     ground_bad_channels, duplicate_bad_channels)
from .pytools import load_parameters

PAR = load_parameters()

DTIME_FORMAT = expipe.io.core.datetime_format


class OpenEphysPlugin(IPlugin):
    """Create the `expipe parse-axona` command for neuro recordings."""
    def attach_to_cli(self, cli):
        @cli.command('process-openephys')
        @click.argument('action-id', type=click.STRING)
        @click.option('--prb-path',
                      type=click.STRING,
                      help='Path to probefile, assumed to be in expipe config directory by default.',
                      )
        @click.option('--openephys-path',
                      type=click.STRING,
                      help='Path to openeophys dir, if none it is deduced from action id.',
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
                      help='Let klusta filter or not. Default = False',
                      )
        @click.option('--pre-filter',
                      is_flag=True,
                      help='Pre filter or not, replaces klusta filter. Default = True',
                      )
        @click.option('--filter-low',
                      type=click.INT,
                      default=300,
                      help='Low cut off frequencey. Default is 300 Hz',
                      )
        @click.option('--filter-high',
                      type=click.INT,
                      default=6000,
                      help='High cut off frequencey. Default is 6000 Hz',
                      )
        @click.option('--common-ref',
                      type=click.Choice(['car', 'cmr', 'none']),
                      default='cmr',
                      help='Apply Common average/median referencing. Default is "car"')
        @click.option('--split-probe',
                      type=click.INT,
                      default=16,
                      help='Splits referencing in 2 at selected channel (for CAR/CMR). Default is 16',
                      )
        @click.option('--ground', '-g',
                      multiple=True,
                      help='Ground selected channels')
        @click.option('--no-klusta',
                      is_flag=True,
                      help='Not run klusta on dataset.',
                      )
        @click.option('--no-convert',
                      is_flag=True,
                      help='Not convert to exdir.',
                      )
        @click.option('--no-local',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--no-preprocess',
                      is_flag=True,
                      help='Preporcess data.',
                      )
        @click.option('--shutter-channel',
                      type=click.INT,
                      default=0,
                      help='TTL channel for shutter events to sync tracking',
                      )
        def process_openephys(action_id, prb_path, pre_filter,
                               klusta_filter, filter_low,
                               filter_high, nchan, common_ref, ground,
                               split_probe, no_local, openephys_path,
                               exdir_path, no_klusta, no_convert, shutter_channel,
                               no_preprocess):
            """Generate a klusta .dat and .prm files from openephys directory.

            COMMAND: action-id"""
            import numpy as np
            if not no_klusta:
                import klusta
                import klustakwik2
            action = None
            if exdir_path is None:
                import exdir
                project = expipe.get_project(PAR.USER_PARAMS['project_id'])
                action = project.require_action(action_id)
                fr = action.require_filerecord()
                if not no_local:
                    exdir_path = _get_local_path(fr)
                else:
                    exdir_path = fr.server_path
                exdir_file = exdir.File(exdir_path)
            if openephys_path is None:
                acquisition = exdir_file["acquisition"]
                if acquisition.attrs['acquisition_system'] != 'OpenEphys':
                    raise ValueError('No Open Ephys aquisition system ' +
                                     'related to this action')
                openephys_session = acquisition.attrs["openephys_session"]
                openephys_path = op.join(str(acquisition.directory), openephys_session)
                openephys_base = op.join(openephys_path, openephys_session)
                klusta_prm = op.abspath(openephys_base) + '.prm'
                prb_path = prb_path or _get_probe_file('oe', nchan=nchan,
                                                       spikesorter='klusta')
                openephys_file = pyopenephys.File(openephys_path, prb_path)
            if not no_preprocess:
                if not pre_filter and not klusta_filter:
                    pre_filter = True
                elif pre_filter and klusta_filter:
                    raise IOError('Choose either klusta-filter or pre-filter.')
                anas = openephys_file.analog_signals[0].signal
                fs = openephys_file.sample_rate.magnitude
                nchan = anas.shape[0]
                create_klusta_prm(openephys_base, prb_path, nchan,
                                  fs=fs, klusta_filter=klusta_filter,
                                  filter_low=filter_low,
                                  filter_high=filter_high)
                if pre_filter:
                    anas = filter_analog_signals(anas, freq=[filter_low, filter_high],
                                                 fs=fs, filter_type='bandpass')
                if len(ground) != 0:
                    ground = [int(g) for g in ground]
                    anas = ground_bad_channels(anas, ground)
                if split_probe is not None:
                    split_chans = np.arange(nchan)
                    if split_probe != nchan / 2:
                        import warnings
                        warnings.warn('The split probe is not dividing the number' +
                                      ' of channels in two')
                    print('Splitting probe in channels \n"' +
                          str(split_chans[:split_probe]) + '"\nand\n"' +
                          str(split_chans[split_probe:]) + '"')
                if common_ref == 'car':
                    anas, _ = apply_CAR(anas, car_type='mean',
                                        split_probe=split_probe)
                elif common_ref == 'cmr':
                    anas, _ = apply_CAR(anas, car_type='median',
                                        split_probe=split_probe)
                if len(ground) != 0:
                    duplicate = [int(g) for g in ground]
                    anas = duplicate_bad_channels(anas, duplicate, prb_path)
                save_binary_format(openephys_base, anas)
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

            if not no_klusta:
                print('Running klusta')
                import subprocess
                try:
                    subprocess.check_output(['klusta', klusta_prm, '--overwrite'])
                except subprocess.CalledProcessError as e:
                    raise Exception(e.output)
            if not no_convert:
                print('Converting to exdir')
                openephys.generate_spike_trains(exdir_path, openephys_file,
                                                source='klusta')
                print('Finished with spiketrains, you can now start manual ' +
                      'clustering while tracking and LFP is processed')
                if shutter_channel is not None:
                    ttl_times = openephys_file.digital_in_signals[0].times[shutter_channel]
                    if len(ttl_times) != 0:
                        openephys_file.sync_tracking_from_events(ttl_times)
                    else:
                        import warnings
                        warnings.warn(
                            'No TTL events was found on IO channel {}'.format(shutter_channel)
                        )
                openephys.generate_tracking(exdir_path, openephys_file)
                openephys.generate_lfp(exdir_path, openephys_file)

        @cli.command('register-openephys')
        @click.argument('openephys-path', type=click.Path(exists=True))
        @click.option('-u', '--user',
                      type=click.STRING,
                      help='The experimenter performing the recording.',
                      )
        @click.option('-a', '--anatomy',
                      multiple=True,
                      type=(click.STRING, float),
                      help='The adjustment amount on given anatomical location in "um".',
                      )
        @click.option('-l', '--location',
                      type=click.Choice(PAR.POSSIBLE_LOCATIONS),
                      help='The location of the recording, e.g. "room1".',
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
        @click.option('--spikes-source',
                      type=click.Choice(['klusta', 'openephys', 'none']),
                      default='none',
                      help='Generate spiketrains from "source". Default is none'
                      )
        @click.option('--no-local',
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
        @click.option('--subject-id',
                      type=click.STRING,
                      help='The id number of the subject.',
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
        @click.option('-m', '--message',
                      multiple=True,
                      type=click.STRING,
                      help='Add message, use "text here" for sentences.',
                      )
        @click.option('-t', '--tag',
                      multiple=True,
                      type=click.STRING,
                      help='Add tags to action.',
                      )
        @click.option('--no-move',
                      is_flag=True,
                      help='Do not delete open ephys directory after copying.',
                      )
        def generate_openephys_action(action_id, openephys_path, no_local,
                                      anatomy, overwrite, no_files, no_modules,
                                      subject_id, user, prb_path, session, nchan,
                                      location, spikes_source, message, no_move,
                                      tag):
            """Generate an open-ephys recording-action to database.

            COMMAND: open-ephys-directory"""
            # TODO default none
            from expipe_io_neuro import pyopenephys
            import quantities as pq
            import shutil
            from datetime import datetime, timedelta
            from .action_tools import register_depth
            openephys_path = op.abspath(openephys_path)
            openephys_dirname = openephys_path.split(os.sep)[-1]
            project = expipe.get_project(PAR.USER_PARAMS['project_id'])
            prb_path = prb_path or _get_probe_file(system='oe', nchan=nchan,
                                                   spikesorter='klusta')
            if prb_path is None:
                raise IOError('No probefile found in expipe config directory,' +
                              ' please provide one')
            openephys_file = pyopenephys.File(openephys_path, prb_path)
            subject_id = subject_id or openephys_dirname.split('_')[0]
            session = session or openephys_dirname.split('_')[-1]
            if session.isdigit():
                session = int(session)
            else:
                raise ValueError('Did not find valid session number "' +
                                 session + '"')
            if action_id is None:
                session_dtime = datetime.strftime(openephys_file.datetime,
                                                  '%d%m%y')
                action_id = subject_id + '-' + session_dtime + '-%.2d' % session
            print('Generating action', action_id)
            action = project.require_action(action_id)
            action.datetime = openephys_file.datetime
            action.type = 'Recording'
            action.tags.extend(list(tag) + ['open-ephys'])
            print('Registering subject id ' + subject_id)
            action.subjects = [subject_id]
            user = user or PAR.USER_PARAMS['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')
            print('Registering user ' + user)
            action.users = [user]
            location = location or PAR.USER_PARAMS['location']
            if location is None:
                raise ValueError('Please add location')
            if len(location) == 0:
                raise ValueError('Please add location')
            assert location in PAR.POSSIBLE_LOCATIONS
            print('Registering location ' + location)
            action.location = location
            messages = [{'message': m, 'user': user, 'datetime': datetime.now()}
                        for m in message]
            if not no_modules:
                if 'openephys' not in PAR.TEMPLATES:
                    raise ValueError('Could not find "openephys" in ' +
                                     'expipe_params.py PAR.TEMPLATES: "' +
                                     '{}"'.format(PAR.TEMPLATES.keys()))
                generate_templates(action, PAR.TEMPLATES['openephys'], overwrite,
                                   git_note=GIT_NOTE)
                headstage = action.require_module(
                    name='hardware_intan_headstage').to_dict()
                headstage['model']['value'] = 'RHD2132'
                action.require_module(name='hardware_intan_headstage',
                                      contents=headstage, overwrite=True)
                correct_depth = register_depth(project, action, anatomy)
                if not correct_depth:
                    print('Aborting registration!')
                    return

                for idx, m in enumerate(openephys_file.messages):
                    secs = float(m['time'].rescale('s').magnitude)
                    dtime = openephys_file.datetime + timedelta(seconds=secs)
                    messages.append({'datetime': dtime,
                                     'message': m['message'],
                                     'user': user})
            action.messages.extend(messages)
            if not no_files:
                fr = action.require_filerecord()
                if not no_local:
                    exdir_path = _get_local_path(fr)
                else:
                    exdir_path = fr.server_path
                if op.exists(exdir_path):
                    if overwrite:
                        shutil.rmtree(exdir_path)
                    else:
                        raise FileExistsError('The exdir path to this action "' +
                                              exdir_path + '" exists, use ' +
                                              'overwrite flag')
                os.makedirs(op.dirname(exdir_path), exist_ok=True)
                shutil.copy(prb_path, openephys_path)
                openephys.convert(openephys_file,
                                  exdir_path=exdir_path)
                if spikes_source != 'none':
                    openephys.generate_spike_trains(exdir_path, openephys_file,
                                                    source=spikes_source)
                if not no_move:
                    shutil.rmtree(openephys_path)

        @cli.command('convert-klusta-oe')
        @click.argument('action-id', type=click.STRING)
        @click.option('--prb-path',
                      type=click.STRING,
                      help='Path to probefile, assumed to be in expipe config directory by default.',
                      )
        @click.option('--openephys-path',
                      type=click.STRING,
                      help='Path to openeophys dir, if none it is deduced from action id.',
                      )
        @click.option('--exdir-path',
                      type=click.STRING,
                      help='Path to desired exdir directory, if none it is deduced from action id.',
                      )
        @click.option('--no-local',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--nchan',
                      type=click.INT,
                      default=32,
                      help='Number of channels. Default = 32',
                      )
        def generate_klusta_oe(action_id, prb_path, no_local, openephys_path,
                               exdir_path, nchan):
            """Convert klusta spikes to exdir.

            COMMAND: action-id"""
            import numpy as np
            if openephys_path is None:
                import exdir
                project = expipe.get_project(PAR.USER_PARAMS['project_id'])
                action = project.require_action(action_id)
                fr = action.require_filerecord()
                if not no_local:
                    exdir_path = _get_local_path(fr)
                else:
                    exdir_path = fr.server_path
                exdir_file = exdir.File(exdir_path)
                acquisition = exdir_file["acquisition"]
                if acquisition.attrs['acquisition_system'] != 'OpenEphys':
                    raise ValueError('No Open Ephys aquisition system ' +
                                     'related to this action')
                openephys_session = acquisition.attrs["openephys_session"]
                openephys_path = op.join(str(acquisition.directory), openephys_session)
            prb_path = prb_path or _get_probe_file('oe', nchan=nchan,
                                                   spikesorter='klusta')
            openephys_file = pyopenephys.File(openephys_path, prb_path)
            print('Converting to exdir')
            openephys.generate_spike_trains(exdir_path, openephys_file,
                                                source='klusta')

        @cli.command('read-messages')
        @click.argument('openephys-path', type=click.Path(exists=True))
        def generate_openephys_action(openephys_path):
            """Read messages from open-ephys recording session.

            COMMAND: open-ephys-directory"""
            # TODO default none
            from expipe_io_neuro import pyopenephys
            import quantities as pq
            import shutil
            from datetime import datetime, timedelta
            from .action_tools import register_depth
            openephys_path = op.abspath(openephys_path)
            openephys_dirname = openephys_path.split(os.sep)[-1]
            project = expipe.get_project(PAR.USER_PARAMS['project_id'])

            openephys_file = pyopenephys.File(openephys_path)
            messages = openephys_file.messages

            print('Open-ephys messages:')
            for m in messages:
                print('time: ', m['time'], ' message: ', m['message'])
