from expipecli.utils.misc import lazy_import
from .action_tools import (generate_templates, _get_local_path, create_notebook,
                           get_git_info, query_yes_no)
from .pytools import deep_update, load_python_module, load_parameters
import click

@lazy_import
def expipe():
    import expipe
    return expipe

@lazy_import
def warnings():
    import warnings
    return warnings

@lazy_import
def datetime():
    from datetime import datetime
    return datetime

@lazy_import
def pq():
    import quantities as pq
    return pq

@lazy_import
def np():
    import numpy as np
    return np

@lazy_import
def PAR():
    PAR = load_parameters()
    return PAR


def validate_position(ctx, param, position):
    try:
        out = []
        for pos in position:
            key, x, y, z, unit = pos.split(',', 5)
            out.append((key, float(x), float(y), float(z), unit))
        return tuple(out)
    except ValueError:
        raise click.BadParameter('Position need to be comma separated i.e ' +
                                 '<key,x,y,z,physical_unit> (ommit <>).')


def attach_to_cli(cli):
    @cli.command('annotate', short_help='Parse info about recorded units')
    @click.argument('action-id', type=click.STRING)
    @click.option('--tag', '-t',
                  multiple=True,
                  type=click.Choice(PAR.POSSIBLE_TAGS),
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
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        user = user or PAR.USER_PARAMS['user_name']
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

    @cli.command('adjust', short_help='Parse info about drive depth adjustment')
    @click.argument('subject-id',  type=click.STRING)
    @click.option('-d', '--date',
                  required=True,
                  type=click.STRING,
                  help='The date of the surgery format: "dd.mm.yyyyTHH:MM" or "now".',
                  )
    @click.option('-a', '--anatomy',
                  nargs=2,
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
        DTIME_FORMAT = expipe.io.core.datetime_format
        if date == 'now':
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
        datestring = datetime.strftime(date, DTIME_FORMAT)
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        if init:
            action = project.require_action(subject_id + '-adjustment')
        else:
            action = project.get_action(subject_id + '-adjustment')
        action.type = 'Adjustment'
        action.subjects = [subject_id]
        user = user or PAR.USER_PARAMS['user_name']
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
                if name.endswith('adjustment'):
                    deltas.append(int(name.split('_')[0]))
            index = max(deltas) + 1
        if init:
            index = 0
            surgery = project.get_action(subject_id + '-surgery-implantation')
            sdict = surgery.modules.to_dict()
            prev_depth = {key: sdict[PAR.MODULES['implantation'][key]]['position'][2]
                          for key, _ in anatomy}
            for key, depth in prev_depth.items():
                if not isinstance(depth, pq.Quantity):
                    raise ValueError('Depth of implant ' +
                                     '"{} = {}" not recognized'.format(key, depth))
                prev_depth[key] = depth.astype(float)
        else:
            prev_name = '{:03d}_adjustment'.format(index - 1)
            prev_dict = action.require_module(name=prev_name).to_dict()
            prev_depth = {key: prev_dict['depth'][key] for key, _ in anatomy}
        name = '{:03d}_adjustment'.format(index)
        module = action.require_module(template=PAR.TEMPLATES['adjustment'],
                                       name=name, overwrite=overwrite)

        curr_depth = {key: round(prev_depth[key] + val * pq.um, 3)
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
        content['git_note'] = get_git_info()
        action.require_module(name=name, contents=content, overwrite=True)

    @cli.command('register-surgery', short_help='Generate a surgery action.')
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
    @click.option('-w', '--weight',
                  required=True,
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  help='The weight of the subject with unit i.e. <200 g> (ommit <>).',
                  )
    @click.option('-p', '--position',
                  required=True,
                  multiple=True,
                  callback=validate_position,
                  help='The position e.g. <mecl,x,y,z,mm> (ommit <>).',
                  )
    @click.option('-a', '--angle',
                  type=click.FLOAT,
                  help='The angle of implantation/injection.',
                  )
    def generate_surgery(subject_id, procedure, date, user, weight,
                         overwrite, position, angle):
        # TODO tag sucject as active
        if procedure not in ["implantation", "injection"]:
            raise ValueError('procedure must be one of "implantation" ' +
                             'or "injection"')
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(subject_id + '-surgery-' + procedure)
        if date == 'now':
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
        action.datetime = date
        action.location = 'Sterile surgery station'
        action.type = 'Surgery'
        action.tags = [procedure]
        action.subjects = [subject_id]
        user = user or PAR.USER_PARAMS['user_name']
        if user is None:
            raise ValueError('Please add user name')
        if len(user) == 0:
            raise ValueError('Please add user name')
        print('Registering user ' + user)
        action.users = [user]
        generate_templates(action, PAR.TEMPLATES['surgery_' + procedure],
                           overwrite, git_note=get_git_info())
        modules_dict = action.modules.to_dict()
        for key, x, y, z, unit in position:
            name = PAR.MODULES[procedure][key]
            mod = action.require_module(template=name, overwrite=overwrite).to_dict()
            assert 'position' in mod
            assert isinstance(mod['position'], pq.Quantity)
            print('Registering position ' +
                  '{}: x={}, y={}, z={} {}'.format(key, x, y, z, unit))
            mod['position'] = pq.Quantity([x, y, z], unit)
            if angle is not None:
                raise NotImplementedError
            # mod['angle'] = pq.Quantity(angle[0], angle[1]) # TODO
            action.require_module(name=name, contents=mod, overwrite=True)

        subject = {'_inherits': '/action_modules/' +
                                'subjects-registry/' +
                                subject_id}
        subject['weight'] = pq.Quantity(weight[0], weight[1])
        action.require_module(name=PAR.MODULES['subject'], contents=subject,
                              overwrite=True)
        subjects_project = expipe.require_project('subjects-registry')
        subject_action = subjects_project.require_action(subject_id)
        subject_action.tags.append('surgery')

    @cli.command('register-subject', short_help='Register a subject to the "subjects-registry" project.')
    @click.argument('subject-id')
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the registration.',
                  )
    @click.option('--birthday',
                  required=True,
                  type=click.STRING,
                  help='The birthday of the subject, format: "dd.mm.yyyy".',
                  )
    @click.option('--cell_line',
                  required=True,
                  type=click.Choice(PAR.POSSIBLE_CELL_LINES),
                  help='Cell line of the subject.',
                  )
    @click.option('--developmental_stage',
                  type=click.STRING,
                  help="The developemtal stage of the subject. E.g. 'embroyonal', 'adult', 'larval' etc.",
                  )
    @click.option('--gender',
                  type=click.STRING,
                  help='Male or female?',
                  )
    @click.option('--genus',
                  type=click.STRING,
                  help='The Genus of the studied subject. E.g "rattus"',
                  )
    @click.option('--health_status',
                  type=click.STRING,
                  help='Information about the health status of this subject.',
                  )
    @click.option('--label',
                  type=click.STRING,
                  help='If the subject has been labled in a specific way. The lable can be described here.',
                  )
    @click.option('--population',
                  type=click.STRING,
                  help='The population this subject is offspring of. This may be the bee hive, the ant colony, etc.',
                  )
    @click.option('--species',
                  type=click.STRING,
                  help='The scientific name of the species e.g. Apis mellifera, Homo sapiens.',
                  )
    @click.option('--strain',
                  type=click.STRING,
                  help='The strain the subject was taken from. E.g. a specific genetic variation etc.',
                  )
    @click.option('--trivial_name',
                  type=click.STRING,
                  help='The trivial name of the species like Honeybee, Human.',
                  )
    @click.option('--weight',
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  help='The weight of the animal.',
                  )
    def generate_subject(subject_id, overwrite, user, **kwargs):
        project = expipe.require_project('subjects-registry')
        action = project.require_action(subject_id)
        kwargs['birthday'] = datetime.strftime(
            datetime.strptime(kwargs['birthday'], '%d.%m.%Y'), DTIME_FORMAT)
        action.datetime = datetime.now()
        action.type = 'Info'
        action.subjects = [subject_id]

        subject = action.require_module(template=PAR.MODULES['subject'],
                                        overwrite=overwrite).to_dict()
        for key, val in kwargs.items():
            if isinstance(val, (str, float, int)):
                subject[key]['value'] = val
            elif isinstance(val, tuple):
                subject[key] = pq.Quantity(val[0], val[1])
            elif isinstance(val, type(None)):
                pass
            else:
                raise TypeError('Not recognized type ' + str(type(val)))
        for key, val in subject.items():
            if isinstance(val, dict):
                if len(val.get('value')) == 0:
                    warnings.warn('No value registered for ' + key)
        action.require_module(name=PAR.MODULES['subject'], contents=subject,
                              overwrite=True)

    @cli.command('register-perfusion',
                 short_help=('Generate a perfusion action. ' +
                             'Also tags the subject as perfused.'))
    @click.argument('subject-id')
    @click.option('--date', '-d',
                  required=True,
                  type=click.STRING,
                  help='The date of the surgery format: "dd.mm.yyyyTHH:MM".',
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
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  default=(None, None),
                  help='The weight of the animal.',
                  )
    def generate_perfusion(subject_id, date, user, overwrite, weight):
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(subject_id + '-perfusion')
        if date == 'now':
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
        action.datetime = date
        action.location = 'Sterile surgery station'
        action.type = 'Surgery'
        action.tags = ['perfusion']
        action.subjects = [subject_id]
        user = user or PAR.USER_PARAMS['user_name']
        if user is None:
            raise ValueError('Please add user name')
        if len(user) == 0:
            raise ValueError('Please add user name')
        print('Registering user ' + user)
        action.users = [user]
        generate_templates(action, PAR.TEMPLATES['perfusion'],
                           overwrite, git_note=get_git_info())
        subject = {'_inherits': '/action_modules/' +
                                'subjects-registry/' +
                                subject_id}
        if weight != (None, None):
            subject['weight'] = pq.Quantity(weight[0], weight[1])
        action.require_module(name=PAR.MODULES['subject'], contents=subject,
                              overwrite=True)
        subjects_project = expipe.require_project('subjects-registry')
        subject_action = subjects_project.require_action(subject_id)
        subject_action.tags.append('surgery')
