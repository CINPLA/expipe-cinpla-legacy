import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq
import os.path as op
from expipe_plugin_cinpla.main import CinplaPlugin
import sys
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import (USER_PARAMS, TEMPLATES, UNIT_INFO, POSSIBLE_TAGS,
                               POSSIBLE_LOCATIONS, OBLIGATORY_TAGS, MODULES,
                               ANALYSIS_PARAMS)


@click.group()
@click.pass_context
def cli(ctx):
    pass


CinplaPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    result = CliRunner().invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception
    return result

if __name__ == '__main__':
    project = expipe.get_project(USER_PARAMS['project_id'])
    for action_id in project.actions.keys():
        run_command(['analyse', action_id, '-a', 'all'])
