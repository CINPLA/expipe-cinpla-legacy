from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.tools import action as action_tools
from expipe_plugin_cinpla.tools import opto as opto_tools
from expipe_plugin_cinpla.tools import config


def attach_to_cli(cli):
    @cli.command('register', short_help='Parse optogenetics info to an action.')
    @click.argument('action-id', type=click.STRING)
    @click.option('--brain-area',
                  required=True,
                  callback=config.optional_choice,
                  envvar=PAR.POSSIBLE_BRAIN_AREAS,
                  help='The anatomical brain-area of the optogenetic stimulus.',
                  )
    @click.option('-t', '--tag',
                  multiple=True,
                  required=True,
                  callback=config.optional_choice,
                  envvar=PAR.POSSIBLE_OPTO_TAGS,
                  help='The anatomical brain-area of the optogenetic stimulus.',
                  )
    @click.option('-m', '--message',
                  multiple=True,
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('--io-channel',
                  default=8,
                  type=click.INT,
                  help='TTL input channel. Default is 8 (axona tetrode 9)',
                  )
    @click.option('--no-local',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    @click.option('--laser-id',
                  type=click.STRING,
                  help='A unique identifier of the laser.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the annotation.',
                  )
    @click.option('--no-modules',
                  is_flag=True,
                  help='Do not upload any modules.',
                  )
    @click.option('--use-axona-cut',
                  is_flag=True,
                  help='Use Axona cut file for input registration.',
                  )
    @click.option('--pulse-phasedur',
                  nargs=2,
                  default=(None, None),
                  type=(click.FLOAT, click.STRING),
                  help=('Duration of laser pulse with units e.g. 10 ms.' +
                        ' Only relevant if no config file available.'),
                  )
    @click.option('--pulse-period',
                  nargs=2,
                  default=(None, None),
                  type=(click.FLOAT, click.STRING),
                  help=('Period of laser pulse with units e.g. 10 ms.' +
                        ' Only relevant if no config file available.'),
                  )
    @click.option('--no-intensity',
                  is_flag=True,
                  help='Use Axona cut file for input registration.',
                  )
    def parse_optogenetics(action_id, brain_area, no_local, overwrite,
                           io_channel, tag, message, laser_id, user,
                           no_modules, use_axona_cut, pulse_phasedur,
                           pulse_period, no_intensity):
        # TODO deafault none
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        user = user or PAR.USER_PARAMS['user_name']
        user = user or []
        if len(user) == 0:
            raise ValueError('Please add user name')
        action.tags.extend(list(tag) + ['opto-' + brain_area])
        fr = action.require_filerecord()
        if not no_local:
            exdir_path = action_tools._get_local_path(fr)
        else:
            exdir_path = fr.server_path
        exdir_object = exdir.File(exdir_path)
        if exdir_object['acquisition'].attrs['acquisition_system'] == 'Axona':
            aq_sys = 'axona'
            if use_axona_cut:
                if pulse_phasedur == (None, None):
                    raise ValueError (
                        'You need to provide pulse phase duration, e.g.' +
                        '"pulse-phasedur 10 ms" to use Axona cut')
                pulse_phasedur = pq.Quantity(pulse_phasedur[0],
                                             pulse_phasedur[1])
                params = opto_tools.generate_axona_opto_from_cut(exdir_path,
                                                      pulse_phasedur,
                                                      io_channel)
            else:
                params = opto_tools.generate_axona_opto(
                    exdir_path, io_channel, no_intensity=no_intensity)
        elif exdir_object['acquisition'].attrs['acquisition_system'] == 'OpenEphys':
            aq_sys = 'openephys'
            params = opto_tools.generate_openephys_opto(exdir_path, io_channel)
        else:
            raise ValueError('Acquisition system not recognized')
        if not no_modules:
            params.update({'location': brain_area})
            action_tools.generate_templates(action, 'opto_' + aq_sys,
                               overwrite, git_note=None)
            opto_tools.populate_modules(action, params,
                                        no_intensity=no_intensity)
            laser_id = laser_id or PAR.USER_PARAMS['laser_device'].get('id')
            laser_name = PAR.USER_PARAMS['laser_device'].get('name')
            assert laser_id is not None
            assert laser_name is not None
            laser = action.require_module(name=laser_name).to_dict()
            laser['device_id'] = {'value': laser_id}
            action.require_module(name=laser_name, contents=laser,
                                  overwrite=True)
        action.messages.extend([{'message': m,
                                 'user': user,
                                 'datetime': datetime.now()}
                               for m in message])

    @cli.command('parse-files', short_help='Parse optogenetics files.')
    @click.argument('action-id', type=click.STRING)
    @click.option('--no-local',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    @click.option('--io-channel',
                  default=4,
                  type=click.INT,
                  help='TTL input channel.',
                  )
    def parse_optogenetics_files(action_id, no_local, io_channel):
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        fr = action.require_filerecord()
        if not no_local:
            exdir_path = action_tools._get_local_path(fr)
        else:
            exdir_path = fr.server_path
        exdir_object = exdir.File(exdir_path)
        if exdir_object['acquisition'].attrs['acquisition_system'] == 'Axona':
            aq_sys = 'axona'
            params = opto_tools.generate_axona_opto(exdir_path, io_channel)
        elif exdir_object['acquisition'].attrs['acquisition_system'] == 'OpenEphys':
            aq_sys = 'openephys'
            params = opto_tools.generate_openephys_opto(exdir_path, io_channel)
        else:
            raise ValueError('Acquisition system not recognized')
