# -*- coding: utf-8 -*-
"""
Class for reading data from a OpenEphys dataset

Depends on: scipy
            h5py >= 2.5.0

Supported: Read

Author: Mikkel E. Lepperød @CINPLA

"""
# TODO: multiple FPGAs

# needed for python 3 compatibility
from __future__ import absolute_import
from __future__ import division

import numpy as np
import quantities as pq
import os
import xml.etree.ElementTree as ET
#version checking
from distutils import version
# check h5py
try:
    import h5py
except ImportError as err:
    HAVE_H5PY = False
    H5PY_ERR = err
else:
    if version.LooseVersion(h5py.__version__) < '2.5.0':
        HAVE_H5PY = False
        H5PY_ERR = ImportError("your h5py version is too old to " +
                                 "support OpenEphysIO, you need at least 2.5.0 " +
                                 "You have %s" % h5py.__version__)
    else:
        HAVE_H5PY = True
        H5PY_ERR = None
# check scipy
try:
    from scipy import stats
except ImportError as err:
    HAVE_SCIPY = False
    SCIPY_ERR = err
else:
    HAVE_SCIPY = True
    SCIPY_ERR = None

# I need to subclass BaseIO
from neo.io.baseio import BaseIO

# to import from core
from neo.core import (Segment, SpikeTrain, Unit, Epoch, AnalogSignal, Block,
                      Event, IrregularlySampledSignal)
import neo.io.tools


class OpenEphysIO(BaseIO):
    """
    Class for "reading" experimental data from a OpenEphys file.

    Generates a :class:`Segment` with a :class:`AnalogSignal`

    """

    is_readable = True # This class can only read data
    is_writable = False # write is not supported

    supported_objects    = [ Block, Segment, AnalogSignal,
                          IrregularlySampledSignal, Event,
                          Epoch]

    # This class can return either a Block or a Segment
    # The first one is the default ( self.read )
    # These lists should go from highest object to lowest object because
    # common_io_test assumes it.
    readable_objects = [Block]

    # This class is not able to write objects
    writeable_objects = []

    has_header = False
    is_streameable = False

    name = 'OpenEphys'
    description = 'This IO reads experimental data from a OpenEphys dataset'
    extensions = ['kwe']
    mode = 'file'

    def __init__(self, filename, dataset=0):
        """
        Arguments:
            filename : the filename
            dataset : dataset number
            experimentNum : experiment number
        """
        BaseIO.__init__(self)
        self._filename = filename
        self._path, file = os.path.split(filename)
        self._dataset = dataset
        if int(file[-5]) > 1:
            xmlfile = 'settings_' + file[-5] + '.xml'
        else:
            xmlfile = 'settings.xml'
        tree = ET.parse(self._path + os.sep + xmlfile)
        root = tree.getroot()
        nodes = {}
        for processor in root.iter('PROCESSOR'):
            processorName = processor.attrib['name'].split('/')
            node_info = {}
            if processorName[0] == 'Sources':
                if processorName[1] == 'OSC Port':
                    oscInfo = processor.findall('EDITOR')
                    osc = oscInfo[0].findall('OSCNODE')
                    node_info['address'] = osc[0].get('address')
                    node_info['NodeId'] = processor.attrib['NodeId']
                elif processorName[1] == 'Rhythm FPGA':
                    chanInfo = processor.findall('CHANNEL_INFO')[0]
                    chan = [a.get('name') for a in chanInfo.findall('CHANNEL')]
                    node_info['chanNames'] = chan
                    node_info['NodeId'] = processor.attrib['NodeId']
                else:
                    node_info['NodeId'] = processor.attrib['NodeId']
                if processorName[1] in nodes.keys():
                    nodes[processorName[1]] += [node_info]
                else:
                    nodes[processorName[1]] = [node_info]
        self._nodes = nodes
        rawfile = file.split('.')[0] + '_' + nodes['Rhythm FPGA'][0]['NodeId'] + '.raw.kwd'
        self._kwe = h5py.File(filename, 'r')
        self._kwd = h5py.File(self._path + os.sep + rawfile, 'r')
        self._attrs = {}
        self._attrs['kwe'] = self._kwe['recordings'][str(self._dataset)].attrs
        self._attrs['kwd'] = self._kwd['recordings'][str(self._dataset)].attrs
        self._attrs['shape'] = self._kwd['recordings'][str(self._dataset)]['data'].shape
        self._attrs['app_data'] = self._kwd['recordings'][str(self._dataset)]['application_data'].attrs

    def read_block(self,
                     lazy=False,
                     cascade=True,
                     channel_index=None,
                     tracking=False,
                     tracking_ttl_chan=None,
                     stim_ttl_chan=None,
                    ):
        """
        Arguments:
            Channel_index: can be int, iterable or None to select one, many or
            all channel(s) respectively
            # TODO multiple stimulus channels
        """

        blk = Block()
        if cascade:
            seg = Segment(file_origin=self._path)
            blk.segments += [seg]

            # if channel_index:
            #     if type(channel_index) is int: channel_index = [ channel_index ]
            #     if type(channel_index) is list: channel_index = np.array( channel_index )
            # else:
            #     channel_index = np.arange(0,self._attrs['shape'][1])
            #
            # rcg = RecordingChannelGroup(name='all channels',
            #                      channel_indexes=channel_index)
            # blk.recordingchannelgroups.append(rcg)
            #
            # for idx in channel_index:
            #     # read nested analosignal
            #     ana = self.read_analogsignal(channel_index=idx,
            #                             lazy=lazy,
            #                             cascade=cascade,
            #                              )
            #     chan = RecordingChannel(index=int(idx))
            #     seg.analogsignals += [ ana ]
            #     chan.analogsignals += [ ana ]
            #     rcg.recordingchannels.append(chan)
            seg.duration = (self._attrs['shape'][0] /
                            self._attrs['kwe']['sample_rate']) * pq.s

            if lazy:
                pass
            else:
                if tracking:
                    if tracking_ttl_chan is not None:
                        events, irsigs = self._get_tracking(channel=tracking_ttl_chan,
                                                            conversion=1)
                        seg.Events += [events]
                    else:
                        irsigs = self._get_tracking(channel=tracking_ttl_chan,
                                                    conversion=1)
                    for irsig in irsigs:
                        seg.irregularlysampledsignals += [irsig]
                if stim_ttl_chan is not None:
                    try:
                        for chan in stim_ttl_chan:
                            epo = self._get_stim(channel=chan)
                            seg.epochs += [epo]
                    except:
                        epo = self._get_stim(channel=stim_ttl_chan)
                        seg.epochs += [epo]

            # neo.tools.populate_RecordingChannel(blk)
        blk.create_many_to_one_relationship()
        return blk

    def _get_tracking(self, channel, conversion):

        if channel is not None:
            eva = Event()
            ttls = self._kwe['event_types']['TTL']['events']['time_samples'].value
            event_channels = self._kwe['event_types']['TTL']['events'] ['user_data']['event_channels'].value
            event_id = self._kwe['event_types']['TTL']['events'] ['user_data']['eventID'].value
            eva.times = (ttls[(event_channels==channel) & (event_id == 1)] /
                         self._attrs['kwe']['sample_rate']) * pq.s
            eva.name = 'TrackingTTL'

        posdata = self._kwe['event_types']['Binary_messages']['events']['user_data']['Data'].value
        node_id = self._kwe['event_types']['Binary_messages']['events']['user_data']['nodeID'].value
        time_samples = self._kwe['event_types']['Binary_messages']['events']['time_samples'].value
        sigs = []
        for node in self._nodes['OSC Port']:
            irsig = IrregularlySampledSignal(
                signal=posdata[node_id == int(node['NodeId'])] * conversion * pq.m,
                times=(time_samples[node_id == int(node['NodeId'])] / self._attrs['kwe']['sample_rate']) * pq.s,
                name=node['address']
            )
            sigs += [irsig]
        if channel is not None:
            return eva, sigs
        else:
            return sigs

    def _get_stim(self, channel):
        epo = Epoch()
        ttls = self._kwe['event_types']['TTL']['events']['time_samples'].value
        event_channels = self._kwe['event_types']['TTL']['events']['user_data']['event_channels'].value
        event_id = self._kwe['event_types']['TTL']['events']['user_data']['eventID'].value
        epo.times = (ttls[(event_channels == channel) & (event_id==1)] / self._attrs['kwe']['sample_rate']) * pq.s
        off_times = (ttls[(event_channels == channel) & (event_id==0)] / self._attrs['kwe']['sample_rate']) * pq.s
        epo.durations = off_times - epo.times  # TODO check length match
        epo.name = 'StimulusTTL'
        return epo

    def read_analogsignal(self, channel_index=None, lazy=False, cascade=True):
        """
        Read raw traces
        Arguments:
            channel_index: must be integer
        """
        try:
            channel_index = int(channel_index)
        except TypeError:
            print('channel_index must be int, not %s' % type(channel_index))

        bit_volts = self._attrs['app_data']['channel_bit_volts']
        sig_unit = 'uV'
        if lazy:
            anasig = AnalogSignal([],
                                  units=sig_unit,
                                  sampling_rate=self._attrs['kwe']['sample_rate'] * pq.Hz,
                                  t_start=self._attrs['kwe']['start_time'] * pq.s,
                                  channel_index=channel_index,
                                  name=self._nodes['Rhythm FPGA'][0]['chanNames'][channel_index]
                                  )
            # we add the attribute lazy_shape with the size if loaded
            anasig.lazy_shape = self._attrs['shape'][0]
        else:
            data = self._kwd['recordings'][str(self._dataset)]['data'].value[:, channel_index]
            data = data * bit_volts[channel_index]
            anasig = AnalogSignal(data,
                                  units=sig_unit,
                                  sampling_rate=self._attrs['kwe']['sample_rate']*pq.Hz,
                                  t_start=self._attrs['kwe']['start_time']*pq.s,
                                  channel_index=channel_index,
                                  name=self._nodes['Rhythm FPGA'][0]['chanNames'][channel_index]
                                  )
            data = []  # delete from memory
        # for attributes out of neo you can annotate
        anasig.annotate(info='raw trace')
        return anasig
