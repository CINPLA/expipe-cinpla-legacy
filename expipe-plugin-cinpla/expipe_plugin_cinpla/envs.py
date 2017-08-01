import expipe
import os
import os.path as op
from expipecli.utils import IPlugin
import click
import yaml

settings_file = op.join(expipe.config.config_dir, 'cinpla_config.yaml')
if not op.exists(settings_file):
    print('No config file found, please use ' +
          '"expipe create-env your-project-id --params-path path-to-params-file"')

DTIME_FORMAT = expipe.io.core.datetime_format

default_settings = {
    'current': {
        'parameters_path': None,
        'project_id': None
    }
}


class EnvironmentPlugin(IPlugin):
    """Create the `expipe command` for neuro recordings."""
    def attach_to_cli(self, cli):
        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def env(ctx):
            pass

        @env.command('activate')
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

        @env.command('create')
        @click.argument('project-id', type=click.STRING)
        @click.option('-p', '--params-path',
                      type=click.Path(exists=True),
                      help='Path to parameters file.',
                      )
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

        @env.command('which')
        def which():
            assert op.exists(settings_file)
            with open(settings_file, "r") as f:
                current_settings = yaml.load(f)
            from pprint import pprint
            pprint(current_settings['current'])
