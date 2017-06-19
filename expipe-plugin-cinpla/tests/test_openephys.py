import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq

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
