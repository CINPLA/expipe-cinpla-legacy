from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.tools.action import generate_templates, get_git_info, query_yes_no
from expipe_plugin_cinpla.tools import config


def attach_to_cli(cli):
    @cli.command('surgery', short_help='Generate a surgery action.')
    @click.argument('entity-id')
    @click.option('--date', '-d',
                  required=True,
                  type=click.STRING,
                  help='The date of the surgery format: "dd.mm.yyyyTHH:MM".',
                  )
    @click.option('-t', '--tag',
                  multiple=True,
                  type=click.STRING,
                  callback=config.optional_choice,
                  envvar=PAR.POSSIBLE_TAGS,
                  help='Add tags to action.',
                  )
    @click.option('--procedure',
                  required=True,
                  type=click.Choice(['implantation', 'injection']),
                  help='The type of surgery "implantation" or "injection".',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    @click.option('--hard',
                  is_flag=True,
                  help='Overwrite by deleting action.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the surgery.',
                  )
    @click.option('-w', '--weight',
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  default=(None, None),
                  help='The weight of the entity with unit i.e. <200 g> (ommit <>).',
                  )
    @click.option('-p', '--position',
                  required=True,
                  multiple=True,
                  callback=config.validate_position,
                  help='The position e.g. <"mecl 0 x y z mm"> (ommit <>).',
                  )
    @click.option('-a', '--angle',
                  required=True,
                  multiple=True,
                  callback=config.validate_angle,
                  help='The angle of implantation/injection.',
                  )
    @click.option('--message', '-m',
                  multiple=True,
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    def generate_surgery(entity_id, procedure, date, user, weight, hard,
                         overwrite, position, angle, message, tag):
        # TODO tag sucject as active
        assert weight != (None, None), 'Missing argument -w / --weight.'
        weight = pq.Quantity(weight[0], weight[1])
        project = expipe.require_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(entity_id + '-surgery-' + procedure)
        if overwrite and hard:
            project.delete_action(entity_id + '-surgery-' + procedure)
        try:
            entity = project.get_entity(entity_id)
        except KeyError as e:
            raise KeyError(
                str(e) +
                '. Register entity with "expipe register-entity entity_id"')
        entity_module = entity.get_module(name=PAR.MODULES['entity'])
        entity.tags.extend(['surgery', PAR.USER_PARAMS['project_id']])
        entity.users.append(user)

        entity_module['weight'] = weight
        action.require_module(
            name=PAR.MODULES['entity'], contents=entity_module.to_dict())

        generate_templates(action, 'surgery_' + procedure,
                           git_note=get_git_info())
        if date == 'now':
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
        action.datetime = date
        action.location = 'Sterile surgery station'
        action.type = 'Surgery'
        action.tags = [procedure] + list(tag)
        action.entities = [entity_id]
        user = user or PAR.USER_PARAMS['user_name']
        user = user or []
        if len(user) == 0:
            raise ValueError('Please add user name')
        print('Registering user ' + user)
        action.users = [user]
        if overwrite:
            action.messages = []
        for m in message:
            action.create_message(text=m, user=user, datetime=datetime.now())
        modules_dict = action.modules.to_dict()
        keys = list(set([pos[0] for pos in position]))
        modules = {
            key: action.require_module(template=PAR.MODULES[procedure][key]).to_dict()
            for key in keys}
        for key, num, x, y, z, unit in position:
            mod = modules[key]
            if 'position' in mod:
                del(mod['position']) # delete position template
            print('Registering position ' +
                  '{} {}: x={}, y={}, z={} {}'.format(key, num, x, y, z, unit))
            mod['position_{}'.format(num)] = pq.Quantity([x, y, z], unit)
        for key, ang, unit in angle:
            mod = modules[key]
            if 'angle' in mod:
                del(mod['angle']) # delete position template
            print('Registering angle ' +
                  '{}: angle={} {}'.format(key, ang, unit))
            mod['angle'] = pq.Quantity(ang, unit)
        for key in keys:
            action.require_module(name=PAR.MODULES[procedure][key],
                                  contents=modules[key])

    @cli.command('euthanasia',
                 short_help=('Register a entities euthanasia.'))
    @click.argument('entity-id')
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the registration.',
                  )
    @click.option('--message', '-m',
                  multiple=True,
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    def generate_euthanasia(entity_id, user, message):
        entity = project.require_entity(entity_id)
        entity.tags.append('euthanised')
        user = user or PAR.USER_PARAMS['user_name']
        user = user or []
        if len(user) == 0:
            raise ValueError('Please add user name')
        print('Registering user ' + user)
        entity.users.append(user)
        entity.messages.extend([{'message': m,
                                 'user': user,
                                 'datetime': datetime.now()}
                               for m in message])

    @cli.command('perfusion',
                 short_help=('Generate a perfusion action. ' +
                             'Also tags the entity as perfused and euthanised.'))
    @click.argument('entity-id')
    @click.option('--date', '-d',
                  required=True,
                  type=click.STRING,
                  help='The date of the surgery format: "dd.mm.yyyyTHH:MM".',
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
    def generate_perfusion(entity_id, date, user, weight):
        project = expipe.require_project(PAR.USER_PARAMS['project_id'])
        action = project.require_action(entity_id + '-perfusion')
        generate_templates(action, 'perfusion',
                           git_note=get_git_info())
        if date == 'now':
            date = datetime.now()
        else:
            date = datetime.strptime(date, '%d.%m.%YT%H:%M')
        action.datetime = date
        action.location = 'Sterile surgery station'
        action.type = 'Surgery'
        action.tags = ['perfusion']
        action.entities = [entity_id]
        user = user or PAR.USER_PARAMS['user_name']
        user = user or []
        if len(user) == 0:
            raise ValueError('Please add user name')
        print('Registering user ' + user)
        action.users = [user]
        if weight != (None, None):
            entity_dict = action.require_module(name=PAR.MODULES['entity']).to_dict()
            entity_dict['weight'] = pq.Quantity(weight[0], weight[1])
            action.require_module(name=PAR.MODULES['entity'], contents=entity_dict)
        entity = project.require_entity(entity_id)
        entity.tags.extend(['perfused', 'euthanised'])
