from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.tools.action import query_yes_no
from expipe_plugin_cinpla._version import get_versions
from expipe_plugin_cinpla.tools.config import settings_file_path

default_settings = {
    'current': {
        'params': None,
        'project_id': None,
        'probe': None
    }
}


def attach_to_cli(cli):
    @cli.command('activate')
    @click.argument('project-id', type=click.STRING)
    def activate(project_id):
        assert os.path.exists(settings_file_path)
        with open(settings_file_path, "r") as f:
            settings = yaml.load(f)
        settings['current'] = settings[project_id]
        settings['current'].update({'project_id': project_id})
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('status')
    @click.option('--verbose', '-v',
                  is_flag=True,
                  help='Show all information about every environment.',
                  )
    def status(**kw):
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                settings = yaml.load(f)
        else:
            raise FileExistsError('No settings file found, use "expipe env ' +
                                  'set project-id --params".')
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
    @click.option('-a', '--activate',
                  is_flag=True,
                  help='Activate the project.',
                  )
    @click.option('--params',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set the expipe cinpla parameter file.',
                  )
    @click.option('--probe',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set a probe file.',
                  )
    def create(project_id, activate, **kwargs):
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                settings = yaml.load(f)
        else:
            settings = default_settings
            activate = True
        if project_id in settings:
            raise IOError(
                'Project "{}" exists, use "expipe env set"'.format(project_id))
        for key, val in kwargs.items():
            settings.update({project_id: {key: val}})
        if activate:
            settings['current'] = settings[project_id]
            settings['current'].update({'project_id': project_id})
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('set')
    @click.argument('project-id', type=click.STRING)
    @click.option('-a', '--activate',
                  is_flag=True,
                  help='Activate the project.',
                  )
    @click.option('--params',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set the expipe cinpla parameter file.',
                  )
    @click.option('--probe',
                  type=click.Path(exists=True, resolve_path=True),
                  help='Set a probe file.',
                  )
    def set(project_id, activate, **kwargs):
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                settings = yaml.load(f)
        else:
            settings = default_settings
            activate = True
        if project_id not in settings:
            raise IOError(
                'Project "{}" '.format(project_id) +
                'does not exists, use "expipe env create"')
        for key, val in kwargs.items():
            if project_id in settings:
                settings[project_id].update({key: val})
            else:
                settings.update({project_id: {key: val}})
        if settings['current']['project_id'] == project_id:
            activate = True
        if activate:
            settings['current'] = settings[project_id]
            settings['current'].update({'project_id': project_id})
        with open(settings_file_path, "w") as f:
            yaml.dump(settings, f, default_flow_style=False)

    @cli.command('remove')
    @click.argument('project-id', type=click.STRING)
    def remove(project_id):
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                settings = yaml.load(f)
        else:
            raise FileExistsError('No settings file found.')
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
