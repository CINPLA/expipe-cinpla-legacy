
import logging
import os
import os.path as op
import shutil
import neo
import quantities as pq
import numpy as np
import copy
import shutil
try:
    import exdir
    HAVE_EXDIR = True
except Exception:
    HAVE_EXDIR = False
try:
    import nix
    HAVE_NIX = True
except Exception:
    HAVE_NIX = False

from phy.io.array import (_concatenate_virtual_arrays,
                          _index_of,
                          _spikes_in_clusters,
                          )

logger = logging.getLogger(__name__)

try:
    from klusta.traces import PCA as klusta_pca
    from klusta.klustakwik import klustakwik
    from klustakwik2.default_parameters import default_parameters
except ImportError:  # pragma: no cover
    logger.warn("Package klusta not installed: the NeoModel will not work.")


def copy_file_or_directory(fname, fname_copy):
    if op.isfile(fname):
        shutil.copy(fname, fname_copy)
    if op.isdir(fname):
        shutil.copytree(fname, fname_copy)


def delete_file_or_directory(fname):
    if op.isfile(fname):
        os.remove(fname)
    if op.isdir(fname):
        shutil.rmtree(fname)


def backup(path):
    backup = path + '.bak'
    if op.exists(backup):
        delete_file_or_directory(backup)
    if op.exists(path):
        copy_file_or_directory(path, backup)


# TODO make klustaexdir script that takes rawdata files and saves to exdir
# TODO check masks
# TODO probefile
# TODO save probe info in exdir
# TODO test if sorting spike times messes up anything


class NeoModel(object):
    n_pcs = 3

    def __init__(self, data_path, channel_group=None, segment_num=None,
                 output_dir=None, output_ext=None, output_name=None,
                 mode=False, kk2_params=None, **kwargs):
        self.feature_type = 'pca'
        self.data_path = op.abspath(data_path)
        if not op.exists(self.data_path):
            raise FileNotFoundError('Data path does not exist')
        self.segment_num = segment_num
        self.channel_group = channel_group
        self.output_dir = output_dir
        self.output_ext = output_ext
        self.output_name = output_name
        self.mode = mode
        self.kk2_metadata = kk2_params or default_parameters
        self.__dict__.update(kwargs) # overwrite above stuff with kwargs
        self.output_dir = self.output_dir or op.split(self.data_path)[0]
        fname, ext = op.splitext(op.split(self.data_path)[1])
        self.output_name = self.output_name or fname
        self.output_ext = self.output_ext or ext
        if self.output_ext[0] != '.':
            self.output_ext = '.' + self.output_ext

        # backup(self.data_path)

        save_path = op.join(self.output_dir, self.output_name +
                            self.output_ext)
        try:
            io = neo.get_io(save_path, mode=self.mode)
        except Exception: # cannot use mode
            try: # without mode
                io = neo.get_io(save_path)
            except FileNotFoundError: # file must be made, assuming this io cannot write
                logger.warn('Given output extension requires an existing ' +
                            'file, thus assuming it is not writable and ' +
                            'defaulting to ExdirIO or NIXIO for writing')
                if HAVE_EXDIR:
                    self.output_ext = '.exdir'
                elif HAVE_NIX:
                    self.output_ext = '.h5'
                else:
                    raise IOError("Neither exdir or nix is found, don't know" +
                                  " how to save data, please give a NEO " +
                                  "writable extention.")
                save_path = None
                io = False
            except:
                raise
        if io:
            if not io.is_writable:
                logger.warn('Given output extension is not writable, ' +
                            'defaulting to ExdirIO or NIXIO for writing')
                if hasattr(io, 'close'):
                    io.close()
                if HAVE_EXDIR:
                    self.output_ext = '.exdir'
                elif HAVE_NIX:
                    self.output_ext = '.h5'
                else:
                    raise IOError("Neither exdir or nix is found, don't know" +
                                  " how to save data, please give a NEO " +
                                  "writable extention.")
                save_path = None
        self.save_path = save_path or op.join(self.output_dir,
                                              self.output_name +
                                              self.output_ext)
        # backup(self.save_path)
        logger.debug('Saving output data to {}'.format(self.save_path))
        self.load_data()

    def describe(self):
        def _print(name, value):
            print("{0: <26}{1}".format(name, value))

        _print('Data file', self.data_path)
        _print('Channel group', self.channel_group)
        _print('Number of channels', len(self.channels))
        _print('Duration', '{}'.format(self.duration))
        _print('Number of spikes', self.n_spikes)
        _print('Available channel groups', self.channel_groups)

    def load_data(self, channel_group=None, segment_num=None):
        io = neo.get_io(self.data_path)
        print(self.data_path)
        assert io.is_readable
        self.channel_group = channel_group or self.channel_group
        self.segment_num = segment_num or self.segment_num
        if self.segment_num is None:
            self.segment_num = 0  # TODO find the right seg num
        if neo.Block in io.readable_objects:
            logger.info('Loading block')
            blk = io.read_block()  # TODO params to select what to read
            try:
                io.close()
            except:
                pass

            if not all(['group_id' in chx.annotations
                        for chx in blk.channel_indexes]):
                logger.warn('"group_id" is not in channel_index.annotations ' +
                            'counts channel_group as appended to ' +
                            'Block.channel_indexes')
                self._chxs = {i: chx for i, chx in
                              enumerate(blk.channel_indexes)}
            else:
                self._chxs = {int(chx.annotations['group_id']): chx
                              for chx in blk.channel_indexes}
            self.channel_groups = list(self._chxs.keys())

            self.seg = blk.segments[self.segment_num]
            if self.channel_group is None:
                self.channel_group = self.channel_groups[0]
            if self.channel_group not in self.channel_groups:
                raise ValueError('channel group not available,' +
                                 ' see available channel groups in neo-describe')
            self.chx = self._chxs[self.channel_group]
            self.sptrs = [st for st in self.seg.spiketrains
                          if st.channel_index == self.chx]
        elif neo.Segment in io.readable_objects:
            logger.info('Loading segment')
            self.seg = io.read_segment()
            self.segment_num = 0
            self.sptrs = self.seg.spiketrains
            self.chx = neo.ChannelIndex(
                index=[range(self.sptrs[0].waveforms.shape[1])],
                **{'group_id': 0}
            )

        self.duration = self.seg.t_stop - self.seg.t_start
        self.start_time = self.seg.t_start

        self.channel_ids = self.chx.index
        self.n_chans = len(self.chx.index)

        self.sample_rate = self.sptrs[0].sampling_rate.rescale('Hz').magnitude

        self.spike_times = self._load_spike_times()
        sorted_idxs = np.argsort(self.spike_times)
        self.spike_times = self.spike_times[sorted_idxs]
        ns, = self.n_spikes, = self.spike_times.shape

        self.spike_clusters = self._load_spike_clusters()[sorted_idxs]
        assert self.spike_clusters.shape == (ns,)

        self.cluster_groups = self._load_cluster_groups()

        self.waveforms = self._load_waveforms()[sorted_idxs, :, :]
        assert self.waveforms.shape[::2] == (ns, self.n_chans), '{} != {}'.format(self.waveforms.shape[::2], (ns, self.n_chans))

        self.features, self.masks = self._load_features_masks() # loads from waveforms which is already sorted

        self.amplitudes = self._load_amplitudes()
        assert self.amplitudes.shape == (ns, self.n_chans)

        # TODO load positino from params
        ch_pos = np.zeros((self.n_chans, 2))
        ch_pos[:, 1] = np.arange(self.n_chans)
        self.channel_positions = ch_pos

    def save(self, spike_clusters=None, groups=None, *labels):
        if spike_clusters is None:
            spike_clusters = self.spike_clusters
        assert spike_clusters.shape == self.spike_clusters.shape
        # assert spike_clusters.dtype == self.spike_clusters.dtype # TODO check if this is necessary
        self.spike_clusters = spike_clusters
        blk = neo.Block()
        seg = neo.Segment(name='Segment_{}'.format(self.segment_num),
                          index=self.segment_num)
        # seg.duration = self.duration
        blk.segments.append(seg)
        metadata = self.chx.annotations
        if labels:
            metadata.update({name: values for name, values in labels})
        chx = neo.ChannelIndex(index=self.chx.index,
                               name=self.chx.name,
                               **metadata)
        blk.channel_indexes.append(chx)
        try:
            wf_units = self.sptrs[0].waveforms.units
        except AttributeError:
            wf_units = pq.dimensionless
        clusters = np.unique(spike_clusters)
        self.cluster_groups = groups or self.cluster_groups
        for sc in clusters:
            mask = self.spike_clusters == sc
            waveforms = np.swapaxes(self.waveforms[mask], 1, 2) * wf_units
            sptr = neo.SpikeTrain(times=self.spike_times[mask] * pq.s,
                                  waveforms=waveforms,
                                  sampling_rate=self.sample_rate * pq.Hz,
                                  name='cluster #%i' % sc,
                                  t_stop=self.duration,
                                  t_start=self.start_time,
                                  **{'cluster_id': sc,
                                     'cluster_group': self.cluster_groups[sc].lower(),
                                     'kk2_metadata': self.kk2_metadata})
            sptr.channel_index = chx
            unt = neo.Unit(name='Unit #{}'.format(sc),
                           **{'cluster_id': sc,
                              'cluster_group': self.cluster_groups[sc].lower()})
            unt.spiketrains.append(sptr)
            chx.units.append(unt)
            seg.spiketrains.append(sptr)

        # save block to file
        try:
            io = neo.get_io(self.save_path, mode=self.mode)
        except Exception:
            io = neo.get_io(self.save_path)
        io.write_block(blk)
        if hasattr(io, 'close'):
            io.close()
        if self.output_ext == '.exdir':
            # save features and masks
            group = exdir.File(directory=self.save_path)
            self._exdir_save_group = self._find_exdir_channel_group(
                group["processing"]['electrophysiology']) # TODO not use elphys name
            if self._exdir_save_group is None:
                raise IOError('Can not find a dirctory corresponding to ' +
                              'channel_group {}'.format(self.channel_group))
            self.save_features_masks(spike_clusters)

    def save_features_masks(self, spike_clusters):
        # for saving phy data directly to disc
        feat = self._exdir_save_group.require_group('FeatureExtraction')
        feat.attrs['electrode_idx'] = self.chx.index
        dset = feat.require_dataset('data', data=self.features)
        dset.attrs['feature_type'] = self.feature_type
        dset.attrs['num_samples'] = self.features.shape[0]
        dset.attrs['num_channels'] = self.features.shape[1]
        dset.attrs['num_features'] = self.features.shape[2]
        feat.require_dataset('masks', data=self.masks)
        feat.require_dataset('timestamps', data=self.spike_times)

    def load_features_masks(self):
        # for saving phy data directly to disc
        feat = self._exdir_load_group['FeatureExtraction']
        # TODO check if right feature_type
        if not np.array_equal(feat['timestamps'].data, self.spike_times):
            raise ValueError('Extracted features have different timestamps' +
                             'than the spike times: \n{}\n{}'.format(
                feat['timestamps'].data,
                self.spike_times)
            )
        # HACK TODO memory mapped data cannot be overridden therefore convert to array issue #29 in exdir
        # return np.array(feat['data'].data), np.array(feat['masks'].data)
        return feat['data'].data, feat['masks'].data

    def _find_exdir_channel_group(self, exdir_group):
        # TODO assumes that electrode_group_id is in attributes of an electrode group
        for group in exdir_group.values():
            if 'electrode_group_id' in group.attrs:
                if group.attrs['electrode_group_id'] == self.channel_group:
                    return group
        return None

    def get_metadata(self, name):
        return None

    def get_waveforms(self, spike_ids, channel_ids):
        wf = self.waveforms
        return wf[spike_ids, :, :][:, :, channel_ids]

    def get_features_masks(self, spike_ids, channel_ids):
        # we select the primary principal component
        features = self.features[:, :, 0]
        features = features[spike_ids, :][:, channel_ids]
        features = np.reshape(features, (len(spike_ids), len(channel_ids)))
        masks = np.ones((len(spike_ids), len(channel_ids))) # TODO fix this
        return features, masks

    def cluster(self, spike_ids=None, channel_ids=None):
        if spike_ids is None:
            spike_ids = np.arange(self.n_spikes)
        if channel_ids is None:
            channel_ids = self.channel_ids
        features, masks = self.get_features_masks(spike_ids,
                                                  channel_ids)
        assert features.shape == masks.shape
        spike_clusters, metadata = klustakwik(features=features,
                                              masks=masks, **self.kk2_metadata)
        self.cluster_groups = {cl: 'unsorted' for cl in
                               np.unique(spike_clusters)}
        self.kk2_metadata.update(metadata)
        return spike_clusters

    def _load_features_masks(self):
        logger.debug("Loading features.")
        features = None
        if self.data_path.endswith('.exdir'):
            group = exdir.File(directory=self.data_path)
            self._exdir_load_group = self._find_exdir_channel_group(
                group["processing"]['electrophysiology'])
            if self._exdir_load_group is not None:
                if 'FeatureExtraction' in self._exdir_load_group:
                    features, masks = self.load_features_masks()
        if features is None:
            features, masks = self.calc_features_masks()
        return features, masks

    def calc_features_masks(self):
        masks = np.ones((self.n_spikes, self.n_chans))
        if self.feature_type == 'pca':
            pca = klusta_pca(self.n_pcs)
            pca.fit(self.waveforms, masks)
            features = pca.transform(self.waveforms)
        elif self.feature_type == 'amplitude':
            left_sweep = 0.2 * pq.ms  # TODO select left sweep
            # TODO select left_sweep
            m = int(self.sample_rate * left_sweep.rescale('s').magnitude)
            features = np.zeros((self.waveforms.shape[0], self.waveforms.shape[2], 3))
            features[:,:,0] = self.waveforms[:, m, :].reshape(self.waveforms.shape[0], self.waveforms.shape[2])
        return features, masks

    def _load_cluster_groups(self):
        logger.debug("Loading cluster groups.")
        if 'cluster_group' in self.sptrs[0].annotations:
            out = {sptr.annotations['cluster_id']:
                   sptr.annotations['cluster_group'] for sptr in self.sptrs}
        else:
            logger.warn('No cluster_group found in spike trains, naming all' +
                        ' "unsorted"')
            out = {i: 'unsorted' for i in np.unique(self.spike_clusters)}
        return out

    def _load_spike_times(self):
        logger.debug("Loading spike times.")
        out = np.array([t for sptr in self.sptrs
                        for t in sptr.times.rescale('s').magnitude])
        # HACK sometimes out is shape (n_spikes, 1)
        return np.reshape(out, len(out))

    def _load_spike_clusters(self):
        logger.debug("Loading spike clusters.")
        if 'cluster_id' in self.sptrs[0].annotations:
            try:
                out = np.array([i for sptr in self.sptrs for i in
                               [sptr.annotations['cluster_id']]*len(sptr)],
                               'int64')
            except KeyError:
                logger.debug("cluster_id not found in sptr annotations")
                raise
            except:
                raise
        else:
            logger.debug("cluster_id not found in sptr annotations, " +
                         "giving numbers from 0 to len(sptrs).")
            out = np.array([i for j, sptr in enumerate(self.sptrs)
                            for i in [j]*len(sptr)], 'int64')
        # NOTE sometimes out is shape (n_spikes, 1)
        # NOTE phy requires int64
        return np.reshape(out, len(out))

    def _load_waveforms(self):  # TODO this should be masks for memory saving
        logger.debug("Loading spike waveforms.")
        wfs = np.vstack([sptr.waveforms for sptr in self.sptrs])
        wfs = np.array(wfs, dtype=np.float64)
        assert wfs.shape[1:] == self.sptrs[0].waveforms.shape[1:]
        # neo: num_spikes, num_chans, samples_per_spike = wfs.shape
        return wfs.swapaxes(1, 2)

    def _load_amplitudes(self):
        logger.debug("Loading spike amplitudes.")
        left_sweep = 0.2 * pq.ms  # TODO select left sweep
        # TODO multiple sampling rates is not allowed
        mask = int(self.sample_rate * left_sweep.rescale('s').magnitude)
        out = self.waveforms[:, mask, :]
        return out
