import expipe
import os
import os.path as op
import click
import yaml
import warnings
from .pytools import load_parameters

settings_file = op.join(expipe.config.config_dir, 'cinpla_config.yaml')
if not op.exists(settings_file):
    warnings.warn('No config file found, import errors will occur, please use' +
                  ' "expipe env create project-id -p path-to-params-file"')

DTIME_FORMAT = expipe.io.core.datetime_format

PAR = load_parameters()

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
        assert op.exists(settings_file)
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
        """
        Provide action id to find exdir path

        COMMAND: action-id: Provide action id to find exdir path
        """
        from pprint import pprint
        project = expipe.get_project(PAR.USER_PARAMS['project_id'])
        path = op.join(expipe.settings['data_path'],
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
        assert op.exists(settings_file)
        with open(settings_file, "r") as f:
            current_settings = yaml.load(f)
        from pprint import pprint
        pprint(current_settings['current'])
