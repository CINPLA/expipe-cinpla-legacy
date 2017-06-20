import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq
import os.path as op

expipe.ensure_testing()


@click.group()
@click.pass_context
def cli(ctx):
    pass


from expipe_plugin_cinpla.openephys import OpenEphysPlugin
OpenEphysPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    runner = CliRunner()
    result = runner.invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception


def test_openephys(module_teardown_setup_project_setup):
    currdir = op.abspath(op.dirname(__file__))
    openephys_path = op.join(currdir, 'test_data', 'openephys',
                             'test-rat_2017-06-20_11-43-34_01')
    action_id = 'test-rat-200617-01'
    run_command(['register-openephys', openephys_path, '--no-move'], inp='y')
    # run_command(['process-openephys', action_id])
