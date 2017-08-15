from .imports import *
from ._version import get_versions
from .pytools import load_parameters


settings_file = os.path.join(os.path.expanduser('~'), '.config', 'expipe',
                             'cinpla_config.yaml')
if not os.path.exists(settings_file):
    warnings.warn('No config file found, import errors will occur, please use' +
                  ' "expipe env create project-id -p path-to-params-file"')

default_settings = {
    'current': {
        'parameters_path': None,
        'project_id': None
    }
}


def attach_to_cli(cli):
    @cli.command('activate')
    @click.argument('project-id', type=click.STRING)
    def activate(project_id):
        assert os.path.exists(settings_file)
        with open(settings_file, "r") as f:
            current_settings = yaml.load(f)
        params_path = current_settings[project_id]['parameters_path']
        current_settings.update({
            'current': {
                'parameters_path': params_path,
                'project_id': project_id}})
        with open(settings_file, "w") as f:
            yaml.dump(current_settings, f, default_flow_style=False)

    @cli.command('list')
    @click.argument('what', type=click.Choice(['dir', 'actions']))
    def generate_notebook(what):
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        path = os.path.join(expipe.settings['data_path'],
                       PAR.USER_PARAMS['project_id'])
        if what == 'dir':
            pprint(os.listdir(path))
        elif what == 'actions':
            pprint(project.actions.keys())

    @cli.command('create')
    @click.argument('project-id', type=click.STRING)
    @click.argument('params-path', type=click.Path(exists=True))
    @click.option('-a', '--activate',
                  is_flag=True,
                  help='Activate the project.',
                  )
    def create(project_id, params_path, activate):
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                current_settings = yaml.load(f)
        else:
            current_settings = default_settings
            activate = True
        current_settings.update({
            project_id: {'parameters_path': params_path}
        })
        if activate:
            current_settings.update({
                'current': {'parameters_path': params_path,
                            'project_id': project_id},
            })
        with open(settings_file, "w") as f:
            yaml.dump(current_settings, f, default_flow_style=False)

    @cli.command('which')
    def which():
        assert os.path.exists(settings_file)
        with open(settings_file, "r") as f:
            current_settings = yaml.load(f)
        from pprint import pprint
        pprint(current_settings['current'])