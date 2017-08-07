import exdir
import csv


def csv_to_dict(fname):
    with open(fname, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row_n, row in enumerate(spamreader):
            if row_n == 0:
                keys = row
                out = {key: list() for key in keys}
                continue
            for col_n, col in enumerate(row):
                if col.isnumeric():
                    if '.' in col:
                        col = float(col)
                    else:
                        col = int(col)
                out[keys[col_n]].append(col)
    return out


def parse_psychopy_openephys(exdir_path, psycho_path, io_channel):
    assert psycho_path.endswith('.csv')
    data = csv_to_dict(psycho_path)
    exdir_object = exdir.File(exdir_path)
    session = exdir_object['acquisition'].attrs['openephys_session']
    openephys_path = op.join(str(exdir_object['acquisition'].directory),
                             session)
    param = extract_laser_pulse(openephys_path)
    openephys_file = pyopenephys.File(openephys_path)
    times = openephys_file.digital_in_signals[0].times[io_channel]
    if len(times) == 0:
        raise ValueError('No recorded TTL signals on io channel ' +
                         str(io_channel))

    durations = pq.Quantity(np.array([param['pulse_phasedur']] * len(times)),
                            param['pulse_phasedur'].units)

    generate_epochs(exdir_path=exdir_path, times=times, durations=durations,
                    start_time=0 * pq.s,
                    stop_time=openephys_file.duration)


def generate_epochs(exdir_path, times, durations, **annotations):
    exdir_object = exdir.File(exdir_path)
    group = exdir_object.require_group('epochs')
    epo_group = group.require_group('Optogenetics')
    epo_group.attrs['num_samples'] = len(times)
    dset = epo_group.require_dataset('timestamps', data=times)
    dset.attrs['num_samples'] = len(times)
    dset = epo_group.require_dataset('durations', data=durations)
    dset.attrs['num_samples'] = len(durations)
    attrs = epo_group.attrs.to_dict()
    if annotations:
        attrs.update(annotations)
    epo_group.attrs = attrs

if __name__ == '__main__':
    import os.path as op
    psypath = op.join('/home','mikkel','Dropbox','scripting','python','expipe',
                       'psychopy','psychopymalinegen','data',
                       '_testMil_2017_jul_18_1336.csv')
    generate_epochs(None, psypath)
