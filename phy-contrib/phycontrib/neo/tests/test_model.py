# -*- coding: utf-8 -*-

"""Testing the Template model."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import logging

import numpy as np
from numpy.testing import assert_equal as ae
from pytest import raises

from phy.utils.testing import captured_output

from ..model import NeoModel
import neo
import quantities as pq
import os
import shutil
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------------


def test_load_save():
    n_channels = 5
    n_samples = 20
    n_spikes = 50
    fname = '/tmp/test_phy.exdir'
    if os.path.exists(fname):
        shutil.rmtree(fname)
    wf = np.random.random((n_spikes, n_channels, n_samples))
    ts = np.sort(np.random.random(n_spikes))
    t_stop = np.ceil(ts[-1])
    sptr = neo.SpikeTrain(times=ts, units='s', waveforms=wf * pq.V,
                          t_stop=t_stop, **{'group_id': 0})
    blk = neo.Block()
    seg = neo.Segment()
    seg.duration = t_stop
    blk.segments.append(seg)
    chx = neo.ChannelIndex(index=range(n_channels), **{'group_id': 0})
    blk.channel_indexes.append(chx)
    sptr.channel_index = chx
    unit = neo.Unit()
    unit.spiketrains.append(sptr)
    chx.units.append(unit)
    seg.spiketrains.append(sptr)
    epo = neo.Epoch()
    if os.path.exists(fname):
        shutil.rmtree(fname)
    io = neo.ExdirIO(fname)
    io.write_block(blk)
    wfswap = wf.swapaxes(1, 2)
    m = NeoModel(fname, overwrite=True)
    assert np.array_equal(m.spike_times, ts)
    assert np.array_equal(m.waveforms, wfswap)
    m.save()
    m2 = NeoModel(fname, overwrite=True)
    assert np.array_equal(m2.spike_times, ts)
    assert np.array_equal(m2.waveforms, wfswap)
    assert np.array_equal(m2.features, m.features)
    assert np.array_equal(m2.amplitudes, m.amplitudes)
    assert np.array_equal(m2.spike_clusters, m.spike_clusters)
    # TODO test number of calls
