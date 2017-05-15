import expipe
import expipe.io
import os
import os.path as op
from expipecli.utils import IPlugin
import click
from .action_tools import (generate_templates, _get_local_path, create_notebook,
                           GIT_NOTE)
import sys
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import (user_params, templates, unit_info, possible_tags,
                              possible_locations, obligatory_tags)

DTIME_FORMAT = expipe.io.core.datetime_format


class CinplaPlugin(IPlugin):
    """Create the `expipe parse-axona` command for neuro recordings."""
    def attach_to_cli(self, cli):
        @cli.command('generate-notebook')
        @click.argument('action-id', type=click.STRING)
        @click.option('--no_temp',
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
        def generate_notebook(action_id, channel_group, no_temp, run):
            """
            Provide action id to find exdir path

            COMMAND: action-id: Provide action id to find exdir path
            """
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            fr = action.require_filerecord()
            if not no_temp:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.local_path
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
        @click.option('--rat',
                      required=True,
                      type=click.STRING,
                      help='ID of the rat.',
                      )
        @click.option('--date', '-d',
                      required=True,
                      type=click.STRING,
                      help='The date of the surgery format: "dd.mm.yyyy:HH:MM".',
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
        @click.option('--user',
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
                      help='The birthday of the subject.',
                      )
        def generate_surgery(rat, procedure, date, user, weight, birthday,
                             overwrite):
            """Generate a surgery action."""
            # TODO give depth if implantation
            import quantities as pq
            from datetime import datetime
            if procedure not in ["implantation", "injection"]:
                raise ValueError('procedure must be one of "implantation" ' +
                                 'or "injection"')
            birthday = datetime.strptime(birthday, '%d.%m.%Y')
            birthday = datetime.strftime(birthday, DTIME_FORMAT)
            date = datetime.strptime(date, '%d.%m.%Y:%H:%M')
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(rat + '-surgery-' + procedure)
            action.location = 'Sterile surgery station'
            action.type = 'Surgery'
            action.tags = {procedure: 'true'}
            action.subjects = {rat: 'true'}
            user = user or user_params['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')
            action.users = {user: 'true'}
            action.datetime = date
            generate_templates(action, templates['surgery_' + procedure],
                               overwrite, git_note=GIT_NOTE)
            subject = action.require_module(name='subject').to_dict()  # TODO standard name?
            subject['birthday']['value'] = birthday
            subject['weight'] = weight * pq.g
            action.require_module(name='subject', contents=subject,
                                  overwrite=True)

        @cli.command('transfer')
        @click.argument('action-id', type=click.STRING)
        @click.option('--to-temp',
                      is_flag=True,
                      help='Transfer action data from server to local directory.',
                      )
        @click.option('--from-temp',
                      is_flag=True,
                      help='Transfer action data from local directory to server.',
                      )
        @click.option('--no-tar',
                      is_flag=True,
                      help='Compress before transfer.',
                      )
        @click.option('--no-trash',
                      is_flag=True,
                      help='Do not send temp data to trash after transfer.',
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
        @click.option('--note',
                      type=click.STRING,
                      help='Add note, use "text here" for sentences.',
                      )
        @click.option('-i', '--ignore',
                      multiple=True,
                      type=click.Choice(['acquisition', 'analysis', 'processing',
                                         'epochs', 'none']),
                      help='Omit raw data, acquisition etc..',
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
        def transfer(action_id, to_temp, from_temp, no_tar, overwrite, no_trash,
                     note, raw, ignore, merge, port, username, hostname):
            """Transfer a dataset related to an expipe action

            COMMAND: action-id: Provide action id to find exdir path"""
            from .ssh_tools import get_login, login, ssh_execute, untar
            if not no_tar:
                import tarfile
                import shutil
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            if note is not None:
                notes = action.require_module(name='notes').to_dict()
                notes['transfer_note'] = {'value': note}
                action.require_module(name='notes', contents=notes,
                                      overwrite=True)
            fr = action.require_filerecord()

            host, user, pas, port = get_login(hostname=hostname,
                                              username=username,
                                              port=port)
            ssh, scp_client, sftp_client, pbar = login(hostname=host,
                                                       username=user,
                                                       password=pas, port=port)
            serverpath = expipe.config.settings['server']['data_path']
            server_data = op.dirname(op.join(serverpath, fr.exdir_path))
            server_data = server_data.replace('\\', '/')
            temp_data = op.dirname(_get_local_path(fr))
            if to_temp:
                if overwrite:
                    shutil.rmtree(temp_data)
                    os.mkdir(temp_data)
                print('Initializing transfer of "' + server_data + '" to "' +
                      temp_data + '"')
                print('Packing tar archive')
                ignore_statement = " "
                for ig in ignore:
                    ignore_statement += '--exclude=' + ig + ' '
                ssh_execute(ssh, "tar" + ignore_statement + "-cf " +
                            server_data + '.tar ' + server_data)
                scp_client.get(server_data + '.tar', temp_data + '.tar',
                               recursive=False)
                try:
                    pbar[0].close()
                except Exception:
                    pass
                print('Unpacking tar archive')
                untar(temp_data + '.tar', server_data) # TODO merge with existing
                print('Deleting tar archives')
                os.remove(temp_data + '.tar')
                sftp_client.remove(server_data + '.tar')
            elif from_temp:
                if not raw:
                    tags = action.tags or {}
                    if len(obligatory_tags) > 0:
                        if sum([tag in tags for tag in obligatory_tags]) != 1:
                            raise ValueError('Tags are not approved, please revise')
                print('Initializing transfer of "' + temp_data + '" to "' +
                      server_data + '"')
                try: # make directory for untaring
                    sftp_client.mkdir(server_data)
                except IOError:
                    pass
                if len(ignore) > 0:
                    raise NotImplementedError
                print('Packing tar archive')
                shutil.make_archive(temp_data, 'tar', temp_data)
                scp_client.put(temp_data + '.tar', server_data + '.tar',
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
                os.remove(temp_data + '.tar')
                if not no_trash:
                    try:
                        from send2trash import send2trash
                        send2trash(temp_data)
                        print('Temp data "' + temp_data +
                              '" sent to trash.')
                    except Exception:
                        import warnings
                        warnings.warn('Unable to send temporay data to trash')

            else:
                raise IOError('You must choose "to-temp" or "from-temp"')
            ssh.close()
            sftp_client.close()
            scp_client.close()
            # TODO send to trash


        @cli.command('copy')
        @click.argument('action-id', type=click.STRING)
        @click.option('--overwrite',
                      is_flag=True,
                      help='Overwrite modules or not.',
                      )
        @click.option('--to-temp',
                      is_flag=True,
                      help='',
                      )
        @click.option('--from-temp',
                      is_flag=True,
                      help='Transfer action data from local directory to server.',
                      )
        @click.option('--move',
                      is_flag=True,
                      help='Delete source.',
                      )
        @click.option('--ignore',
                      type=click.Choice(['acquisition', 'analysis', 'processing',
                                         'epochs', 'none']),
                      default='none',
                      help='Omit raw data, acquisition etc..',
                      )
        def copy(action_id, to_temp, from_temp, overwrite, ignore, move):
            """Transfer a dataset related to an expipe action
            COMMAND: action-id: Provide action id to find exdir path"""
            import shutil
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            fr = action.require_filerecord()
            if to_temp:
                source = fr.local_path
                dest = _get_local_path(fr)
            elif from_temp:
                dest = fr.local_path
                source = _get_local_path(fr)
            else:
                raise IOError('You must choose "to-temp" or "from-temp"')
            print('Copying "' + source + '" to "' + dest + '"')
            if not op.exists(source):
                raise FileExistsError('Source file does not exist')
            if op.exists(dest):
                if overwrite:
                    shutil.rmtree(dest)
                else:
                    raise FileExistsError('Destination "' + dest +
                                          '" exist, use overwrite flag')
            if ignore != 'none':
                print('Ignoring "' + ignore + '"')

            def ignore_dir(src, names):
                if src.endswith('main.exdir') and ignore != 'none':
                    return [ignore]
                else:
                    return set()

            shutil.copytree(source, dest, ignore=ignore_dir)  # TODO write progress
            if move:
                shutil.rmtree(source)


        @cli.command('spikesort')
        @click.argument('action-id',
                        type=click.STRING,
                        )
        @click.option('--no-temp',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        @click.option('--debug',
                      is_flag=True,
                      help='Store temporary on local drive.',
                      )
        def spikesort(action_id, no_temp, debug):
            """Spikesort with klustakwik

            COMMAND: action-id: Provide action id to find exdir path"""
            import numpy as np
            if debug:
                import logging.config
                logging.basicConfig(level=logging.DEBUG)
            from phycontrib.neo.model import NeoModel
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            fr = action.require_filerecord()
            if not no_temp:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.local_path
            print('Spikesorting ', exdir_path)
            model = NeoModel(exdir_path)
            channel_groups = model.channel_groups
            for channel_group in channel_groups:
                if not channel_group == model.channel_group:
                    model.load_data(channel_group)
                print('Sorting channel group {}'.format(channel_group))
                clusters = model.cluster(np.arange(model.n_spikes), model.channel_ids)
                model.save(spike_clusters=clusters)

        @cli.command('register-units')
        @click.argument('action-id', type=click.STRING)
        @click.option('--no-temp',
                      is_flag=True,
                      help='Store temporary on local drive.',
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
                      type=click.Choice(possible_tags),
                      help='The anatomical brain-area of the optogenetic stimulus.',
                      )
        @click.option('--note',
                      type=click.STRING,
                      help='Add note, use "text here" for sentences.',
                      )
        def register_units(action_id, no_temp, channel_group, overwrite, tag,
                           note):
            """Parse info about recorded units

            COMMAND: action-id: Provide action id to find exdir path"""
            import neo
            import copy
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            if note is not None:
                notes = action.require_module(name='notes').to_dict()
                notes['unit_note'] = {'value': note}
                action.require_module(name='notes', contents=notes,
                                      overwrite=True)
            tags = action.tags or {}
            tags.update({t: 'true' for t in tag})
            action.tags = tags

            fr = action.require_filerecord()
            if not no_temp:
                exdir_path = _get_local_path(fr)
            else:
                exdir_path = fr.local_path
            print(exdir_path)
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
                    attrs = copy.copy(unit_info)
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
        @click.argument('rat-id',  type=click.STRING)
        @click.option('-d', '--date',
                      required=True,
                      type=click.STRING,
                      help='The date of the surgery format: "dd.mm.yyyy:HH:MM" or "now".',
                      )
        @click.option('-l', '--left',
                      required=True,
                      type=click.INT,
                      help='The adjustment amount on left side in "um".',
                      )
        @click.option('-r', '--right',
                      required=True,
                      type=click.INT,
                      help='The adjustment amount on right side in "um".',
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
        @click.option('--user',
                      type=click.STRING,
                      help='The experimenter performing the adjustment.',
                      )
        def generate_adjustment(rat_id, date, left, right, user, index, init,
                                overwrite):
            """Parse info about drive depth adjustment

            COMMAND: rat-id: ID of the rat."""
            import numpy as np
            import quantities as pq
            from .action_tools import query_yes_no
            from datetime import datetime
            if date == 'now':
                date = datetime.now()
            else:
                date = datetime.strptime(date, '%d.%m.%Y:%H:%M')
            datestring = datetime.strftime(date, DTIME_FORMAT)
            left = left * pq.um
            right = right * pq.um
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(rat_id + '-adjustment')
            action.type = action.type or 'Adjustment'
            action.subjects = action.subjects or {rat_id: 'true'}
            user = user or user_params['user_name']
            if user is None:
                raise ValueError('Please add user name')
            if len(user) == 0:
                raise ValueError('Please add user name')
            users = action.users or dict()
            if user not in users:
                users.update({user: 'true'})
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
                surgery = project.get_action(rat_id + '-surgery-implantation')
                sdict = surgery.modules.to_dict()
                sleft = sdict['implant_drive_L']['position'][2]
                sright = sdict['implant_drive_R']['position'][2]
                if not np.isfinite(sleft):
                    raise ValueError('Depth of left implant ' +
                                     '"{}" not recognized'.format(sleft))
                if not np.isfinite(sright):
                    raise ValueError('Depth of left implant ' +
                                     '"{}" not recognized'.format(sright))
                prev_dict = {'depth': [sleft, sright]}
            else:
                prev_name = '%.3d_adjustment' % (index - 1)
                prev_dict = action.require_module(name=prev_name).to_dict()
                assert prev_dict['location'].lower() == 'left, right'
            name = '%.3d_adjustment' % index
            module = action.require_module(template=templates['adjustment'],
                                           name=name, overwrite=overwrite)
            left_depth = round(prev_dict['depth'][0] + left.rescale('mm'), 3) # round to um
            right_depth = round(prev_dict['depth'][1] + right.rescale('mm'), 3)
            answer = query_yes_no(
                'Correct adjustment: left = {}, right = {}?'.format(left, right) +
                ' New depth: left = {}, right = {}'.format(left_depth, right_depth))
            if answer == False:
                print('Aborting adjustment')
                return
            print('Registering adjustment left = {}, new depth = {}.'.format(left, left_depth))
            print('Registering adjustment right = {}, new depth = {}.'.format(right, right_depth))
            content = module.to_dict()
            content['depth'] = np.array([left_depth, right_depth]) * pq.mm
            content['adjustment'] = np.array([left, right]) * pq.um
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
        @click.option('--no-temp',
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
        def plotting(**kwargs):
            """Analyse a dataset

            COMMAND: action-id: Provide action id to find exdir path"""
            from .plotter import Plotter
            # TODO add exana version and git note
            if isinstance(kwargs['channel_group'], int):
                kwargs['channel_group'] = [kwargs['channel_group']]
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(kwargs['action_id'])
            plot = Plotter(kwargs['action_id'],
                           channel_group=kwargs['channel_group'],
                           no_temp=kwargs['no_temp'],
                           overwrite=kwargs['overwrite'],
                           skip=kwargs['skip'])
            if kwargs['stim_stat'] or kwargs['all']:
                plot.stimulation_statistics()
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
            ## do not use:
            # plot.spatial_stim_overview()

        @cli.command('note')
        @click.argument('action-id', type=click.STRING)
        @click.option('--note', '-n',
                      type=click.STRING,
                      help='Add note, use "text here" for sentences.',
                      )
        def register_units(action_id, note):
            """Parse info about recorded units

            COMMAND: action-id: Provide action id to get action"""
            project = expipe.io.get_project(user_params['project_id'])
            action = project.require_action(action_id)
            if note is not None:
                notes = action.require_module(name='notes').to_dict()
                idx = []
                for name in notes.keys():
                    try:
                        idx.append(int(name.split('_')[-1]))
                    except Exception:
                        continue
                if len(idx) == 0:
                    idx = 0
                else:
                    idx = max(idx)
                notes['note_{}'.format(idx)] = {'value': note}
                action.require_module(name='notes', contents=notes,
                                      overwrite=True)
