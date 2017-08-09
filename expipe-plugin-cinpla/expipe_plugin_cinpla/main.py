import click
from expipecli.utils import IPlugin
from . import project_manager
from . import misc
from . import transfer
from . import openephys as _openephys
from . import optogenetics
from . import intan as _intan
from . import axona as _axona
from . import intan_ephys as _intan_ephys
from . import electrical_stimulation
from . import visual_stimulus


class CinplaPlugin(IPlugin):
    def attach_to_cli(self, cli):
        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def project(ctx):
            pass

        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def opto(ctx):
            pass

        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def openephys(ctx):
            pass

        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def intan(ctx):
            pass

        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def axona(ctx):
            pass

        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def intan_ephys(ctx):
            pass

        @cli.group()
        @click.help_option('-h', '--help')
        @click.pass_context
        def visual(ctx):
            pass

        visual_stimulus.attach_to_cli(visual)
        project_manager.attach_to_cli(project)
        misc.attach_to_cli(cli)
        transfer.attach_to_cli(cli)
        misc.attach_to_cli(cli)
        _openephys.attach_to_cli(openephys)
        optogenetics.attach_to_cli(opto)
        _intan.attach_to_cli(intan)
        _intan_ephys.attach_to_cli(intan_ephys)
        electrical_stimulation.attach_to_cli(cli)
