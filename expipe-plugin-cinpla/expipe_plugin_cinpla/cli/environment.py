from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.tools.action import query_yes_no
from expipe_plugin_cinpla._version import get_versions
from expipe_plugin_cinpla.tools.config import settings_file_path


def if_active_update_current(settings, project_id):
    current = settings.get('current') or {}
    if current.get('project_id') == project_id:
        current = settings[project_id]
        current.update({'project_id': project_id})
        # if current was None
        settings['current'] = current
    else:
        print('Activate project with "expipe env activate ' +
              '{}"'.format(project_id))


def check_project_exists(settings, project_id):
    if project_id not in settings:
        raise IOError(
            'Project "{}" '.format(project_id) +
            'does not exists, use "expipe env create {}"'.format(project_id))


def load_settings():
    if os.path.exists(settings_file_path):
        with open(settings_file_path, "r") as f:
            settings = yaml.load(f)
    else:
        settings = None
    return settings


def set_firebase_settings(path):
    expipe.config.rc_params['settings_file_path'] = path
    with open(expipe.config.rc_file_path, "w") as f:
        yaml.dump(expipe.config.rc_params, f, default_flow_style=False)


def attach_to_cli(cli):
    @cli.command('activate')
    @click.argument('project-id', type=click.STRING)
    def activate(project_id):
        settings = load_settings()
        assert settings is not None, 'Cannot find settings file.'
        settings['current'] = settings[project_id]
        settings['current'].update({'project_id': project_id})
        set_firebase_settings(settings[project_id]['config'])
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('status')
    @click.option('--verbose', '-v',
                  is_flag=True,
                  help='Show all information about every environment.',
                  )
    def status(**kw):
        settings = load_settings()
        assert settings is not None, 'Cannot find settings file.'
        print('Current environment:\n')
        print('\n'.join(['{}: \n\t {}'.format(key, val)
                         for key, val in settings['current'].items()]))
        print('\nAvailable environment(s):')
        for pid, value in [(p, v) for p, v in settings.items() if p != 'current']:
            print('\nproject_id: ', pid)
            if kw['verbose']:
                print('\n'.join(['{}: \n\t {}\n'.format(key, val)
                                 for key, val in value.items()]))

    @cli.command('create')
    @click.argument('project-id', type=click.STRING)
    @click.argument('config',
                  type=click.Path(exists=True, resolve_path=True),
                  )
    @click.option('--probe',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set a probe file.',
                  )
    @click.option('--params',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set a probe file.',
                  )
    def create(project_id, **kwargs):
        settings = load_settings() or {}
        update = {k: v for k, v in kwargs.items() if v is not None}
        settings.update({project_id: update})
        if_active_update_current(settings, project_id)
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('set')
    @click.argument('project-id', type=click.STRING)
    @click.option('--config',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set the expipe config file.',
                  )
    @click.option('--probe',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set a probe file.',
                  )
    @click.option('--params',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set a probe file.',
                  )
    def set(project_id, **kwargs):
        settings = load_settings() or {}
        check_project_exists(settings, project_id)
        update = {k: v for k, v in kwargs.items() if v is not None}
        settings.update({project_id: update})
        if_active_update_current(settings, project_id)
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('remove')
    @click.argument('project-id', type=click.STRING)
    def remove(project_id):
        settings = load_settings()
        assert settings is not None, 'Cannot find settings file.'
        if project_id in settings:
            delete = query_yes_no('Are you sure you want to completely remove' +
                                  ' ' + project_id)
            if delete:
                del(settings[project_id])
            if project_id == settings['current']['project_id']:
                warnings.warn('The environment you are removing is the ' +
                              'current active environment. You need to ' +
                              'activate another environment to change ' +
                              'current active environment.')

        else:
            raise ValueError('Project id "' + project_id +
                             '" not found in settings file.')
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('sync-project-settings')
    @click.argument('project-id', type=click.STRING)
    def create(project_id):
        project_params_file_path = os.path.join(
            os.path.expanduser('~'), '.config', 'expipe',
            '{}-project-params.yaml'.format(project_id))
        project = expipe.get_project(project_id)
        settings = project.modules['settings'].to_dict()
        with open(project_params_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)
