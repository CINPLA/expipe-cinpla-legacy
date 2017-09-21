# -*- coding: utf-8 -*-

"""Neo GUI."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging
from operator import itemgetter
import os
import os.path as op
import shutil
import click
import numpy as np

from phy.cluster.supervisor import Supervisor
from phy.cluster.views import (WaveformView,
                               FeatureView,
                               CorrelogramView,
                               ScatterView,
                               select_traces,
                               )
from phy.cluster.views.trace import _iter_spike_waveforms
from phy.gui import create_app, run_app, GUI
from phy.io.array import (Selector,
                          )
from phy.io.context import Context, _cache_methods
from phy.stats import correlograms
from phy.utils import Bunch, IPlugin, EventEmitter
from phy.utils._color import ColorSelector
from phy.utils.cli import _run_cmd, _add_log_file

from .model import NeoModel
from ..utils import attach_plugins

logger = logging.getLogger(__name__)

try:
    import klusta
except ImportError:  # pragma: no cover
    logger.warn("Package klusta not installed: the NeoGUI will not work.")

#------------------------------------------------------------------------------
# Utils and views
#------------------------------------------------------------------------------

class NeoFeatureView(ScatterView):
    _callback_delay = 100

    def _get_data(self, cluster_ids):
        if len(cluster_ids) != 2:
            return []
        b = self.coords(cluster_ids)
        return [Bunch(x=b.x0, y=b.y0), Bunch(x=b.x1, y=b.y1)]


class AmplitudeView(ScatterView):
    def _plot_points(self, bunchs, data_bounds):
        super(AmplitudeView, self)._plot_points(bunchs, data_bounds)
        liney = 1.
        self.lines(pos=[[data_bounds[0], liney, data_bounds[2], liney]],
                   data_bounds=data_bounds,
                   color=(1., 1., 1., .5),
                   )


#------------------------------------------------------------------------------
# Neo Controller
#------------------------------------------------------------------------------

def _get_distance_max(pos):
    return np.sqrt(np.sum(pos.max(axis=0) - pos.min(axis=0)) ** 2)


class NeoController(EventEmitter):
    gui_name = 'NeoGUI'

    n_spikes_waveforms = 200
    batch_size_waveforms = 200

    n_spikes_features = 10000
    n_spikes_amplitudes = 10000
    n_spikes_correlograms = 100000

    def __init__(self, data_path, config_dir=None, **kwargs):
        super(NeoController, self).__init__()
        self.model = NeoModel(data_path, **kwargs)
        self.distance_max = _get_distance_max(self.model.channel_positions)
        self.cache_dir = op.join(self.model.output_dir, '.phy')
        cg = kwargs.get('channel_group', None)
        cg = cg or 0
        self.cache_dir = op.join(self.cache_dir, 'channel_group_' + str(cg))
        self.context = Context(self.cache_dir)
        self.config_dir = config_dir
        self._set_cache()
        self.supervisor = self._set_supervisor()
        self.selector = self._set_selector()
        self.color_selector = ColorSelector()

        self._show_all_spikes = False

        attach_plugins(self, plugins=kwargs.get('plugins', None),
                       config_dir=config_dir)

    # Internal methods
    # -------------------------------------------------------------------------

    def _set_cache(self):
        memcached = ('get_best_channels',
                     #'get_probe_depth',
                     '_get_mean_waveforms',
                     )
        cached = ('_get_waveforms',
                  '_get_features',
                  )
        _cache_methods(self, memcached, cached)

    def _set_supervisor(self):
        # Load the new cluster id.
        new_cluster_id = self.context.load('new_cluster_id'). \
            get('new_cluster_id', None)
        cluster_groups = self.model.cluster_groups
        supervisor = Supervisor(self.model.spike_clusters,
                                similarity=self.similarity,
                                cluster_groups=cluster_groups,
                                new_cluster_id=new_cluster_id,
                                context=self.context,
                                )

        @supervisor.connect
        def on_create_cluster_views():

            supervisor.add_column(self.get_best_channel, name='channel')
            supervisor.add_column(self.get_probe_depth, name='depth')

            @supervisor.actions.add
            def recluster():
                """Relaunch KlustaKwik on the selected clusters."""
                # Selected clusters.
                cluster_ids = supervisor.selected  # TODO can you have multiselect here?
                spike_ids = self.selector.select_spikes(cluster_ids)
                logger.info("Running KlustaKwik on %d spikes.", len(spike_ids))
                print('***********************')
                print('Fix this wierd fix, cant send in list (cluster_ids)')
                channel_ids = self.get_best_channels(cluster_ids[0])  # TODO sending several cluster_ids to get best channels ?
                spike_clusters = self.model.cluster(spike_ids, channel_ids)
                self.supervisor.split(spike_ids, spike_clusters)

        # Save.
        @supervisor.connect
        def on_request_save(spike_clusters, groups, *labels):
            """Save the modified data."""
            # Save the clusters.
            groups = {c: g.title() for c, g in groups.items()}
            self.model.save(spike_clusters, groups, *labels)

        return supervisor

    def _set_selector(self):
        def spikes_per_cluster(cluster_id):
            return self.supervisor.clustering.spikes_per_cluster[cluster_id]
        return Selector(spikes_per_cluster)

    def _add_view(self, gui, view):
        view.attach(gui)
        self.emit('add_view', gui, view)
        return view

    # Model methods
    # -------------------------------------------------------------------------

    def get_best_channel(self, cluster_id):
        channel_ids = self.get_best_channels(cluster_id)
        amps = self._get_mean_waveforms(cluster_id).data[0].min(axis=0)
        channel_id = channel_ids[np.argmin(amps)]
        return channel_id

    def get_best_channels(self, cluster_ids):  # TODO
        return np.arange(self.model.n_chans)

    def get_cluster_position(self, cluster_id):
        channel_id = self.get_best_channel(cluster_id)
        return self.model.channel_positions[channel_id]

    def get_probe_depth(self, cluster_id):
        channel_id = self.get_best_channel(cluster_id)
        return self.model.channel_positions[channel_id][1]

    def similarity(self, cluster_id):
        """Return the list of similar clusters to a given cluster."""

        pos_i = self.get_cluster_position(cluster_id)
        
        def _sim_ij(cj):
            """Distance between channel position of clusters i and j."""
            pos_j = self.get_cluster_position(cj)
            d = np.sqrt(np.sum((pos_j - pos_i) ** 2))
            return self.distance_max - d
        out = [(cj, _sim_ij(cj))
               for cj in self.supervisor.clustering.cluster_ids]
        return sorted(out, key=itemgetter(1), reverse=True)

    # Waveforms
    # -------------------------------------------------------------------------

    def _get_waveforms(self, cluster_id):
        """Return a selection of waveforms for a cluster."""
        pos = self.model.channel_positions
        spike_ids = self.selector.select_spikes([cluster_id],
                                                self.n_spikes_waveforms,
                                                self.batch_size_waveforms,
                                                )
        channel_ids = self.get_best_channels(cluster_id)
        data = self.model.get_waveforms(spike_ids, channel_ids)
        return Bunch(data=data,
                     channel_ids=channel_ids,
                     channel_positions=pos[channel_ids],
                     alpha=0.25
                     )

    def _get_mean_waveforms(self, cluster_id):
        b = self._get_waveforms(cluster_id)
        b.data = b.data.mean(axis=0)[np.newaxis, ...]
        b['alpha'] = 1.
        return b

    def add_waveform_view(self, gui):
        v = WaveformView(waveforms=self._get_waveforms,
                         )
        v = self._add_view(gui, v)

        v.actions.separator()

        @v.actions.add(shortcut='m')
        def toggle_mean_waveforms():
            f, g = self._get_waveforms, self._get_mean_waveforms
            v.waveforms = f if v.waveforms == g else g
            v.on_select()

        return v

    # Features
    # -------------------------------------------------------------------------

    def _get_spike_ids(self, cluster_id=None, load_all=None):
        nsf = self.n_spikes_features
        if cluster_id is None:
            # Background points.
            ns = self.model.n_spikes
            return np.arange(0, ns, max(1, ns // nsf))
        else:
            # Load all spikes from the cluster if load_all is True.
            n = nsf if not load_all else None
            return self.selector.select_spikes([cluster_id], n)

    def _get_spike_times(self, cluster_id=None, load_all=None):
        spike_ids = self._get_spike_ids(cluster_id)
        return Bunch(data=self.model.spike_times[spike_ids],
                     lim=(0., self.model.duration))

    def _get_features(self, cluster_id=None, channel_ids=None, load_all=None):
        spike_ids = self._get_spike_ids(cluster_id, load_all=load_all)
        # Use the best channels only if a cluster is specified and
        # channels are not specified.
        if cluster_id is not None and channel_ids is None:
            channel_ids = self.get_best_channels(cluster_id)
        f = self.model.features[spike_ids][:, channel_ids]
        m = self.model.masks[spike_ids][:, channel_ids]
        return Bunch(data=f,
                     masks=m,
                     spike_ids=spike_ids,
                     channel_ids=channel_ids,
                     )

    def add_feature_view(self, gui):
        v = FeatureView(features=self._get_features,
                        attributes={'time': self._get_spike_times}
                        )
        return self._add_view(gui, v)

    # Correlograms
    # -------------------------------------------------------------------------

    def _get_correlograms(self, cluster_ids, bin_size, window_size):
        spike_ids = self.selector.select_spikes(cluster_ids,
                                                self.n_spikes_correlograms,
                                                subset='random',
                                                )
        st = self.model.spike_times[spike_ids]
        sc = self.supervisor.clustering.spike_clusters[spike_ids]
        return correlograms(st,
                            sc,
                            sample_rate=self.model.sample_rate,
                            cluster_ids=cluster_ids,
                            bin_size=bin_size,
                            window_size=window_size,
                            )

    def add_correlogram_view(self, gui):
        m = self.model
        v = CorrelogramView(correlograms=self._get_correlograms,
                            sample_rate=m.sample_rate,
                            )
        return self._add_view(gui, v)

    # Amplitudes
    # -------------------------------------------------------------------------

    def _get_amplitudes(self, cluster_id):
        n = self.n_spikes_amplitudes
        m = self.model
        spike_ids = self.selector.select_spikes([cluster_id], n)
        channel_id = self.get_best_channel(cluster_id)
        x = m.spike_times[spike_ids]
        y = m.amplitudes[spike_ids, channel_id]
        return Bunch(x=x, y=y, data_bounds=(0., y.min(), m.duration, y.max()))

    def add_amplitude_view(self, gui):
        v = AmplitudeView(coords=self._get_amplitudes,
                          )
        return self._add_view(gui, v)

    # GUI
    # -------------------------------------------------------------------------

    def create_gui(self, **kwargs):
        gui = GUI(name=self.gui_name,
                  subtitle=self.model.data_path,
                  config_dir=self.config_dir,
                  **kwargs)

        self.supervisor.attach(gui)

        self.add_waveform_view(gui)
        if self.model.features is not None:
            self.add_feature_view(gui)
        self.add_correlogram_view(gui)
        if self.model.amplitudes is not None:
            self.add_amplitude_view(gui)

        # Save the memcache when closing the GUI.
        @gui.connect_
        def on_close():
            self.context.save_memcache()

        self.emit('gui_ready', gui)

        return gui


#------------------------------------------------------------------------------
# Neo GUI plugin
#------------------------------------------------------------------------------

def _run(data_path, **kwargs):  # pragma: no cover
    controller = NeoController(data_path, **kwargs)
    gui = controller.create_gui()
    gui.show()
    run_app()
    gui.close()
    del gui


class NeoGUIPlugin(IPlugin):
    """Create the `phy neo-gui` command for NEO files."""

    def attach_to_cli(self, cli):

        # Create the `phy cluster-manual file.exdir` command.
        @cli.command('neo-gui')  # pragma: no cover
        @click.argument('data-path', type=click.Path(exists=True))
        @click.option('--output-dir',
                      type=click.Path(file_okay=False, dir_okay=True),
                      help='Output directory.',
                      )
        @click.option('--output-ext',
                      type=click.STRING,
                      default='.exdir',
                      help=('Output extension, defaults to same as data-path' +
                           ' if extension is NEO writable, .exdir if not.'),
                      )
        @click.option('--output-name',
                      type=click.STRING,
                      help='Output file basename, defaults to same as data-path.',
                      )
        @click.option('--channel-group',
                      type=click.INT,
                      help='Channel group.',
                      )
        @click.option('--segment-num',
                      type=click.INT,
                      help='Segment number.',
                      )
        @click.option('--mode',
                      help='Mode to neo writer io.',
                      type=click.STRING,
                      default='',
                      )
        @click.pass_context
        def gui(ctx, data_path, **kwargs):
            """Launch the NEO GUI on a NEO readable file."""

            # Create a `phy.log` log file with DEBUG level.
            _add_log_file(op.join(op.dirname(data_path), 'phy.log'))

            create_app()

            _run_cmd('_run(data_path, **kwargs)',
                     ctx, globals(), locals())

        @cli.command('neo-describe')
        @click.argument('data-path', type=click.Path(exists=True))
        @click.option('--channel-group',
                      type=click.INT,
                      help='Channel group.',
                      )
        @click.option('--segment-num',
                      type=click.INT,
                      help='Segment number.',
                      )
        def describe(data_path, **kwargs):
            """Describe a NEO dataset."""
            NeoModel(data_path, **kwargs).describe()
