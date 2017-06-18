import expipe
import os
import os.path as op
from expipecli.utils import IPlugin
import click
from .action_tools import (generate_templates, _get_local_path, create_notebook,
                           GIT_NOTE, nwb_main_groups)
import sys
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import (USER_PARAMS, TEMPLATES, UNIT_INFO, POSSIBLE_TAGS,
                              POSSIBLE_LOCATIONS, OBLIGATORY_TAGS)

DTIME_FORMAT = expipe.io.core.datetime_format


class CinplaPlugin(IPlugin):
    """Create the `expipe parse-axona` command for neuro recordings."""
    def attach_to_cli(self, cli):
        @cli.command('generate-notebook')
        @click.argument('action-id', type=click.STRING)
        @click.option('--no_local',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--channel-group',
                      type=click.INT,
                      help='Which channel-group to plot.',
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
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(action_id)
            fr = action.require_filerecord()
            if not no_local:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.server_path
            fname = create_notebook(exdir_path)
            if run:
                import subprocess
                subprocess.run(['jupyter', 'notebook', fname])

        @cli.command('copy-to-config')
        @click.argument('filename', type=click.Path(exists=True))
        def copy_to_config(filename):
            import shutil
            """Copy file to expipe config directory"""
            shutil.copy(filename, expipe.config.config_dir)

        @cli.command('register-surgery')
        @click.argument('subject-id')
        @click.option('--date', '-d',
                      required=True,
                      type=click.STRING,
                      help='The date of the surgery format: "dd.mm.yyyyTHH:MM".',
                      )
        @click.option('--procedure',
                      required=True,
                      type=click.STRING,
                      help='The type of surgery "implantation" or "injection".',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('-u', '--user',
                      type=click.STRING,
                      help='The experimenter performing the surgery.',
                      )
        @click.option('--weight',
                      required=True,
                      type=click.FLOAT,
                      help='The weight of the subject in grams.',
                      )
        @click.option('--birthday',
                      required=True,
                      type=click.STRING,
                      help='The birthday of the subject, format: "dd.mm.yyyy".',
                      )
        @click.option('-a', '--anatomy',
                      multiple=True,
                      required=True,
                      type=(click.STRING, float),
                      help='The adjustment amount on given anatomical location in "um".',
                      )
        def generate_surgery(subject_id, procedure, date, user, weight, birthday,
                             overwrite, anatomy):
            """Generate a surgery action."""
            # TODO give depth if implantation
            import quantities as pq
            from datetime import datetime
            if procedure not in ["implantation", "injection"]:
                raise ValueError('procedure must be one of "implantation" ' +
                                 'or "injection"')
            birthday = datetime.strptime(birthday, '%d.%m.%Y')
            birthday = datetime.strftime(birthday, DTIME_FORMAT)
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(subject_id + '-surgery-' + procedure)
            action.location = 'Sterile surgery station'
            action.type = 'Surgery'
            action.tags = [procedure]
            action.subjects = [subject_id]
            user = user or USER_PARAMS['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')
            action.users = [user]
            action.datetime = date
            generate_templates(action, TEMPLATES['surgery_' + procedure],
                               overwrite, git_note=GIT_NOTE)
            modules_dict = action.modules.to_dict()
            for key, val in anatomy:
                name = MODULES[procedure][key]
                mod = modules_dict[modules_dict[name]}
                assert 'position' in mod
                assert isinstance(mod['position'], pq.Quantity)
                mod['position'][2] = position
                print('Registering depth ', key, ' = ', mod['depth'])
                action.require_module(name=name, contents=mod, overwrite=True)

            subject = action.require_module(name=MODULES['subject']).to_dict()  # TODO standard name?
            subject['birthday']['value'] = birthday
            subject['weight'] = weight * pq.g
            action.require_module(name=MODULES['subject'], contents=subject,
                                  overwrite=True)

        @cli.command('transfer')
        @click.argument('action-id', type=click.STRING)
        @click.option('--to-local',
                      is_flag=True,
                      help='Transfer action data from server to local directory.',
                      )
        @click.option('--from-local',
                      is_flag=True,
                      help='Transfer action data from local directory to server.',
                      )
        @click.option('--no-trash',
                      is_flag=True,
                      help='Do not send local data to trash after transfer.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite data or not.',
                      )
        @click.option('--raw',
                      is_flag=True,
                      help='Transfer without tags etc.',
                      )
        @click.option('--merge',
                      is_flag=True,
                      help='Merge with existing, overwriting equal files.',
                      )
        @click.option('-r', '--recursive',
                      is_flag=True,
                      help='Recursive directory transfer.',
                      )
        @click.option('-m', '--message',
                      type=click.STRING,
                      help='Add message, use "text here" for sentences.',
                      )
        @click.option('-e', '--exclude',
                      multiple=True,
                      type=click.Choice(nwb_main_groups),
                      help='Omit raw data, acquisition etc..',
                      )
        @click.option('-i', '--include',
                      multiple=True,
                      type=click.Choice(nwb_main_groups),
                      help='Only select which folders to include.',
                      )
        @click.option('--port',
                      default=22,
                      type=click.INT,
                      help='SSH port. Default is 22',
                      )
        @click.option('--hostname',
                      type=click.STRING,
                      help='SSH hostname.',
                      )
        @click.option('--username',
                      type=click.STRING,
                      help='SSH username.',
                      )
        @click.option('--server',
                      default='norstore',
                      type=click.STRING,
                      help='Name of server as named in config.yaml. Default is "norstore"',
                      )
        def transfer(action_id, to_local, from_local, overwrite, no_trash,
                     message, raw, exclude, include, merge, port, username,
                     hostname, recursive, server):
            """Transfer a dataset related to an expipe action

            COMMAND: action-id: Provide action id to find exdir path"""
            assert server in expipe.config.settings
            server_dict = expipe.config.settings.get(server)
            if len(exclude) > 0 and len(include) > 0:
                raise IOError('You can only use exlude or include')
            from .ssh_tools import get_login, login, ssh_execute, untar
            import tarfile
            import shutil
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(action_id)
            action.messages.extend([{'message': m,
                                     'user': user,
                                     'datetime': datetime.now()}
                                   for m in message])
            fr = action.require_filerecord()

            host, user, pas, port = get_login(hostname=hostname,
                                              username=username,
                                              port=port,
                                              server=server_dict)
            ssh, scp_client, sftp_client, pbar = login(hostname=host,
                                                       username=user,
                                                       password=pas, port=port)
            serverpath = expipe.config.settings[server]['data_path']
            server_data = op.dirname(op.join(serverpath, fr.exdir_path))
            server_data = server_data.replace('\\', '/')
            if to_local:
                local_data = op.dirname(_get_local_path(fr, make=True))
                if recursive:
                    scp_client.get(server_data, local_data, recursive=True)
                    try:
                        pbar[0].close()
                    except Exception:
                        pass
                else:
                    if overwrite:
                        shutil.rmtree(local_data)
                        os.mkdir(local_data)
                    print('Initializing transfer of "' + server_data + '" to "' +
                          local_data + '"')
                    print('Packing tar archive')
                    exclude_statement = " "
                    for ex in exclude:
                        exclude_statement += '--exclude=' + ex + ' '
                    if len(include) > 0:
                        for ex in nwb_main_groups:
                            if ex not in include:
                                exclude_statement += '--exclude=' + ex + ' '
                    ssh_execute(ssh, "tar" + exclude_statement + "-cf " +
                                server_data + '.tar ' + server_data)
                    scp_client.get(server_data + '.tar', local_data + '.tar',
                                   recursive=False)
                    try:
                        pbar[0].close()
                    except Exception:
                        pass
                    print('Unpacking tar archive')
                    untar(local_data + '.tar', server_data) # TODO merge with existing
                    print('Deleting tar archives')
                    os.remove(local_data + '.tar')
                    sftp_client.remove(server_data + '.tar')
            elif from_local:
                local_data = op.dirname(_get_local_path(fr, assert_exists=True))
                if not raw:
                    tags = action.tags or list()
                    if len(OBLIGATORY_TAGS) > 0:
                        if sum([tag in tags for tag in OBLIGATORY_TAGS]) != 1:
                            raise ValueError('Tags are not approved, please revise')
                if recursive:
                    scp_client.get(server_data, local_data, recursive=True)
                    try:
                        pbar[0].close()
                    except Exception:
                        pass
                else:
                    print('Initializing transfer of "' + local_data + '" to "' +
                          server_data + '"')
                    try: # make directory for untaring
                        sftp_client.mkdir(server_data)
                    except IOError:
                        pass
                    if len(exclude) > 0 or len(include) > 0:
                        raise NotImplementedError
                    print('Packing tar archive')
                    shutil.make_archive(local_data, 'tar', local_data)
                    scp_client.put(local_data + '.tar', server_data + '.tar',
                                   recursive=False)
                    try:
                        pbar[0].close()
                    except Exception:
                        pass
                    print('Unpacking tar archive')
                    cmd = "tar -C " + server_data + " -xf " + server_data + '.tar'
                    if not overwrite:
                        cmd += " -k --skip-old-files"
                    else:
                        cmd += " -k --overwrite"
                    ssh_execute(ssh, cmd)
                    print('Deleting tar archives')
                    sftp_client.remove(server_data + '.tar')
                    os.remove(local_data + '.tar')
                if not no_trash:
                    try:
                        from send2trash import send2trash
                        send2trash(local_data)
                        print('local data "' + local_data +
                              '" sent to trash.')
                    except Exception:
                        import warnings
                        warnings.warn('Unable to send local data to trash')

            else:
                raise IOError('You must choose "to-local" or "from-local"')
            ssh.close()
            sftp_client.close()
            scp_client.close()
            # TODO send to trash

        @cli.command('copy-action')
        @click.argument('action-id', type=click.STRING)
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--to-local',
                      is_flag=True,
                      help='',
                      )
        @click.option('--from-local',
                      is_flag=True,
                      help='Transfer action data from local directory to server.',
                      )
        @click.option('--move',
                      is_flag=True,
                      help='Delete source.',
                      )
        @click.option('--exclude',
                      type=click.Choice(['acquisition', 'analysis', 'processing',
                                         'epochs', 'none']),
                      default='none',
                      help='Omit raw data, acquisition etc..',
                      )
        def copy_action(action_id, to_local, from_local, overwrite, exclude, move):
            """Transfer a dataset related to an expipe action
            COMMAND: action-id: Provide action id to find exdir path"""
            import shutil
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(action_id)
            fr = action.require_filerecord()
            if to_local:
                source = fr.server_path
                dest = _get_local_path(fr)
            elif from_local:
                dest = fr.server_path
                source = _get_local_path(fr)
            else:
                raise IOError('You must choose "to-local" or "from-local"')
            print('Copying "' + source + '" to "' + dest + '"')
            if not op.exists(source):
                raise FileExistsError('Source file does not exist')
            if op.exists(dest):
                if overwrite:
                    shutil.rmtree(dest)
                else:
                    raise FileExistsError('Destination "' + dest +
                                          '" exist, use overwrite flag')
            if exclude != 'none':
                print('Ignoring "' + exclude + '"')

            def exclude_dir(src, names):
                if src.endswith('main.exdir') and exclude != 'none':
                    return [exclude]
                else:
                    return set()

            shutil.copytree(source, dest, ignore=exclude_dir)  # TODO write progress
            if move:
                shutil.rmtree(source)


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

            project = expipe.get_project(USER_PARAMS['project_id'])
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

        @cli.command('annotate')
        @click.argument('action-id', type=click.STRING)
        @click.option('--tag', '-t',
                      multiple=True,
                      type=click.Choice(POSSIBLE_TAGS),
                      help='The tag to be applied to the action.',
                      )
        @click.option('--message', '-m',
                      multiple=True,
                      type=click.STRING,
                      help='Add message, use "text here" for sentences.',
                      )
        @click.option('-u', '--user',
                      type=click.STRING,
                      help='The experimenter performing the annotation.',
                      )
        def annotate(action_id, tag, message, user):
            """Parse info about recorded units

            COMMAND: action-id: Provide action id to get action"""
            from datetime import datetime
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(action_id)
            user = user or USER_PARAMS['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')

            users = list(set(action.users))
            if user not in users:
                users.append(user)
            action.users = users
            action.messages.extend([{'message': m,
                                     'user': user,
                                     'datetime': datetime.now()}
                                   for m in message])
            action.tags.extend(tag)

        @cli.command('register-units')
        @click.argument('action-id', type=click.STRING)
        @click.option('--no-local',
                      is_flag=True,
                      help='Store on local drive.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--channel-group',
                      type=click.INT,
                      help='Which channel-group to plot.',
                      )
        @click.option('--tag', '-t',
                      required=True,
                      multiple=True,
                      type=click.Choice(POSSIBLE_TAGS),
                      help='The anatomical brain-area of the optogenetic stimulus.',
                      )
        @click.option('-m', '--message',
                      multiple=True,
                      required=True,
                      type=click.STRING,
                      help='Add message, use "text here" for sentences.',
                      )
        @click.option('-u', '--user',
                      type=click.STRING,
                      help='The experimenter performing the adjustment.',
                      )
        def register_units(action_id, no_local, channel_group, overwrite, tag,
                           message, user):
            """Parse info about recorded units

            COMMAND: action-id: Provide action id to find exdir path"""
            import neo
            import copy
            from datetime import datetime
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(action_id)
            user = user or USER_PARAMS['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')

            users = list(set(action.users))
            if user not in users:
                users.append(user)
            action.users = users
            action.tags.update(tag)
            action.messages.extend([{'message': m,
                                     'user': user,
                                     'datetime': datetime.now()}
                                   for m in message])
            fr = action.require_filerecord()
            if not no_local:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.server_path
            io = neo.io.ExdirIO(exdir_path)
            blk = io.read_block()
            for chx in blk.channel_indexes:
                contents = {}
                group_id = chx.annotations['group_id']
                if channel_group is None:
                    pass
                elif channel_group != group_id:
                    continue
                for unit in chx.units:
                    sptr = unit.spiketrains[0]
                    if sptr.annotations['cluster_group'].lower() == 'noise':
                        continue
                    attrs = copy.copy(UNIT_INFO)
                    attrs.update(sptr.annotations)
                    if sptr.name is None:
                        sptr.name = 'Unit_{}'.format(sptr.annotations['cluster_id'])
                    name = sptr.name.replace(' ', '_').replace('#', '')
                    assert group_id == sptr.annotations['electrode_group_id']
                    contents[name] = attrs
                modname = 'channel_group_' + str(group_id)
                action.require_module(name=modname,
                                      contents=contents, overwrite=overwrite)
                print('Adding module ', modname)
            contents.update({'git_note': GIT_NOTE})

        @cli.command('adjust')
        @click.argument('subject-id',  type=click.STRING)
        @click.option('-d', '--date',
                      required=True,
                      type=click.STRING,
                      help='The date of the surgery format: "dd.mm.yyyyTHH:MM" or "now".',
                      )
        @click.option('-a', '--anatomy',
                      multiple=True,
                      required=True,
                      type=(click.STRING, int),
                      help='The adjustment amount on given anatomical location in "um".',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--index',
                      type=click.INT,
                      help='Index for module name, this is found automatically by default.',
                      )
        @click.option('--init',
                      is_flag=True,
                      help='Initialize, retrieve depth from surgery.',
                      )
        @click.option('-u', '--user',
                      type=click.STRING,
                      help='The experimenter performing the adjustment.',
                      )
        def generate_adjustment(subject_id, date, anatomy, user, index, init,
                                overwrite):
            """Parse info about drive depth adjustment

            COMMAND: subject-id: ID of the subject."""
            import numpy as np
            import quantities as pq
            from .action_tools import query_yes_no
            from datetime import datetime
            if date == 'now':
                date = datetime.now()
            else:
                date = datetime.strptime(date, '%d.%m.%YT%H:%M')
            datestring = datetime.strftime(date, DTIME_FORMAT)
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(subject_id + '-adjustment')
            action.type = 'Adjustment'
            action.subjects = [subject_id]
            user = user or USER_PARAMS['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')
            users = list(set(action.users))
            if user not in users:
                users.append(user)
            action.users = users
            if index is None and not init:
                deltas = []
                for name in action.modules.keys():
                    if not name.endswith('adjustment'):
                        continue
                    deltas.append(int(name.split('_')[0]))
                index = max(deltas) + 1
            if init:
                index = 0
                surgery = project.get_action(subject_id + '-surgery-implantation')
                sdict = surgery.modules.to_dict()
                prev_depth = {key: sdict[MODULES['implantation'][key]]['position'][2]
                              for key, _ in anatomy}
                for key, depth in prev_depth:
                    if not np.isfinite(depth):
                        raise ValueError('Depth of left implant ' +
                                         '"{}={}" not recognized'.format(key, depth))
            else:
                prev_name = '{:.3d}_adjustment'.format(index - 1)
                prev_dict = action.require_module(name=prev_name).to_dict()
                prev_depth = {key: prev_dict['depth'][key] for key, _ in anatomy}
            name = '%.3d_adjustment' % index
            module = action.require_module(template=TEMPLATES['adjustment'],
                                           name=name, overwrite=overwrite)

            curr_depth = {key: round(prev_dict['depth'][key] + val * pq.um, 3)
                          for key, val in anatomy} # round to um
            curr_adjustment = {key: val * pq.um for key, val in anatomy}
            answer = query_yes_no(
                'Correct adjustment: ' +
                ' '.join('{} = {}'.format(key, val) for key, val in curr_adjustment.items()) +
                '? New depth: ' +
                ' '.join('{} = {}'.format(key, val) for key, val in curr_depth.items())
            )
            if answer == False:
                print('Aborting adjustment')
                return
            print(
                'Registering adjustment: ' +
                ' '.join('{} = {}'.format(key, val) for key, val in anatomy) +
                ' New depth: ' +
                ' '.join('{} = {}'.format(key, val) for key, val in curr_depth.items())
            )
            content = module.to_dict()
            content['depth'] = curr_depth
            content['adjustment'] = curr_adjustment
            content['experimenter'] = user
            content['date'] = datestring
            content['git_note'] = GIT_NOTE
            action.require_module(name=name, contents=content, overwrite=True)

        @cli.command('analyse')
        @click.argument('action-id', type=click.STRING)
        @click.option('--channel-group',
                      type=click.INT,
                      help='Which channel-group to plot.',
                      )
        @click.option('--no-local',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--spike-stat',
                      is_flag=True,
                      help='Plot spike statistics.',
                      )
        @click.option('--spatial',
                      is_flag=True,
                      help='Plot spatial overview.',
                      )
        @click.option('--psd',
                      is_flag=True,
                      help='Plot power spectrum density.',
                      )
        @click.option('--spike-lfp',
                      is_flag=True,
                      help='Plot spike lfp coherence.',
                      )
        @click.option('--tfr',
                      is_flag=True,
                      help='Plot time frequency representation.',
                      )
        @click.option('--stim-stat',
                      is_flag=True,
                      help='Plot stimulation statistics.',
                      )
        @click.option('--occupancy',
                      is_flag=True,
                      help='Plot occupancy matrix.',
                      )
        @click.option('--all',
                      is_flag=True,
                      help='Plot all.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite.',
                      )
        @click.option('--skip',
                      is_flag=True,
                      help='Skip previously generated files.',
                      )
        @click.option('--orient-tuning',
                      is_flag=True,
                      help='Plot orientation tuning overview.',
                      )
        def plotting(**kwargs):
            """Analyse a dataset

            COMMAND: action-id: Provide action id to find exdir path"""
            from .plotter import Plotter
            # TODO add exana version and git note
            if isinstance(kwargs['channel_group'], int):
                kwargs['channel_group'] = [kwargs['channel_group']]
            project = expipe.get_project(USER_PARAMS['project_id'])
            action = project.require_action(kwargs['action_id'])
            plot = Plotter(kwargs['action_id'],
                           channel_group=kwargs['channel_group'],
                           no_local=kwargs['no_local'],
                           overwrite=kwargs['overwrite'],
                           skip=kwargs['skip'])
            if kwargs['stim_stat'] or kwargs['all']:
                plot.stimulation_statistics()
            if kwargs['occupancy'] or kwargs['all']:
                plot.occupancy()
            if kwargs['spatial'] or kwargs['all']:
                plot.spatial_overview()
            if kwargs['spike_stat'] or kwargs['all']:
                plot.spike_statistics()
            if kwargs['psd'] or kwargs['all']:
                plot.psd()
            if kwargs['spike_lfp'] or kwargs['all']:
                plot.spike_lfp_coherence()
            if kwargs['tfr']:
                plot.tfr()
            if kwargs['orient_tuning']:
                plot.orient_tuning_overview()
            ## do not use:
            # plot.spatial_stim_overview()

        @cli.command('generate-analysis-action')
        @click.argument('action-id', type=click.STRING)
        @click.option('-u', '--user',
                      type=click.STRING,
                      help='The experimenter performing the analysis.',
                      )
        @click.option('-t', '--tag',
                      multiple=True,
                      type=click.STRING,
                      help='Tags to sort the analysis.',
                      )
        @click.option('-s', '--subject',
                      multiple=True,
                      type=click.STRING,
                      help='Subjects to sort the analysis.',
                      )
        @click.option('-l', '--location',
                      multiple=True,
                      type=click.STRING,
                      help='Subjects to sort the analysis.',
                      )
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite.',
                      )
        def generate_analysis(action_id, user, tag, overwrite):
            """Parse info about recorded units

            COMMAND: action-id: Provide action id to get action"""
            from datetime import datetime
            project = expipe.get_project(USER_PARAMS['project_id'])
            analysis_action = project.require_action(action_id)

            analysis_action.type = 'Analysis'
            user = user or USER_PARAMS['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')
            users = analysis_action.users or list()
            if user not in users:
                users.append(user)
            analysis_action.users = users
            subjects = {}
            analysis_action.tags = tag
            for action in project.actions:
                if action.type != 'Recording':
                    continue
                if action.tags is None:
                    raise ValueError('No tags in "' + action.id + '"')
                if not any(t in tag for t in action.tags.keys()):
                    continue
                fr = action.require_filerecord()
                name = action.id
                subjects.update(action.subjects)
                contents = {}
                for key, val in action.modules.items():
                    if 'channel_group' in key:
                        contents[key] = val
                analysis_action.require_module(name=name, contents=contents,
                                               overwrite=overwrite)
            analysis_action.subjects = subjects
