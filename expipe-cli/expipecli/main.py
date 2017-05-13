# -*- coding: utf-8 -*-
# flake8: noqa

"""CLI tool."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
import os
import os.path as op
import sys
from traceback import format_exception

import click
from six import exec_
import glob

from .utils import discover_plugins, IPlugin


# ------------------------------------------------------------------------------
# CLI tool
# ------------------------------------------------------------------------------

@click.group()
# @click.version_option(version=__version_git__)
@click.help_option('-h', '--help')
@click.pass_context
def expipe(ctx, pdb=None):
    """Add subcommands to 'expipe' with plugins
    using `attach_to_cli()` and the `click` library.

    Note that you can get help from a COMMAND by "expipe COMMAND --help"
    """
    pass


class Default(IPlugin):
    def attach_to_cli(self, cli):
        @cli.command('configure')
        @click.option('--data-path',
                      type=click.STRING,
                      help='Path to where data files should be stored',
                      )
        @click.option('--email',
                      type=click.STRING,
                      help='User email on Firebase server',
                      )
        @click.option('--password',
                      type=click.STRING,
                      help='User password on Firebase server (WARNING: Will be stored in plain text!)',
                      )
        @click.option('--url_prefix',
                      type=click.STRING,
                      help='Prefix of Firebase server URL (https://<url_prefix>.firebaseio.com)',
                      )
        @click.option('--api_key',
                      type=click.STRING,
                      help='Firebase API key',
                      )
        def configure(data_path, email, password, url_prefix, api_key):
            """Create a configuration file."""
            import expipe
            expie.configure(data_path, email, password, url_prefix, api_key)


# ------------------------------------------------------------------------------
# CLI plugins
# ------------------------------------------------------------------------------


def load_cli_plugins(cli, config_dir=None):
    """Load all plugins and attach them to a CLI object."""
    
    plugins = discover_plugins()
    for plugin in plugins:
        if not hasattr(plugin, 'attach_to_cli'):  # pragma: no cover
            continue
        # NOTE: plugin is a class, so we need to instantiate it.
        try:
            plugin().attach_to_cli(cli)
        except Exception as e:  # pragma: no cover
            print("Error when loading plugin `%s`" % plugin)
            raise e


# Load all plugins when importing this module.
load_cli_plugins(expipe)
