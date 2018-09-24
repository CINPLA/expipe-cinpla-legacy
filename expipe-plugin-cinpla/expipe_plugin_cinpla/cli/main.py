import expipe_plugin_cinpla
from expipecli.utils.plugin import IPlugin
from expipe_plugin_cinpla.imports import *
from . import cli_misc
from . import cli_analysis
from . import cli_environment
from . import cli_transfer
from . import cli_openephys
from . import cli_axona
from . import cli_optogenetics
from . import cli_intan
from . import cli_intan_ephys
from . import cli_visual_stimulus
from . import cli_electrical_stimulation


def reveal():
    """
    This imports all plugins when loading expipe-cli.
    """
    pass


class CinplaPlugin(IPlugin):
    def attach_to_cli(self, cli):
        @cli.group(short_help='Tools to select environment parameters pluss more helpful environment tools.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def env(ctx):
            pass

        @cli.group(short_help='Tools related to optogenetics.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def opto(ctx):
            pass

        @cli.group(short_help='Tools related to Open Ephys.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def openephys(ctx):
            pass

        @cli.group(short_help='Tools related to Intan.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def intan(ctx):
            pass

        @cli.group(short_help='Tools related to Axona.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def axona(ctx):
            pass

        @cli.group(short_help='Tools related to the combination of Open Ephys and Intan.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def intan_ephys(ctx):
            pass

        @cli.group(short_help='Tools related to visual stimulation.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def visual(ctx):
            pass

        cli_misc.attach_to_cli(cli)
        cli_analysis.attach_to_cli(cli)
        cli_environment.attach_to_cli(env)
        cli_transfer.attach_to_cli(cli)
        cli_openephys.attach_to_cli(openephys)
        cli_axona.attach_to_cli(axona)
        cli_optogenetics.attach_to_cli(opto)
        cli_intan.attach_to_cli(intan)
        cli_intan_ephys.attach_to_cli(intan_ephys)
        cli_visual_stimulus.attach_to_cli(visual)
        cli_electrical_stimulation.attach_to_cli(cli)
