import expipe
import expipe.io
from expipecli.utils import IPlugin
import click
from expipe_io_neuro import axona
import os
import os.path as op
import sys
from .action_tools import (generate_templates, _get_local_path, GIT_NOTE)

from .visual_tools import (get_grating_stimulus_events, get_key_press_events,
                           generate_blank_group, generate_key_event_group,
                           generate_grating_stimulus_group,
                           generate_grating_stimulus_epoch,
                           parse_bonsai_head_tracking_file,
                           copy_bonsai_raw_data,
                           organize_bonsai_tracking_files,
                           generate_head_tracking_groups,
                           parse_psychopy_openephys)
from .pytools import load_parameters

PAR = load_parameters()

DTIME_FORMAT = expipe.io.core.datetime_format


def attach_to_cli(cli):
    @cli.command('register-axona',
                 short_help=('Generates stimulus groups and epoch based on ' +
                             'axona inp epoch. Arguments: ACTION-ID'))
    @click.argument('action-id', type=click.STRING)
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    def generate_stim_group_and_epoch(action_id, overwrite):
        # TODO: check overwrite
        """"""
        import exdir

        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.get_action(action_id)
        fr = action.require_filerecord()
        exdir_path = _get_local_path(fr)
        exdir_object = exdir.File(exdir_path)

        grating = get_grating_stimulus_events(exdir_object["epochs/axona_inp"])
        keys = get_key_press_events(exdir_object["epochs/axona_inp"])
        durations = grating["blank"]["timestamps"][1:] - grating["grating"]["timestamps"]

        # generate stimulus groups
        generate_blank_group(exdir_path, grating["blank"]["timestamps"])
        generate_key_event_group(exdir_path, keys["keys"], keys["timestamps"])
        generate_grating_stimulus_group(exdir_path,
                                        grating["grating"]["timestamps"], grating["grating"]["data"], grating["grating"]["mode"])

        # generate stimulus epoch
        generate_grating_stimulus_epoch(exdir_path,
                                        grating["grating"]["timestamps"],
                                        durations,
                                        grating["grating"]["data"])

        print("successfully created stimulus groups and epoch.")

    @cli.command('register-psychopy')
    @click.argument('action-id', type=click.STRING)
    @click.argument('psyexp-path', type=click.Path(exists=True))
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    @click.option('--io-channel',
                  default=7,
                  type=click.INT,
                  help='Channel recieving timestamps, open ephys IO board.',
                  )
    def generate_epoch_openephys(action_id, psyexp_path, overwrite,
                                 io_channel):
        # TODO: check overwrite
        """Generates stimulus groups and epoch based on axona inp epoch.

        COMMAND: action-id: Provide action id to find exdir path"""
        assert psyexp_path.endswith('.psyexp')
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.get_action(action_id)
        fr = action.require_filerecord()
        exdir_path = _get_local_path(fr)

        grating = parse_psychopy_openephys(action, psyexp_path, io_channel)
        # keys = get_key_press_events(exdir_object["epochs/axona_inp"])

        # generate stimulus groups
        generate_blank_group(exdir_path, grating["blank"]["timestamps"])
        # generate_key_event_group(exdir_path, keys["keys"], keys["timestamps"])
        generate_grating_stimulus_group(exdir_path,
                                        grating["grating"]["timestamps"],
                                        grating["grating"]["data"])
                                        # grating["grating"]["mode"])

        # generate stimulus epoch
        generate_grating_stimulus_epoch(exdir_path,
                                        grating["grating"]["timestamps"],
                                        grating['durations'],
                                        grating["grating"]["data"])

        print("successfully created stimulus groups and epoch.")

    @cli.command('register-bonsai-tracking')
    @click.argument('action-id', type=click.STRING)
    @click.option('--axona-filename',
                  required=True,
                  type=click.STRING,
                  help='Axona filename (.set file)',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    def generate_bonsai_tracking_groups(action_id, axona_filename, overwrite):
        # TODO: check overwrite
        """Generates bonsai tracking group and copies raw data.

        COMMAND: action-id: Provide action id to find exdir path"""
        import exdir

        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        fr = action.require_filerecord()
        exdir_path = _get_local_path(fr)
        exdir_object = exdir.File(exdir_path)

        copy_bonsai_raw_data(exdir_path, axona_filename)
        axona_dirname = os.path.dirname(axona_filename)
        filenames = organize_bonsai_tracking_files(axona_dirname)

        for key, path in filenames.items():
            if "ir" in key:
                tracking = parse_bonsai_head_tracking_file(path)
                try:
                    source_filename = os.path.basename(path)
                    generate_head_tracking_groups(exdir_path, tracking,
                                                  key, source_filename)
                except FileExistsError:
                    print("Headtracking datasets (" + str(key) + ") already exist. Skipping...")
