import expipe
import os
import os.path as op
import click
import sys
import warnings
from .action_tools import (generate_templates, _get_local_path, create_notebook,
                           GIT_NOTE)
from .pytools import deep_update, load_python_module, load_parameters

PAR = load_parameters()

DTIME_FORMAT = expipe.io.core.datetime_format


def attach_to_cli(cli):
    @cli.command('generate-notebook')
    @click.argument('action-id', type=click.STRING)
    @click.option('--no_local',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    @click.option('--channel-group',
                  type=click.INT,
                  help='Which channel-group to analyse.',
                  )
    @click.option('--run',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    def generate_notebook(action_id, channel_group, no_local, run):
        """
        Provide action id to find exdir path

        COMMAND: action-id: Provide action id to find exdir path
        """
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        fr = action.require_filerecord()
        if not no_local:
            exdir_path = _get_local_path(fr, assert_exists=True)
        else:
            exdir_path = fr.server_path
        fname = create_notebook(exdir_path)
        if run:
            import subprocess
            subprocess.run(['jupyter', 'notebook', fname])

    @cli.command('analyse')
    @click.argument('action-id', type=click.STRING)
    @click.option('--channel-group',
                  multiple=True,
                  type=click.INT,
                  help='Which channel-group to analyse.',
                  )
    @click.option('--no-local',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    @click.option('-a', '--analysis',
                  multiple=True,
                  type=click.Choice(['spike-stat', 'spatial', 'all',
                                     'psd', 'spike-lfp', 'tfr', 'stim-stat',
                                     'occupancy', 'orient-tuning']),
                  help='Analyse data.',
                  )
    @click.option('--tag', '-t',
                  multiple=True,
                  type=click.Choice(PAR.POSSIBLE_TAGS),
                  help='The anatomical brain-area of the optogenetic stimulus.',
                  )
    @click.option('-m', '--message',
                  multiple=True,
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the adjustment.',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite.',
                  )
    @click.option('--skip',
                  is_flag=True,
                  help='Skip previously generated files.',
                  )
    def analysis(**kwargs):
        """Analyse a dataset

        COMMAND: action-id: Provide action id to find exdir path"""
        from .analysis_tools import Analyser
        from datetime import datetime
        if len(kwargs['channel_group']) == 0: kwargs['channel_group'] = None
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(kwargs['action_id'] + '-analysis')
        rec_action = project.require_action(kwargs['action_id'])
        action.type = 'Action-analysis'
        user = kwargs['user'] or PAR.USER_PARAMS['user_name']
        if user is None:
            raise ValueError('Please add user name')
        if len(user) == 0:
            raise ValueError('Please add user name')

        users = list(set(rec_action.users))
        if user not in users:
            users.append(user)
        action.users = users
        action.tags.extend(list(kwargs['tag']) + list(rec_action.tags))
        action.location = rec_action.location or ''
        action.datetime = rec_action.datetime or ''
        subjects = rec_action.subjects or []
        action.subjects.extend(list(subjects))
        action.messages.extend([{'message': m,
                                 'user': user,
                                 'datetime': datetime.now()}
                               for m in kwargs['message']])
        fr = rec_action.require_filerecord()
        if not kwargs['no_local']:
            exdir_path = _get_local_path(fr)
        else:
            exdir_path = fr.server_path
        action.require_module('software_version_control_git',
                              contents=GIT_NOTE,
                              overwrite=(kwargs['overwrite'] or kwargs['skip']))
        action.require_module('software_analysis_parameters',
                              contents=PAR.ANALYSIS_PARAMS,
                              overwrite=(kwargs['overwrite'] or kwargs['skip']))
        an = Analyser(exdir_path, params=PAR.ANALYSIS_PARAMS,
                      unit_info=PAR.UNIT_INFO,
                      channel_group=kwargs['channel_group'],
                      no_local=kwargs['no_local'],
                      overwrite=kwargs['overwrite'],
                      skip=kwargs['skip'])
        if any(arg in kwargs['analysis'] for arg in ['stim-stat', 'all']):
            print('Analysing stimulation statistics.')
            an.stimulation_statistics()
        if any(arg in kwargs['analysis'] for arg in ['occupancy', 'all']):
            print('Analysing occupancy.')
            an.occupancy()
        if any(arg in kwargs['analysis'] for arg in ['spatial', 'all']):
            print('Analysing spatial statistics.')
            an.spatial_overview()
        if any(arg in kwargs['analysis'] for arg in ['spike-stat', 'all']):
            print('Analysing spike statistics.')
            an.spike_statistics()
        if any(arg in kwargs['analysis'] for arg in ['psd', 'all']):
            print('Analysing stimulation statistics.')
            an.psd()
        if any(arg in kwargs['analysis'] for arg in ['spike-lfp', 'all']):
            print('Analysing spike LFP relations.')
            an.spike_lfp_coherence()
        if any(arg in kwargs['analysis'] for arg in ['tfr']):
            print('Analysing TFR.')
            an.tfr()
        if any(arg in kwargs['analysis'] for arg in ['orient-tuning']):
            print('Analysing orientation tuning.')
            an.orient_tuning_overview()
        for key, val in an.analysis_output.items():
            try:
                mod = action.get_module(key).to_dict()
            except NameError:
                mod = {}
            deep_update(mod, val)
            action.require_module(key, contents=mod,
                                  overwrite=True)
                # fname = op.abspath(op.join('action_modules',
                #                            PAR.USER_PARAMS['project_id'],
                #                            action.id, key + '.json'))
                # os.makedirs(op.dirname(fname), exist_ok=True)
                # print('Got exception during module update of "' + key +
                #       '" stored in "' + fname + '"')
                # import json
                # with open(fname, 'w') as f:
                #     result = expipe.io.core.convert_quantities(val)
                #     json.dump(result, f, sort_keys=True, indent=4)

    @cli.command('group-analyse')
    @click.argument('action-id', type=click.STRING)
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the analysis.',
                  )
    @click.option('-t', '--tags',
                  multiple=True,
                  type=click.STRING,
                  help='Tags to sort the analysis.',
                  )
    @click.option('-a', '--actions',
                  multiple=True,
                  type=click.STRING,
                  help='Actions to include in the analysis.',
                  )
    @click.option('-s', '--subjects',
                  multiple=True,
                  type=click.STRING,
                  help='Subjects to sort the analysis.',
                  )
    @click.option('-l', '--locations',
                  multiple=True,
                  type=click.STRING,
                  help='Subjects to sort the analysis.',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite.',
                  )
    def group_analysis(action_id, user, tags, overwrite, subjects,
                       locations, actions):
        """Parse info about recorded units

        COMMAND: action-id: Provide action id to get action"""
        from datetime import datetime
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        analysis_action = project.require_action(action_id)

        analysis_action.type = 'Group-analysis'
        user = user or PAR.USER_PARAMS['user_name']
        if user is None:
            raise ValueError('Please add user name')
        if len(user) == 0:
            raise ValueError('Please add user name')
        analysis_action.users.append(user)
        analysis_action.tags = list(tag)
        # TODO this is slow, can omit loading all the modules for each action
        for action in project.actions:
            if action.type != 'Action-analysis':
                continue
            if len(actions) > 0:
                if action.id not in actions:
                    continue
            if len(action.tags) == 0:
                raise ValueError('No tags in "' + action.id + '"')
            if not any(t in tags for t in action.tags):
                continue
            if len(subjects) > 0:
                if not any(s in subjects for s in action.subjects):
                    continue
            if les(locations) > 0:
                if action.location not in locations:
                    continue
            fr = action.require_filerecord()
            name = action.id.rstrip('-analysis')
            analysis_action.subjects.extend(list(action.subjects))
            contents = {}
            for key, val in action.modules.items():
                if 'channel_group' in key:
                    contents[key] = val
            analysis_action.require_module(name=name, contents=contents,
                                           overwrite=overwrite)

    @cli.command('spikesort')
    @click.argument('action-id', type=click.STRING)
    @click.option('--no-local',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    def spikesort(action_id, no_local):
        """Spikesort with klustakwik

        COMMAND: action-id: Provide action id to find exdir path"""
        import numpy as np
        from phycontrib.neo.model import NeoModel
        import logging
        import sys
        # anoying!!!!
        logger = logging.getLogger('phy')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)

        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        fr = action.require_filerecord()
        if not no_local:
            exdir_path = _get_local_path(fr, assert_exists=True)
        else:
            exdir_path = fr.server_path
        print('Spikesorting ', exdir_path)
        model = NeoModel(exdir_path)
        channel_groups = model.channel_groups
        for channel_group in channel_groups:
            if not channel_group == model.channel_group:
                model.load_data(channel_group)
            print('Sorting channel group {}'.format(channel_group))
            clusters = model.cluster(np.arange(model.n_spikes), model.channel_ids)
            model.save(spike_clusters=clusters)
