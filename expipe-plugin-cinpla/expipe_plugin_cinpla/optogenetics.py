import expipe
import expipe.io
from expipecli.utils import IPlugin
import click
from expipe_io_neuro import pyopenephys, openephys, pyintan, intan, axona

from .action_tools import generate_templates, _get_local_path, GIT_NOTE
from .opto_tools import (generate_epochs, generate_axona_opto, populate_modules,
                        extract_laser_pulse, read_pulse_pal_mat,
                        read_pulse_pal_xml, read_laser_intensity,
                        generate_openephys_opto)
import os
import os.path as op
import sys
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import (user_params, templates, unit_info,
                               possible_brain_areas)

DTIME_FORMAT = expipe.io.core.datetime_format


class OptoPlugin(IPlugin):
    """Create the `expipe parse-axona` command for neuro recordings."""
    def attach_to_cli(self, cli):
        @cli.command('register-opto')
        @click.argument('action-id', type=click.STRING)
        @click.option('--brain-area',
                      required=True,
                      type=click.Choice(possible_brain_areas),
                      help='The anatomical brain-area of the optogenetic stimulus.',
                      )
        @click.option('--tag',
                      required=True,
                      type=click.Choice(['opto-inside', 'opto-outside', 'opto-train']),
                      help='The anatomical brain-area of the optogenetic stimulus.',
                      )
        @click.option('--note',
                      type=click.STRING,
                      help='Add note, use "text here" for sentences.',
                      )
        @click.option('--io-channel',
                      default=4,
                      type=click.INT,
                      help='TTL input channel.',
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
        def parse_optogenetics(action_id, brain_area, no_local, overwrite,
                               io_channel, tag, note, laser_id):
            """Parse optogenetics info to an action.

            COMMAND: action-id: Provide action id to find exdir path"""
            import exdir
            # TODO deafault none
            if brain_area not in possible_brain_areas:
                raise ValueError("brain_area must be either %s",
                                 possible_brain_areas)
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            tags = action.tags or {}
            tags.update({tag: 'true', 'opto-' + brain_area: 'true'})
            action.tags = tags
            fr = action.require_filerecord()
            if not no_local:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.server_path
            exdir_object = exdir.File(exdir_path)
            if exdir_object['acquisition'].attrs['acquisition_system'] == 'Axona':
                aq_sys = 'axona'
                params = generate_axona_opto(exdir_path, io_channel)
            elif exdir_object['acquisition'].attrs['acquisition_system'] == 'OpenEphys':
                aq_sys = 'openephys'
                params = generate_openephys_opto(exdir_path, io_channel)
            else:
                raise ValueError('Acquisition system not recognized')
            params.update({'location': brain_area})
            generate_templates(action, templates['opto_' + aq_sys],
                               overwrite, git_note=None)
            populate_modules(action, params)
            laser_id = laser_id or user_params['laser_device'].get('id')
            laser_name = user_params['laser_device'].get('name')
            assert laser_id is not None
            assert laser_name is not None
            laser = action.require_module(name=laser_name).to_dict()
            laser['device_id'] = {'value': laser_id}
            action.require_module(name=laser_name, contents=laser,
                                  overwrite=True)
            if note is not None:
                notes = action.require_module(name='notes').to_dict()
                notes['opto_note'] = {'value': note}
                action.require_module(name='notes', contents=notes,
                                      overwrite=True)

        @cli.command('register-opto-files')
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
            """Parse optogenetics info to an action.

            COMMAND: action-id: Provide action id to find exdir path"""
            import exdir
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            fr = action.require_filerecord()
            if not no_local:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.server_path
            exdir_object = exdir.File(exdir_path)
            if exdir_object['acquisition'].attrs['acquisition_system'] == 'Axona':
                aq_sys = 'axona'
                params = generate_axona_opto(exdir_path, io_channel)
            elif exdir_object['acquisition'].attrs['acquisition_system'] == 'OpenEphys':
                aq_sys = 'openephys'
                params = generate_openephys_opto(exdir_path, io_channel)
            else:
                raise ValueError('Acquisition system not recognized')
