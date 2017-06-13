from __future__ import division
from __future__ import print_function
from __future__ import with_statement

import platform
import locale
import quantities as pq
import numpy as np


def _fread_QString(f):  
    a = ''
    length = np.fromfile(f, 'u4', 1)[0]

    if hex(length) == '0xffffffff':
        print('return fread_QString')
        return

    # convert length from bytes to 16-bit Unicode words
    length = int(length / 2)

    for ii in range(length):
        newchar = np.fromfile(f, 'u2', 1)[0]
        a += newchar.tostring().decode('utf-16')
    return a

def _plural(n):

    # s = plural(n)
    #
    # Utility function to optionally plurailze words based on the value
    # of n.

    if n == 1:
        s = ''
    else:
        s = 's'

    return s

def get_rising_falling_edges(idx_high):
    '''

    :param idx_high: indeces where dig signal is '1'
    :return: rising and falling indices lists
    '''
    rising = []
    falling = []

    idx_high = idx_high[0]

    if len(idx_high) != 0:
        for i, idx in enumerate(idx_high[:-1]):
            if i==0:
                # first idx is rising
                rising.append(idx)
            else:
                if idx_high[i+1] != idx + 1:
                    falling.append(idx)
                if idx - 1 != idx_high[i-1]:
                    rising.append(idx)

    return rising, falling


def clip_anas(analog_signals, times, clipping_times, start_end):
    '''

    :param analog_signals:
    :param times:
    :param clipping_times:
    :param start_end:
    :return:
    '''

    if len(analog_signals.signal) != 0:
        times.rescale(pq.s)
        if len(clipping_times) == 2:
            idx = np.where((times > clipping_times[0]) & (times < clipping_times[1]))
        elif len(clipping_times) ==  1:
            if start_end == 'start':
                idx = np.where(times > clipping_times[0])
            elif start_end == 'end':
                idx = np.where(times < clipping_times[0])
        else:
            raise AttributeError('clipping_times must be of length 1 or 2')

        if len(analog_signals.signal.shape) == 2:
            anas_clip = analog_signals.signal[:, idx[0]]
        else:
            anas_clip = analog_signals.signal[idx[0]]

        return anas_clip
    else:
        return []


def clip_digs(digital_signals, clipping_times, start_end):
    '''

    :param digital_signals:
    :param clipping_times:
    :param start_end:
    :return:
    '''

    digs_clip = []
    for i, dig in enumerate(digital_signals.times):
        dig.rescale(pq.s)
        if len(clipping_times) == 2:
            idx = np.where((dig > clipping_times[0]) & (dig < clipping_times[1]))
        elif len(clipping_times) == 1:
            if start_end == 'start':
                idx = np.where(dig > clipping_times[0])
            elif start_end == 'end':
                idx = np.where(dig < clipping_times[0])
        else:
            raise AttributeError('clipping_times must be of length 1 or 2')
        if start_end != 'end':
            digs_clip.append(dig[idx] - clipping_times[0])
        else:
            digs_clip.append(dig[idx])

    return np.array(digs_clip) * pq.s


def clip_times(times, clipping_times, start_end):
    '''

    :param times:
    :param clipping_times:
    :param start_end:
    :return:
    '''
    times.rescale(pq.s)

    if len(clipping_times) == 2:
        idx = np.where((times > clipping_times[0]) & (times < clipping_times[1]))
    elif len(clipping_times) ==  1:
        if start_end == 'start':
            idx = np.where(times > clipping_times[0])
        elif start_end == 'end':
            idx = np.where(times < clipping_times[0])
    else:
        raise AttributeError('clipping_times must be of length 1 or 2')
    if start_end != 'end':
        times_clip = times[idx] - clipping_times[0]
    else:
        times_clip = times[idx]

    return times_clip

def clip_stimulation(stimulation, times, clipping_times, start_end):
    '''

    :param stimulation:
    :param times:
    :param clipping_times:
    :param start_end:
    :return:
    '''
    if len(stimulation.stim_signal) != 0:
        if len(clipping_times) == 2:
            idx = np.where((times > clipping_times[0]) & (times < clipping_times[1]))
        elif len(clipping_times) ==  1:
            if start_end == 'start':
                idx = np.where(times > clipping_times[0])
            elif start_end == 'end':
                idx = np.where(times < clipping_times[0])
        else:
            raise AttributeError('clipping_times must be of length 1 or 2')

        if len(stimulation.stim_signal.shape) == 2:
            stim_clip = stimulation.stim_signal[:, idx[0]]
        else:
            stim_clip = stimulation.stim_signal[idx[0]]

        return stim_clip
    else:
        return []