import os
import os.path as op
import numpy as np
import expipe.io
from .action_tools import _get_local_path
import expipe
import sys
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import USER_PARAMS
    from expipe_params import ANALYSIS_PARAMS as par

# TODO select channel_group, delete names with channel group if selected


class Plotter:
    def __init__(self, action_id, ext='.png', save_figs=True,
                 close_fig=True, channel_group=None, no_local=False,
                 overwrite=False, skip=False):
        import exdir
        import exana.tracking as tr
        import quantities as pq
        import neo
        project = expipe.get_project(USER_PARAMS['project_id'])
        action = project.require_action(action_id)
        fr = action.require_filerecord()
        if not no_local:
            exdir_path = _get_local_path(fr)
        else:
            exdir_path = fr.server_path
        print('Initializing plotting for {}'.format(exdir_path))
        if ext[0] != '.':
            ext = '.' + ext
        self.overwrite = overwrite
        self.skip = skip
        self.ext = ext
        self.save_figs = save_figs
        self.close_fig = close_fig
        io = neo.ExdirIO(exdir_path)
        self.blk = io.read_block()
        self.seg = self.blk.segments[0]
        self.chxs = self.blk.channel_indexes
        channel_groups = [chx.annotations['group_id'] for chx in self.chxs]
        self.channel_group = channel_group or channel_groups
        assert isinstance(self.channel_group, list)
        self.anas = [ana for ana in self.seg.analogsignals
                     if ana.sampling_rate == 250 * pq.Hz]
        exdir_group = exdir.File(exdir_path)

        position_group = exdir_group['processing']['tracking']['camera_0']['Position']
        x1, y1, t1 = tr.get_raw_position(position_group['led_0'])
        try:
            x2, y2, t2 = tr.get_raw_position(position_group['led_1'])
        except KeyError:
            x2, y2, t2 = x1, y1, t1
            print("Only found one tracking led..")

        x, y, t = tr.select_best_position(x1, y1, t1, x2, y2, t2)
        self.ang, self.ang_t = tr.head_direction(x1, y1, x2, y2, t1,
                                                 return_rad=False)
        self.x, self.y, self.t = tr.interp_filt_position(x, y, t,
                                                         pos_fs=par['pos_fs'],
                                                         f_cut=par['f_cut'])
        self.x, self.y, self.t = self.x, self.y, self.t
        if len(self.seg.epochs) == 1:
            self.epoch = self.seg.epochs[0]
        else:
            self.epoch = None
        self._exdir_object = exdir.File(exdir_path)
        self._processing = self._exdir_object.require_group("processing")
        self._epochs = self._exdir_object.require_group("epochs")
        self._analysis = self._exdir_object.require_group("analysis")

    def savefig(self, fname, fig, dpi=300):
        import matplotlib.pyplot as plt
        if self.save_figs:
            if self.ext == '.pdf':
                fig.savefig(fname + self.ext, bbox_inches='tight')
            if self.ext == '.png':
                try:
                    fig.savefig(fname + self.ext, bbox_inches='tight', dpi=dpi)
                except OverflowError as e:
                    self.savefig(fname, fig, dpi=dpi-50)
        if self.close_fig:
            plt.close(fig)

    def _delete_figures(self, directory, channel_group):
        import glob
        name = 'Channel_group_{}*'.format(channel_group)
        files = glob.glob(op.join(directory, name))
        if len(files) > 0:
            if self.overwrite:
                pass
            if not self.overwrite and self.skip:
                return False
            if not self.overwrite and not self.skip:
                raise ValueError('Figures exist, use overwrite or skip')
        for fname in files:
            print('Deleting {}'.format(fname))
            os.remove(fname)
        return True

    def spatial_overview(self):
        import exana.tracking as tr
        from .make_spatiality_overview import make_spatiality_overview
        raw_dir = str(self._analysis.require_raw('spatial_overview').directory)
        os.makedirs(raw_dir, exist_ok=True)
        for nr, chx in enumerate(self.chxs):
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting spatial overview, ' +
                  'channel group {}'.format(group_id))
            for u, unit in enumerate(chx.units):
                if unit.name is None:
                    raise ValueError('unrecognized unit')
                if unit.annotations['cluster_group'].lower() == 'noise':
                    continue
                sptr = unit.spiketrains[0]
                fname = '{} {}'.format(chx.name, unit.name).replace(" ", "_")
                fpath = op.join(raw_dir, fname)
                try:
                    rate_map = tr.spatial_rate_map(self.x, self.y, self.t, sptr,
                                                   binsize=par['spat_binsize'],
                                                   box_xlen=par['box_xlen'],
                                                   box_ylen=par['box_ylen'],
                                                   mask_unvisited=False)
                    G, acorr = tr.gridness(rate_map, return_acorr=True,
                                           box_xlen=par['box_xlen'],
                                           box_ylen=par['box_ylen'])
                    fig = make_spatiality_overview(self.x, self.y, self.t, self.ang,
                                                   self.ang_t, sptr=sptr,
                                                   acorr=acorr, G=G,
                                                   mask_unvisited=True,
                                                   title=None,
                                                   ang_binsize=par['ang_binsize'],
                                                   rate_map=rate_map,
                                                   spike_size=1.)
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)
                    continue
                self.savefig(fpath, fig)

    def occupancy(self):
        import exana.tracking as tr
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        from mpl_toolkits.axes_grid1 import make_axes_locatable
        raw_dir = str(self._analysis.require_raw('occupancy').directory)
        os.makedirs(raw_dir, exist_ok=True)
        fname = 'occupancy_map'
        fpath = op.join(raw_dir, fname)
        print(fpath)
        # if op.isdir(raw_dir):
        #     os.removedirs(raw_dir)
        try:
            fig = plt.figure()
            gs = gridspec.GridSpec(20,9)
            ax1 = fig.add_subplot(gs[:9, 3:6])
            ax2 = fig.add_subplot(gs[11:, 3:6])
            tr.plot_path(self.x, self.y, self.t,
                            box_xlen=par['box_xlen'],
                            box_ylen=par['box_ylen'],
                            ax=ax1)
            im, max_t = tr.plot_occupancy(self.x, self.y, self.t,
                            binsize=par['spat_binsize'],
                            box_xlen=par['box_xlen'],
                            box_ylen=par['box_ylen'],
                            ax=ax2)
            divider = make_axes_locatable(ax2)
            cax = divider.append_axes("bottom", size="5%", pad=0.05)

            plt.colorbar(im, cax=cax)
            cbar = fig.colorbar(im, cax = cax, ticks= [int(0), max_t], orientation='horizontal')

            ax1.axis('tight')
            ax2.axis('tight')

            ax1.set_xticks([])
            ax1.set_yticks([])
            ax1.axes.xaxis.set_ticklabels([])
            ax1.axes.yaxis.set_ticklabels([])
            ax2.axis('off')
        except Exception as e:
            with open(fpath + '.exception', 'w+') as f:
                print(str(e), file=f)
        self.savefig(fpath, fig)

    def spatial_stim_overview(self):
        if self.epoch is None:
            print('There is no epochs related to this experiment')
            return
        from spatial_stim_overview import spatial_stim_overview
        raw_dir = (self._analysis.require_raw('spatial_stim_overview').directory)
        os.makedirs(raw_dir, exist_ok=True)
        for nr, chx in enumerate(self.chxs):
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting spatial stimulation overview, ' +
                  'channel group {}'.format(group_id))
            for u, unit in enumerate(chx.units):
                if unit.annotations['cluster_group'].lower() == 'noise':
                    continue
                sptr = unit.spiketrains[0]
                fname = '{} {}'.format(chx.name, unit.name).replace(" ", "_")
                fpath = op.join(raw_dir, fname)
                if group_id < 4:
                    id_list = range(4)
                else:
                    id_list = range(4, 8)
                anas = [ana for ana in self.seg.analogsignals
                        if ana.channel_index.annotations['group_id'] in id_list
                        and ana.sampling_rate == 250 * pq.Hz]
                try:
                    fig, data = spatial_stim_overview(spiketrain=sptr,
                                                      analogsignals=anas,
                                                      epoch=self.epoch,
                                                      pos_x=self.x, pos_y=self.y,
                                                      pos_t=self.t, pos_ang=self.ang,
                                                      pos_ang_t=self.ang_t
                                                      )
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)
                    continue
                self.savefig(fpath, fig)
                data.to_json(fpath + '.json', orient='index')

    def tfr(self):
        from exana.stimulus import epoch_overview
        from exana.time_frequency import plot_tfr
        import quantities as pq
        import neo
        raw_dir = str(self._analysis.require_raw('time_frequency').directory)
        os.makedirs(raw_dir, exist_ok=True)
        for chx in self.chxs:
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting time frequency representation, ' +
                  'channel group {}'.format(group_id))
            for num, ana in enumerate(chx.analogsignals): # TODO write the correct channel
                fname = '{} channelproxy {}'.format(chx.name, num).replace(" ", "_")
                fpath = op.join(raw_dir, fname)
                if self.epoch is not None:
                    epo_over = epoch_overview(self.epoch,
                                              np.median(np.diff(self.epoch.times)))
                    if len(epo_over.times) > 15:
                        with open(fpath + '.exception', 'w+') as f:
                            print('Counted {} '.format(len(epo_over.times)) +
                                  ' epochs and truncated to 15', file=f)
                        epo_over = neo.Epoch(times=epo_over.times[:15],
                                             durations=epo_over.durations[:15])
                else:
                    epo_over = None
                try:
                    fig = plot_tfr(ana, epoch=epo_over, f0=3, flim=[0, 120],
                                   plot_ana=True)
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)
                    continue
                self.savefig(fpath, fig)

    def psd(self):
        from exana.stimulus import epoch_overview
        from exana.time_frequency import plot_psd
        import quantities as pq
        import neo
        raw_dir = str(self._analysis.require_raw('power_spectrum_density').directory)
        os.makedirs(raw_dir, exist_ok=True)
        for chx in self.chxs:
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting power spectrum density, ' +
                  'channel group {}'.format(group_id))
            for num, ana in enumerate(chx.analogsignals): # TODO write the correct channel
                fname = '{} channelproxy {}_psd'.format(chx.name, num).replace(" ", "_")
                fpath = op.join(raw_dir, fname)
                try:
                    ax = plot_psd(ana, xlim=[0, 100], nperseg=2048)
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)
                    continue
                self.savefig(fpath, fig)

    def stimulation_statistics(self, ylim=[0, 30]):
        if self.epoch is None:
            print('There is no epochs related to this experiment')
            return
        from exana.stimulus import plot_psth
        from exana.stimulus import epoch_overview
        import quantities as pq
        import matplotlib.pyplot as plt
        raw_dir = str(self._analysis.require_raw('stimulation_statistics').directory)
        os.makedirs(raw_dir, exist_ok=True)
        for nr, chx in enumerate(self.chxs):
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting stimulation statistics, ' +
                  'channel group {}'.format(group_id))
            for u, unit in enumerate(chx.units):
                if unit.annotations['cluster_group'].lower() == 'noise':
                    continue
                sptr = unit.spiketrains[0]
                try:
                    fname = '{} {} stim macro'.format(chx.name, unit.name)
                    fpath = op.join(raw_dir, fname).replace(" ", "_")
                    epo_over = epoch_overview(self.epoch,
                                              np.median(np.diff(self.epoch.times)))
                    t_start = -np.round(epo_over.durations[0])
                    t_stop = np.round(epo_over.durations[0])
                    binsize = (abs(t_start) + abs(t_stop)) / 100.
                    fig = plt.figure()

                    plot_psth(sptr=sptr, epoch=epo_over, t_start=t_start,
                              t_stop=t_stop, output='counts', binsize=binsize,
                              fig=fig, ylim=ylim) # TODO does not manage to send ylim???
                    self.savefig(fpath, fig)
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)

                try:
                    fname = '{} {} stim micro'.format(chx.name, unit.name)
                    fpath = op.join(raw_dir, fname).replace(" ", "_")
                    fig = plt.figure()
                    t_start = -np.round(self.epoch.durations[0].rescale('ms')) * 3  # FIXME is milliseconds always good?
                    t_stop = np.round(self.epoch.durations[0].rescale('ms')) * 3
                    binsize = (abs(t_start) + abs(t_stop)) / 100.
                    plot_psth(sptr=sptr, epoch=self.epoch, t_start=t_start,
                              t_stop=t_stop, output='counts', binsize=binsize,
                              fig=fig)
                    self.savefig(fpath, fig)
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)

    def spike_lfp_coherence(self, xlim=[4, 16], color='b',
                            srch=[6, 10], show_max=False): # TODO plots everything twice
        from exana.time_frequency import plot_spike_psd, plot_psd
        from exana.misc.tools import normalize
        from matplotlib import gridspec
        import matplotlib.lines as mlines
        from matplotlib.ticker import MaxNLocator
        import elephant as el
        from exana.stimulus import epoch_overview
        import quantities as pq
        import neo
        import matplotlib.pyplot as plt
        import warnings
        # from .signal_tools import downsample_250
        raw_dir = str(self._analysis.require_raw('spike_lfp_coherence').directory)
        os.makedirs(raw_dir, exist_ok=True)
        starts = [self.blk.segments[0].t_start]
        stops = [self.blk.segments[0].t_stop]
        if self.epoch is not None:
            epo_over = epoch_overview(self.epoch,
                                      np.median(np.diff(self.epoch.times)))
            if len(epo_over) > 10:
                epo_over = None
                warnings.warn('More than 10 trains was found, skipping epoch')

            if epo_over is not None:
                starts = starts + [t for t in epo_over.times]
                stops = stops + [t + d for t, d in zip(epo_over.times, epo_over.durations)]

        for chx in self.chxs:
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting spike lfp coherence, ' +
                  'channel group {}'.format(group_id))

            if group_id < 4:
                id_list = range(4)
            else:
                id_list = range(4, 8)

            for u, unit in enumerate(chx.units):
                if unit.annotations['cluster_group'].lower() == 'noise':
                    continue
                fig = plt.figure(figsize=(12 * len(starts), 20))
                gs_main = gridspec.GridSpec(1, len(starts))

                fname = '{} {}'.format(chx.name, unit.name)
                fpath = op.join(raw_dir, fname).replace(" ", "_")

                ylim_sptr_spec = []
                ylim_ana_spec = []
                ylim_coher = []
                axs_sptr_spec = []
                axs_ana_spec = []
                axs_coher = []

                for plot_num, (t_start, t_stop) in enumerate(zip(starts, stops)):
                    sptr = unit.spiketrains[0]
                    sptr = sptr[(sptr.times > t_start) & (sptr.times < t_stop)]

                    sliced_anas = []
                    sampling_rates = [ana.sampling_rate
                                      for ana in self.seg.analogsignals]
                    if len(np.unique(sampling_rates)) > 1:
                        warnings.warn('Found multiple sampling rates, selecting minimum')
                    target_rate = min(sampling_rates)
                    anas = [ana for ana in self.seg.analogsignals
                            if ana.sampling_rate == target_rate and
                            ana.channel_index.annotations['group_id'] in id_list]

                    for ana in anas:
                        mask = (ana.times > t_start) & (ana.times < t_stop)
                        sliced_anas.append(
                            neo.AnalogSignal(
                                ana.magnitude[mask, :] * ana.units,
                                sampling_rate=ana.sampling_rate,
                                t_start=0 * pq.s
                            )
                        )
                    # anas = downsample_250(anas)
                    ana_arr = np.array([np.reshape(ana.magnitude, len(ana))
                                        for ana in anas])
                    ana_arr = neo.AnalogSignal(signal=ana_arr.T * anas[0].units,
                                               sampling_rate=ana.sampling_rate,
                                               t_start=0 * pq.s)

                    gs = gridspec.GridSpecFromSubplotSpec(
                        3, 1, subplot_spec=gs_main[0, plot_num])

                    ax_sptr_spec = fig.add_subplot(gs[0])
                    plot_spike_psd([sptr], xlim=xlim,
                                   mark_max=False, NFFT=6000, title=None,
                                   xlabel=None, color=color, ax=ax_sptr_spec,
                                   ylabel=None, ylim=None)
                    ax_sptr_spec.ticklabel_format(style='sci',
                                                  scilimits=(-3, 4),
                                                  axis='y')
                    ax_sptr_spec.tick_params(axis='y', pad=8)

                    plt.setp(ax_sptr_spec.get_xticklabels(), visible=False)
                    # lfp psd
                    # TODO select proper lfp signal
                    ax_ana_spec = fig.add_subplot(gs[1])
                    plot_psd(sliced_anas, color=color, xlim=xlim,
                             mark_max=False, nperseg=2048, ylim=None,
                             fcn=lambda inp: normalize(inp, mode='zscore'),
                             title=None, ax=ax_ana_spec, xlabel=False,
                             ylabel=None, max_power=show_max, srch=srch,
                             legend=False)

                    plt.setp(ax_ana_spec.get_xticklabels(), visible=False)
                    ax_ana_spec.yaxis.set_major_locator(MaxNLocator(prune='both'))

                    ax_coher = fig.add_subplot(gs[2])
                    sptr.t_stop = ana_arr.t_stop
                    sig, freqs = el.sta.spike_field_coherence(ana_arr, sptr,
                                                              **{'nperseg': 2048})
                    if not np.isfinite(sig).all():
                        warnings.warn('Coherence is all NAN')
                    if show_max:
                        freqs = freqs.magnitude
                        idx = np.argmax(np.max(sig[(freqs > srch[0]) &
                                                   (freqs < srch[1]), :], axis=0))
                        sig = sig[:, idx]
                        ax_coher.plot(freqs, sig, color=color)
                    else:
                        ax_coher.plot(freqs, sig)
                    ax_coher.set_xlim(xlim)

                    ax_coher.set_xlabel('Frequency [Hz]')
                    ax_coher.set_ylabel('Coherence')
                    ax_sptr_spec.set_ylabel('Spike power')
                    ax_ana_spec.set_ylabel('LFP power')
                    ylim_sptr_spec.append(ax_sptr_spec.get_ylim()[1])
                    ylim_ana_spec.append(ax_ana_spec.get_ylim()[1])
                    ylim_coher.append(ax_coher.get_ylim()[1])
                    axs_sptr_spec.append(ax_sptr_spec)
                    axs_ana_spec.append(ax_ana_spec)
                    axs_coher.append(ax_coher)

                for ax in axs_sptr_spec:
                    ax.set_ylim([0, max(ylim_sptr_spec)])
                for ax in axs_ana_spec:
                    ax.set_ylim([0, max(ylim_ana_spec)])
                for ax in axs_coher:
                    ax.set_ylim([0, max(ylim_coher)])
                self.savefig(fpath, fig)

    def spike_statistics(self, color='b'):
        from exana.waveform import (plot_amp_clusters, plot_waveforms)
        from exana.statistics import correlogram, plot_isi_hist
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        raw_dir = str(self._analysis.require_raw('spike_statistics').directory)
        os.makedirs(raw_dir, exist_ok=True)
        for nr, chx in enumerate(self.chxs):
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            print('Plotting spike statistics, ' +
                  'channel group {}'.format(group_id))
            for u, unit in enumerate(chx.units):
                if unit.name is None:
                    raise ValueError('unrecognized unit')
                if unit.annotations['cluster_group'].lower() == 'noise':
                    continue
                sptr = unit.spiketrains[0]

                try:
                    fname = '{} {}'.format(chx.name, unit.name)
                    fpath = op.join(raw_dir, fname).replace(" ", "_")
                    fig = plt.figure()
                    nrc = sptr.waveforms.shape[1]
                    gs = gridspec.GridSpec(2*nrc+4, 2*nrc+4)
                    plot_waveforms(sptr=sptr, color=color, fig=fig, gs=gs[:nrc+1, :nrc+1])
                    plot_amp_clusters([sptr], colors=[color], fig=fig, gs=gs[:nrc+1, nrc+2:])
                    bin_width = par['corr_bin_width'].rescale('s').magnitude
                    limit = par['corr_limit'].rescale('s').magnitude
                    count, bins = correlogram(t1=sptr.times.magnitude, t2=None,
                                              bin_width=bin_width, limit=limit,
                                              auto=True)
                    ax_cor = fig.add_subplot(gs[nrc+3:, :nrc+1])
                    ax_cor.bar(bins[:-1] + bin_width / 2., count, width=bin_width,
                               color=color)
                    ax_cor.set_xlim([-limit, limit])

                    ax_isi = fig.add_subplot(gs[nrc+3:, nrc+2:])
                    plot_isi_hist(sptr.times, alpha=1, ax=ax_isi, binsize=par['isi_binsize'],
                                  time_limit=par['isi_time_limit'], color=color, )
                    self.savefig(fpath, fig)
                except Exception as e:
                    with open(fpath + '.exception', 'w+') as f:
                        print(str(e), file=f)

    def orient_tuning_overview(self):
        import exana.stimulus as st
        try:
            stim_epoch = st.get_epoch(self.seg.epochs, "visual_stimulus")
        except ValueError:
            print("Could not find epoch of type 'visual_stimulus'")
            raise
        raw_dir = str(self._analysis.require_raw('orient_tuning_overview').directory)
        os.makedirs(raw_dir, exist_ok=True)
        stim_off_epoch = st.make_stimulus_off_epoch(stim_epoch)
        off_rates = st.compute_spontan_rate(self.chxs, stim_off_epoch)

        stim_trials = st.make_stimulus_trials(self.chxs, stim_epoch)
        for nr, chx in enumerate(self.chxs):
            group_id = chx.annotations['group_id']
            if group_id not in self.channel_group:
                continue
            if not self._delete_figures(raw_dir, group_id):
                continue
            for u, unit in enumerate(chx.units):
                if unit.annotations.get('cluster_group') == 'Good':
                    print('Plotting orientation tuning, ' +
                          'channel group {}'.format(group_id))
                    unit_id = unit.annotations["cluster_id"]
                    trials = stim_trials[chx.name][unit_id]
                    off_rate = off_rates[chx.name][unit_id]

                    fname = 'raster {} Unit {}'.format(chx.name, u)
                    fpath = op.join(raw_dir, fname).replace(" ", "_")
                    fig = st.orient_raster_plots(trials)
                    self.savefig(fpath, fig)

                    fname = 'tuning {} Unit {}'.format(chx.name, u)
                    fpath = op.join(raw_dir, fname).replace(" ", "_")
                    fig = st.plot_tuning_overview(trials, off_rate)
                    self.savefig(fpath, fig)
