import exdir
import shutil
import glob
import os
import quantities as pq
import numpy as np

# from expipe.core import Filerecord
# from expipe.core import user
# from expipe import settings
import os.path as op

# TODO inform database about openephys data being included
# TODO SpikeTrain class - needs klusta stuff


def _prepare_exdir_file(exdir_file):
    general = exdir_file.require_group("general")
    subject = general.require_group("subject")
    processing = exdir_file.require_group("processing")
    epochs = exdir_file.require_group("epochs")

    return general, subject, processing, epochs


def convert(openephys_rec, exdir_path, session):
    exdir_file = exdir.File(exdir_path)
    experiment = openephys_rec.experiment
    dtime = experiment.datetime.strftime('%Y-%m-%dT%H:%M:%S')
    exdir_file.attrs['session_start_time'] = dtime
    exdir_file.attrs['session_duration'] = openephys_rec.duration
    acquisition = exdir_file.require_group("acquisition")
    general = exdir_file.require_group("general")

    target_folder = op.join(str(acquisition.directory), session)
    acquisition.attrs["openephys_session"] = session
    acquisition.attrs["acquisition_system"] = experiment.acquisition_system

    print("Copying ", openephys_rec.absolute_foldername, " to ", target_folder)
    shutil.copytree(experiment.file.absolute_foldername, target_folder)


def _prepare_channel_groups(exdir_path, openephys_rec):
    exdir_file = exdir.File(exdir_path)
    general, subject, processing, epochs = _prepare_exdir_file(exdir_file)
    exdir_channel_groups = []
    elphys = processing.require_group('electrophysiology')
    for openephys_channel_group in openephys_rec.channel_groups:
        exdir_channel_group = elphys.require_group(
            "channel_group_{}".format(openephys_channel_group.id))
        exdir_channel_groups.append(exdir_channel_group)
        channel_identities = np.array([ch.index for ch in openephys_channel_group.channels])
        exdir_channel_group.attrs['start_time'] = 0 * pq.s
        exdir_channel_group.attrs['stop_time'] = openephys_rec.duration
        exdir_channel_group.attrs["electrode_identities"] = channel_identities
        exdir_channel_group.attrs["electrode_idx"] = channel_identities - channel_identities[0]
        exdir_channel_group.attrs['electrode_group_id'] = openephys_channel_group.id
        # TODO else=test if attrs are the same
    return exdir_channel_groups


def generate_lfp(exdir_path, openephys_rec):
    import scipy.signal as ss
    import copy
    exdir_channel_groups = _prepare_channel_groups(exdir_path, openephys_rec)
    for channel_group, openephys_channel_group in zip(exdir_channel_groups,
                                                      openephys_rec.channel_groups):
        lfp = channel_group.require_group("LFP")
        group_id = openephys_channel_group.id
        print('Generating LFP, channel group ', group_id)
        for channel in openephys_channel_group.channels:
                lfp_timeseries = lfp.require_group(
                    "LFP_timeseries_{}".format(channel.index)
                )
                analog_signal = openephys_channel_group.analog_signals[channel.index]
                # decimate
                target_rate = 1000 * pq.Hz
                signal = np.array(analog_signal.signal, dtype=float)
                sample_rate = copy.copy(openephys_rec.sample_rate)
                qs = [10, int((openephys_rec.sample_rate / target_rate) / 10)]
                for q in qs:
                    signal = ss.decimate(signal, q=q, zero_phase=True)
                    sample_rate /= q
                t_stop = len(signal) / sample_rate
                assert round(t_stop, 1) == round(openephys_rec.duration, 1), '{}, {}'.format(t_stop, openephys_rec.duration)
                signal = signal * channel.gain
                lfp_timeseries.attrs["num_samples"] = len(signal)
                lfp_timeseries.attrs["start_time"] = 0 * pq.s
                lfp_timeseries.attrs["stop_time"] = t_stop
                lfp_timeseries.attrs["sample_rate"] = sample_rate
                lfp_timeseries.attrs["electrode_identity"] = analog_signal.channel_id
                lfp_timeseries.attrs["electrode_idx"] = analog_signal.channel_id - openephys_channel_group.id * 4
                lfp_timeseries.attrs['electrode_group_id'] = group_id
                data = lfp_timeseries.require_dataset("data", data=signal)
                data.attrs["num_samples"] = len(signal)
                # NOTE: In exdirio (python-neo) sample rate is required on dset #TODO
                data.attrs["sample_rate"] = sample_rate


def generate_spike_trains(exdir_path, openephys_rec, source='klusta'):
    import neo
    if source == 'klusta': # TODO acquire features and masks
        print('Generating spike trains from KWIK file')
        exdir_file = exdir.File(exdir_path)
        acquisition = exdir_file["acquisition"]
        openephys_session = acquisition.attrs["openephys_session"]
        openephys_directory = op.join(str(acquisition.directory), openephys_session, 'klusta')
        kwikfiles = [f for f in os.listdir(openephys_directory) if f.endswith('_klusta.kwik')]
        for kwikfile in kwikfiles:
            kwikfile = op.join(openephys_directory, kwikfile)
            if op.exists(kwikfile):
                kwikio = neo.io.KwikIO(filename=kwikfile,)
                blk = kwikio.read_block(raw_data_units='uV')
                seg = blk.segments[0]
                try:
                    exdirio = neo.io.ExdirIO(exdir_path)
                    exdirio.write_block(blk)
                except Exception:
                    print('WARNING: unable to convert\n', kwikfile)
        if len(kwikfiles) == 0:
            raise IOError('.kwik file cannot be found in ' + openephys_directory)
    elif source == 'openephys':
        exdirio = neo.io.ExdirIO(exdir_path)
        for oe_group in openephys_rec.channel_groups:
            channel_ids = [ch.id for ch in oe_group.channels]
            channel_index = [ch.index for ch in oe_group.channels]
            chx = neo.ChannelIndex(
                name='channel group {}'.format(oe_group.id),
                channel_ids=channel_ids,
                index=channel_index,
                group_id=oe_group.id
            )
            for sptr in oe_group.spiketrains:
                unit = neo.Unit(
                    cluster_group='unsorted',
                    cluster_id=sptr.attrs['cluster_id'],
                    name=sptr.attrs['name']
                )
                unit.spiketrains.append(
                    neo.SpikeTrain(
                        times=sptr.times,
                        waveforms=sptr.waveforms,
                        sampling_rate=sptr.sample_rate,
                        t_stop=sptr.t_stop,
                        **sptr.attrs
                    )
                )
                chx.units.append(unit)
            exdirio.write_channelindex(chx, start_time=0 * pq.s,
                                       stop_time=openephys_rec.duration)
    else:
        raise ValueError(source + ' not supported')


def generate_tracking(exdir_path, openephys_rec):
    exdir_file = exdir.File(exdir_path)
    general, subject, processing, epochs = _prepare_exdir_file(exdir_file)
    tracking = processing.require_group('tracking')
    # NOTE openephys supports only one camera, but other setups might support several
    camera = tracking.require_group("camera_0")
    position = camera.require_group("Position")
    position.attrs['start_time'] = 0 * pq.s
    # TODO update to new
    position.attrs['stop_time'] = openephys_rec.duration
    for n, tracking in enumerate(openephys_rec.tracking):
        x, y, times = tracking.x, tracking.y, tracking.times
        led = position.require_group("led_" + str(n))
        dset = led.require_dataset('data', data=np.vstack((x, y)).T * pq.m)
        dset.attrs['num_samples'] = len(times)
        dset = led.require_dataset("timestamps", data=times)
        dset.attrs['num_samples'] = len(times)
        led.attrs['start_time'] = 0 * pq.s
        led.attrs['stop_time'] = openephys_rec.duration
