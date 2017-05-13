# -*- coding: utf-8 -*-

"""Launch routines."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from operator import itemgetter
import os.path as op
import shutil
import sys

import click
import numpy as np
from phy.utils import IPlugin
from .model import NeoModel
from phy.utils.cli import _run_cmd, _add_log_file

logger = logging.getLogger(__name__)


def neo_klusta(*args, **kwargs):
    assert not args
    model = NeoModel(**kwargs)
    if kwargs['channel_group'] is None:
        channel_groups = model.channel_groups
    else:
        channel_groups = [model.channel_group]
    for channel_group in channel_groups:
        if not channel_group == model.channel_group:
            model.load_data(channel_group)
        clusters = model.cluster(np.arange(model.n_spikes), model.channel_ids)
        model.save(spike_clusters=clusters)


class NeoKlusta(IPlugin):
    """Create the `phy neo-klusta` command for NEO files."""

    def attach_to_cli(self, cli):

        # Create the `phy cluster-manual file.neo` command.
        @cli.command('neo-klusta')  # pragma: no cover
        @click.argument('data-path', type=click.Path(exists=True))
        @click.option('--output-dir',
                      type=click.Path(file_okay=False, dir_okay=True),
                      help='Output directory.',
                      )
        @click.option('--output-ext',
                      type=click.STRING,
                      default='.exdir',
                      help='Output extension.',
                      )
        @click.option('--output-name',
                      type=click.STRING,
                      help='Output basename of file.',
                      )
        @click.option('--channel-group',
                      type=click.INT,
                      help='Channel group to cluster (all by default).',
                      )
        @click.option('--segment-num',
                      type=click.INT,
                      help='Segment to cluster (all by default).',
                      )
        @click.option('--detect-only',
                      help='Only do spike detection.',
                      default=False,
                      is_flag=True,
                      )
        @click.option('--cluster-only',
                      help='Only do automatic clustering.',
                      default=False,
                      is_flag=True,
                      )
        @click.option('--mode',
                      help='Mode to neo writer io.',
                      type=click.STRING,
                      default='',
                      )
        @click.help_option()
        def main(*args, **kwargs):
            """Spikesort a dataset.

            By default, perform spike detection (with SpikeDetekt) and automatic
            clustering (with KlustaKwik2). You can also choose to run only one step.

            You need to specify three pieces of information to spikesort your data:

            * The raw data file: typically a `.dat` file.

            * The PRM file: a Python file with the `.prm` extension, containing the parameters for your sorting session.

            * The PRB file: a Python file with the `.prb` extension, containing the layout of your probe.

            """  # noqa

            return neo_klusta(*args, **kwargs)
