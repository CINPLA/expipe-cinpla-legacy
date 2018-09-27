import expipe_plugin_cinpla
from expipecli.utils.plugin import IPlugin
from expipe_plugin_cinpla.imports import *
from . import adjust
from . import axona as AX
from . import environment
from . import misc
from . import openephys as OE
from . import subject
from . import surgery
from . import transfer


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

        @cli.group(short_help='Tools related to Open Ephys.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def openephys(ctx):
            pass

        @cli.group(short_help='Tools related to Axona.')
        @click.help_option('-h', '--help')
        @click.pass_context
        def axona(ctx):
            pass

        misc.attach_to_cli(cli)
        adjust.attach_to_cli(cli)
        surgery.attach_to_cli(cli)
        subject.attach_to_cli(cli)
        transfer.attach_to_cli(cli)
        environment.attach_to_cli(env)
        OE.attach_to_cli(openephys)
        AX.attach_to_cli(axona)
