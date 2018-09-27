from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.tools.action import generate_templates, get_git_info, query_yes_no
from expipe_plugin_cinpla.tools import config


def attach_to_cli(cli):
    @cli.command('adjust',
                 short_help='Parse info about drive depth adjustment')
    @click.argument('subject-id',  type=click.STRING)
    @click.option('-d', '--date',
                  type=click.STRING,
                  help=('The date of the surgery format: "dd.mm.yyyyTHH:MM" ' +
                        'or "now".'),
                  )
    @click.option('-a', '--adjustment',
                  multiple=True,
                  callback=config.validate_adjustment,
                  help=('The adjustment amount on given anatomical location ' +
                        'given as <key num value unit>'),
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    @click.option('--index',
                  type=click.INT,
                  help=('Index for module name, this is found automatically ' +
                        'by default.'),
                  )
    @click.option('--init',
                  is_flag=True,
                  help='Initialize, retrieve depth from surgery.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the adjustment.',
                  )
    @click.option('-y', '--yes',
                  is_flag=True,
                  help='No query for correct adjustment.',
                  )
    def generate_adjustment(subject_id, date, adjustment, user, index, init,
                            overwrite, yes):
        if not init:
            assert len(adjustment) != 0, 'Missing option "-a" / "--adjustment".'
            assert date is not None, 'Missing option "-d" / "--date".'
        if init and date is None:
            date = 'now'
        DTIME_FORMAT = expipe.io.core.datetime_format
        if date == 'now':
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
        datestring = datetime.strftime(date, DTIME_FORMAT)
        project = expipe.require_project(PAR.USER_PARAMS['project_id'])
        if init:
            action = project.require_action(subject_id + '-adjustment')
        else:
            action = project.get_action(subject_id + '-adjustment')
        if index is None and not init:
            deltas = []
            for name in action.modules.keys():
                if name.endswith('adjustment'):
                    deltas.append(int(name.split('_')[0]))
            index = max(deltas) + 1
        if init:
            index = 0
            surgery = project.get_action(subject_id + '-surgery-implantation')
            sdict = surgery.modules.to_dict()
            templates_used = {
                key: mod for key, mod in PAR.MODULES['implantation'].items()
                if mod in sdict}
            prev_depth = {key: {pos_key: sdict[mod][pos_key][2]
                                for pos_key in sdict[mod]
                                if pos_key.startswith('position_')
                                and pos_key.split('_')[-1].isnumeric()}
                          for key, mod in templates_used.items()}
            for key, groups in prev_depth.items():
                for group, depth in groups.items():
                    if not isinstance(depth, pq.Quantity):
                        raise ValueError('Depth of implant ' +
                                         '"{} {} = {}"'.format(key, group, depth) +
                                         ' not recognized')
                    prev_depth[key][group] = depth.astype(float)
        else:
            prev_name = '{:03d}_adjustment'.format(index - 1)
            prev_depth = action.require_module(name=prev_name).to_dict()['depth']
        name = '{:03d}_adjustment'.format(index)
        assert isinstance(prev_depth, dict), 'Unable to retrieve previous depth.'
        adjustment_dict = {key: dict() for key in prev_depth}
        for key, num, val, unit in adjustment:
            pos_key = 'position_{}'.format(num)
            adjustment_dict[key][pos_key] = pq.Quantity(val, unit)
        adjustment = {key: {pos_key: adjustment_dict[key].get(pos_key) or 0 * pq.mm
                            for pos_key in prev_depth[key]}
                      for key in prev_depth}
        curr_depth = {key: {pos_key: round(prev_depth[key][pos_key] + val[pos_key], 3)
                            for pos_key in val}
                      for key, val in adjustment.items()} # round to um

        def last_num(x):
            return '%.3d' % int(x.split('_')[-1])
        correct = query_yes_no(
            'Correct adjustment?: \n' +
            ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                     for key, val in adjustment.items()
                     for pos_key in sorted(val, key=lambda x: last_num(x))) +
            'New depth: \n' +
            ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                     for key, val in curr_depth.items()
                     for pos_key in sorted(val, key=lambda x: last_num(x))),
            answer=yes
        )
        if not correct:
            print('Aborting adjustment.')
            return
        print(
            'Registering adjustment: \n' +
            ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                     for key, val in adjustment.items()
                     for pos_key in sorted(val, key=lambda x: last_num(x))) +
            ' New depth: \n' +
            ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                     for key, val in curr_depth.items()
                     for pos_key in sorted(val, key=lambda x: last_num(x)))
        )
        template_name = PAR.TEMPLATES.get('adjustment') or 'protocol_depth_adjustment'
        module = action.require_module(template=template_name,
                                       name=name, overwrite=overwrite)
        content = module.to_dict()
        content['depth'] = curr_depth
        content['adjustment'] = adjustment
        content['experimenter'] = user
        content['date'] = datestring
        content['git_note'] = get_git_info()
        action.require_module(name=name, contents=content, overwrite=True)

        action.type = 'Adjustment'
        action.subjects = [subject_id]
        user = user or PAR.USER_PARAMS['user_name']
        user = user or []
        if len(user) == 0:
            raise ValueError('Please add user name')
        action.users = [user]
