from .imports import *
from ._version import get_versions
from .action_tools import query_yes_no
from .config import settings_file_path

default_settings = {
    'current': {
        'params': None,
        'project_id': None
    }
}


def attach_to_cli(cli):
    @cli.command('activate')
    @click.argument('project-id', type=click.STRING)
    def activate(project_id):
        assert os.path.exists(settings_file_path)
        with open(settings_file_path, "r") as f:
            current_settings = yaml.load(f)
        current_settings['current'] = current_settings[project_id]
        current_settings['current'].update({'project_id': project_id})
        with open(settings_file_path, "w") as f:
            yaml.dump(current_settings, f, default_flow_style=False)

    @cli.command('status')
    def generate_notebook():
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                current_settings = yaml.load(f)
        else:
            raise FileExistsError('No settings file found, use "expipe env ' +
                                  'set project-id --params".')
        print('Current environment:\n')
        print('\n'.join(['{}: \n\t {}'.format(key, val)
                         for key, val in current_settings['current'].items()]))
        print('\nAvailable environment(s):')
        for pid, value in [(p, v) for p, v in current_settings.items() if p != 'current']:
            print('\nproject_id:\n\t', pid)
            print('\n'.join(['{}: \n\t {}'.format(key, val)
                             for key, val in value.items()]))

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
                  help='Set the expipe cinpla parameter file.',
                  )
    def set(project_id, activate, **kwargs):
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                current_settings = yaml.load(f)
        else:
            current_settings = default_settings
            activate = True
        for key, val in kwargs.items():
            if project_id in current_settings:
                current_settings[project_id].update({key: val})
            else:
                current_settings.update({project_id: {key: val}})
        if activate:
            current_settings['current'] = current_settings[project_id]
            current_settings['current'].update({'project_id': project_id})
        with open(settings_file_path, "w") as f:
            yaml.dump(current_settings, f, default_flow_style=False)

    @cli.command('remove')
    @click.argument('project-id', type=click.STRING)
    def remove(project_id):
        if os.path.exists(settings_file_path):
            with open(settings_file_path, "r") as f:
                current_settings = yaml.load(f)
        else:
            raise FileExistsError('No settings file found.')
        if project_id in current_settings:
            delete = query_yes_no('Are you sure you want to completely remove' +
                                  ' ' + current_settings[project_id])
            if delete:
                del(current_settings[project_id])
            if project_id == current_settings['current']['project_id']:
                warnings.warn('The environment you are removing is the ' +
                              'current active environment. You need to ' +
                              'activate another environment to change ' +
                              'current active environment.')

        else:
            raise ValueError('Project id "' + project_id + '" not found in settings file.')
        with open(settings_file_path, "w") as f:
            yaml.dump(current_settings, f, default_flow_style=False)
