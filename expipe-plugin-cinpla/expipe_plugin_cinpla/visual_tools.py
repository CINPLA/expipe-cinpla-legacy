from .imports import *


def parse_psychopy_openephys(action, psyexp_path, io_channel):
    exdir_path = action.require_filerecord().local_path
    exdir_object = exdir.File(exdir_path)
    session = exdir_object['acquisition'].attrs['openephys_session']
    openephys_path = os.path.join(str(exdir_object['acquisition'].directory),
                             session)
    settings = psychopyio.read_xml(psyexp_path)['PsychoPy2experiment']
    exp_name = psychopyio.list_dict_get(settings['Settings']['Param'], 'expName')
    psycho_data_path = os.path.join(os.path.dirname(psyexp_path), 'data')
    session = action.id.split('-')[-1]
    datestr = datetime.strftime(action.datetime, '%Y_%b_%d')
    assert len(action.subjects) == 1, 'Unable to find subject info in action.'
    psycho_search = '{}-{}_*-{}_{}*'.format(action.subjects[0], datestr,
                                           session, exp_name)
    psycho_paths = glob.glob(os.path.join(psycho_data_path, psycho_search))
    if len(psycho_paths) == 0: # try searching in openephys_path
        psycho_paths = glob.glob(os.path.join(openephys_path, psycho_search))
    if len(psycho_paths) != 3:
        raise ValueError('Did not found psychopy related files searching ' +
                         ' for "{}". '.format(psycho_search) +
                         'Please make sure the psychopy file names begins ' +
                         'with the correct "action-id" by using this as ' +
                         'the "participant" name in psychopy.')
    psycho_basepath = os.path.splitext(psycho_paths[0])[0]
    psycho_exts = [os.path.splitext(path)[-1] for path in psycho_paths]
    expected_exts = ['.log', '.csv', '.psydat']
    if not set(psycho_exts) == set(expected_exts):
        missing = [ext for ext in expected_exts if not ext in psycho_exts]
        raise ValueError('Missing file types "{}" in folder'.format(missing))
    psycho_paths.append(psyexp_path)
    for path in psycho_paths:
        shutil.copy2(path, openephys_path)
    csvdata = psychopyio.csv_to_dict(psycho_basepath + '.csv')
    stim_on, stim_off, durations = psychopyio.read_psychopy_log(psycho_basepath + '.log')
    if not len(stim_on) == len(csvdata['ori']):
        raise ValueError('Inconsistency in number of orientations and ' +
                         'stimulus onsets')
    openephys_file = pyopenephys.File(openephys_path)
    times = openephys_file.digital_in_signals[0].times[io_channel]
    if len(times) == 0:
        raise ValueError('No recorded TTL signals on io channel ' +
                         str(io_channel))
    rel_times = times - times[0]
    if not all(abs(psy_t - oe_t) < 0.01 for psy_t, oe_t in zip(stim_on, rel_times)):
        raise ValueError('Inconsistency in timestamps from psychopy and' +
                         ' timestamps from paralell port to open ephys.')
    blanks = np.hstack((0, times + durations)).magnitude * pq.s
    grating = {
        'grating': {
            'timestamps': times,
            'data': csvdata['ori'],
            # 'mode': csvdata['']
        },
        'blank': {
            'timestamps': blanks
        },
        'durations': durations
    }
    return grating


###############################################################################
#                  core parser functions for stimulus files
###############################################################################
def get_raw_inp_data(inp_group):
    # TODO: check tests
    '''
    Return raw data from axona inp data

    Parameters
    ----------
    inp_group : exdir.Group
        exdir group containing the inp data

    Returns
    -------
    event_types : array of stings
        event type, I, O, or K
    timestamps : array
        event timestamps
    values : array
            value of the event (bytes)
    '''
    event_types = inp_group["event_types"].data
    timestamps = pq.Quantity(inp_group["timestamps"].data, inp_group["timestamps"].attrs["unit"])
    values = inp_group["values"].data

    return event_types, timestamps, values


def convert_inp_values_to_keys(values):
    # TODO: check tests
    '''
    Converts inp values to keys (strings)

    Parameters
    ----------
    values : array_like
        event values, byte 6 and 7 (see DacqUSB doc)

    Returns
    -------
    keys : array_like
         pressed keys (strings)
    '''
    keys = [None] * len(values)
    for i in range(len(values)):
        if(values[i, 0].astype(int) != 0):
            raise ValueError("Cannot map a functional key event:", values[i, 0])
        else:
            key = str(chr(values[i, 1]))
            if(key == " "):
                keys[i] = "space"
            else:
                keys[i] = key

    return np.array(keys)


def get_key_press_events(inp_group):
    # TODO: check tests
    '''
    Parameters
    ----------
    inp_group : exdir.Group
        exdir group containing the inp data

    Returns
    -------
    data : dict
           dict with pressed keys and corrosponding timestamps
    '''
    event_types, timestamps, values = get_raw_inp_data(inp_group)

    data = {}
    event_ids = np.where(event_types == "K")[0]
    keys = convert_inp_values_to_keys(values[event_ids])
    data = {"timestamps": timestamps[event_ids],
            "keys": keys}

    return data


def _find_identical_trialing_elements(values):
    # TODO: check tests
    '''
    Finds indices of the first elements when there are two or more
    trialing elements with the same value

    Parameters
    ----------
    values : array_like
        event values

    Returns
    -------
    ids : list
             list of indices
    '''
    ids = []
    value_id = 0
    samples_count = len(values)
    while value_id < samples_count - 1:
        current_id = value_id
        current_value = values[value_id]
        rep_count = 1
        next_id = value_id + 1
        for i in range(next_id, samples_count):
            if values[i] == current_value:
                rep_count += 1
            else:
                value_id = i
                break
        if len(ids) != 0 and ids[-1] == current_id:
                break
        if rep_count > 1:
            ids.append(current_id)
    return ids


def get_synced_orientation_data(timestamps, values):
    # TODO: check tests
    '''
    Converts inp values to degrees

    Parameters
    ----------
    timestamps : array_like
        inp file timestamps

    values : array_like
        event values, byte 6 and 7 (see DacqUSB doc)

    Returns
    -------
    orientations : array of quantities
                    orientation in degrees
    t_stim : array of quantities
               stimulus onset times
    t_blank : array of quantities
                stimulus offset times
    '''
    orientations = None
    t_stim = None
    t_blank = None

    value = values[:, 1]  # Only the last byte is used to carry information
    ids = _find_identical_trialing_elements(value)  # ids confirmed to carry data
    if not ids:
        raise AssertionError("Could not find identical trialing elements, ids: ", ids)

    offset = value[ids[0]]  # first input is value for blank screen

    # If the last index is single and is a blank, add it to the ids
    if value[-1] != value[-2] and value[-1] == offset:
        id_last_element = len(value) - 1
        ids.append(id_last_element)

    times = timestamps[ids]
    offset_values = value[ids] - offset

    if (offset_values < 0).any():
        raise AssertionError("Negative numbers in offset values, offset_values: ", offset_values)

    # Find the corresponding orientations
    stim_ids = np.where(offset_values > 0)[0]  # 0 > corrospond to stimulus
    blank_ids = np.where(offset_values == 0)[0]  # 0 corrospond to blank

    # orientations are given in range [0, 360>.
    orientation_count = max(offset_values)
    orientations = (offset_values[stim_ids] - 1) * 360. / orientation_count

    t_stim = times[stim_ids]
    t_blank = times[blank_ids]

    return orientations * pq.deg, t_stim, t_blank


def get_grating_stimulus_events(inp_group, mode="orientation"):
    # TODO: check tests
    # TODO: add more read modes if necessary
    '''
    Parameters
    ----------
    inp_group : exdir.Group
        exdir group containing the inp data

    Returns
    -------
    data : dict
           dict with grating data and blank times.
           grating data includes timestamps and
           grating parameters (e.g. orientation)
    '''
    t_blank, t_stim, grating_param = None, None, None
    event_types, timestamps, values = get_raw_inp_data(inp_group)

    data = {}
    event_ids = np.where(event_types == "I")[0]

    if(mode == "orientation"):
        grating_param, t_stim, t_blank = get_synced_orientation_data(timestamps[event_ids], values[event_ids])
    else:
        raise NameError("unknown mode: ", mode)

    data["grating"] = {"timestamps": t_stim, "data": grating_param, "mode": mode}
    data["blank"] = {"timestamps": t_blank}

    return data


###############################################################################
#              stimulus group/epoch generate functions
###############################################################################
def generate_grating_stimulus_group(exdir_path, data, timestamps, mode="None"):
    '''
    Generates grating exdir group with timestamp dataset and
    data (eg. orientation) dataset.

    Parameters
    ----------
    exdir_path : string
            Path to exdir file

    data : array_like
        array with grating data (eg. orientation)

    timestamps : array_like

    mode: string, optional
        describes grating data
    '''
    exdir_file = exdir.File(exdir_path)
    stimulus = exdir_file.require_group("stimulus")
    presentation = stimulus.require_group("presentation")
    visual = presentation.require_group("visual")

    grating = visual.require_group("grating")
    grating.require_dataset("timestamps", data=timestamps)
    dset = grating.require_dataset("data", data=data)
    dset.attrs["mode"] = mode


def generate_blank_group(exdir_path, timestamps):
    '''
    Generates blank exdir group with timestamp dataset

    Parameters
    ----------
    exdir_path : string
            Path to exdir file

    timestamps : array_like
    '''
    exdir_file = exdir.File(exdir_path)
    stimulus = exdir_file.require_group("stimulus")
    presentation = stimulus.require_group("presentation")
    visual = presentation.require_group("visual")

    blank = visual.require_group("blank")
    blank.require_dataset("timestamps", data=timestamps)


def generate_key_event_group(exdir_path, keys, timestamps):
    '''
    Generates key press exdir group with timestamp
    dataset and key dataset.

    Parameters
    ----------
    exdir_path : string
            Path to exdir file

    keys : array_like
        array with pressed keys

    timestamps : array_like
    '''
    exdir_file = exdir.File(exdir_path)
    stimulus = exdir_file.require_group("stimulus")
    presentation = stimulus.require_group("presentation")
    key_press = presentation.require_group("key_press")

    key_press.require_dataset("timestamps", data=timestamps)
    key_press.require_dataset("keys", data=keys)


def generate_grating_stimulus_epoch(exdir_path, timestamps, durations, data):
    '''
    Generates visual stimulus epoch exdir group with timestamps
    and duration.

    Parameters
    ----------
    exdir_path : string
            Path to exdir file

    timestamps : array_like

    durations : array_like
    '''
    exdir_file = exdir.File(exdir_path)
    epochs = exdir_file.require_group("epochs")
    stim_epoch = epochs.require_group("visual_stimulus")
    stim_epoch.attrs["type"] = "visual_stimulus"
    times = stim_epoch.require_dataset('timestamps', data=timestamps)
    times.attrs['num_samples'] = len(timestamps)
    durations = stim_epoch.require_dataset('durations', data=durations)
    durations.attrs['num_samples'] = len(durations)
    data = stim_epoch.require_dataset('data', data=data)
    data.attrs['num_samples'] = len(data)


###############################################################################
#                           Bonsai parsing
###############################################################################
def copy_bonsai_raw_data(exdir_path, axona_filename):
    axona_file = pyxona.File(axona_filename)
    exdir_file = exdir.File(exdir_path)
    acquisition = exdir_file.require_group("acquisition")
    target_folder = acquisition.require_raw(axona_file.session)

    axona_dirname = os.path.dirname(axona_filename)
    csv_files = glob.glob(os.path.join(axona_dirname, "*.csv"))
    avi_files = glob.glob(os.path.join(axona_dirname, "*.avi"))

    for filename in csv_files + avi_files:
        shutil.copy(filename, target_folder)

    print("Copied files with extension .csv and .avi in session", axona_file.session + ".*", "to", target_folder)


def organize_bonsai_tracking_files(filepath):
    """
    Organizes the tracking data from bonsai

    Parameters
    ----------
    filepath : str
               path to .csv files

    Returns
    ----------
    out : dict
        dictionary of tracking filenames and keylogs
    """
    csv_files = glob.glob(os.path.join(filepath, "*.csv"))
    filenames = {}
    i = 0
    for f in csv_files:
        basename = os.path.basename(f)
        if basename.startswith("IR"):
            filenames["ir_camera_"+str(i)] = f
            i += 1
        elif basename.startswith("Overhead"):
            filenames["overhead_camera"] = f
        elif basename.startswith("Key"):
            filenames["key_log"] = f

    return filenames


def _remove_bad_positions(x1, y1, x2, y2,
                          t_start, t_stop):
    """
    Removes positions where both leds
    have position (0,0) or if is nan

    Parameters
    ----------
    x1 : array_like
        1d vector of x positions from led 1
    y1 : array_like
        1d vector of y positions from led 1
    x2 : array_like
        1d vector of x positions from led 2
    y2 : array_like
        1d vector of x positions from led 2
    t_start : array_like
        1d vector of timestamps for led 1
    t_stop : array_like
        1d vector of timestamps for led 2

    Returns
    ----------
    out : list
        coords and timestamps of both leds
        with bad positions removed:
        x1, y1, x2, y2, t_start, t_stop.
    """
    from exana.tracking.tools import rm_nans
    x1, y1, x2, y2, t_start, t_stop = rm_nans(x1, y1, x2, y2,
                                              t_start, t_stop)

    iszero_1 = (np.column_stack((x1, y1)) == 0).all(axis=1)
    iszero_2 = (np.column_stack((x2, y2)) == 0).all(axis=1)

    bad_ids = []
    for i, iszero in enumerate(iszero_1):
        if iszero and iszero_2[i]:
            bad_ids.append(i)

    out = []
    for arg in [x1, y1, x2, y2, t_start, t_stop]:
        if isinstance(arg, pq.Quantity):
            unit = arg.units
        else:
            unit = pq.Quantity(1,)
        out.append(np.delete(arg, bad_ids) * unit)
    return out


def _check_bonsai_processing_delay(t_start, t_stop, eps=1*pq.ms):
    """
    Checks if the delay due to bonsai processing is
    less than accepted value

    Parameters
    ----------
    t_start : array_like
            timestamps before processing

    t_stop : array_like
            timestamps after processing

    eps : Quantity, optinal
        accepted delay. Default is 1 ms.
    """
    try:
        assert(len(t_start) == len(t_stop))
    except AssertionError:
        print("Warning: t_start and t_stop have different length. Cannot compute Bonsai processing delay.")

    max_delay = (t_stop - t_start).max().rescale("ms")
    if max_delay > eps:
        print("Warning: Bonsai processing delay ({}) > accepted value ({})".format(round(max_delay, 2), eps))


def parse_bonsai_head_tracking_file(filepath):
    """
    Parses the tracking data from bonsai

    Parameters
    ----------
    filepath : str
               path to .csv file

    Returns
    ----------
    out : dict
        dictionary with position and time data
    """
    filename, extension = os.path.splitext(filepath)

    if extension != ".csv":
        raise ValueError("file extension must be '.csv'")

    data = pd.read_csv(filepath, sep=" ",
                       usecols=range(0, 6), parse_dates=[4, 5],
                       names=["x1", "y1", "x2", "y2", "t_start", "t_stop"])

    data["t_start"] = (data["t_start"] - data["t_start"][0]).astype('timedelta64[us]')
    data["t_stop"] = (data["t_stop"] - data["t_stop"][0]).astype('timedelta64[us]')

    t_start = np.array(data["t_start"]) / 1.e6 * pq.s
    t_stop = np.array(data["t_stop"]) / 1.e6 * pq.s

    if not len(t_start) == len(t_stop):
        print("Warning: t_start and t_stop have different length: ", len(t_start), " ", len(t_stop))

    # TODO: add dimention to coords
    unit = pq.Quantity(1,)
    x1 = np.array(data["x1"]) * unit
    y1 = np.array(data["y1"]) * unit

    y2 = np.array(data["y2"]) * unit
    x2 = np.array(data["x2"]) * unit

    x1, y1, x2, y2, t_start, t_stop = _remove_bad_positions(x1, y1, x2, y2,
                                                            t_start, t_stop)

    if t_start.size is not 0:
        _check_bonsai_processing_delay(t_start, t_stop)
    tracking = {"led_1": {"x": x1, "y": y1, "t": t_start},
                "led_2": {"x": x2, "y": y2, "t": t_start}
                }

    return tracking


def parse_bonsai_overhead_tracking_file(filepath):
    # TODO: parse overhead files
    pass


def generate_head_tracking_groups(exdir_path, tracking_data,
                                  camera_id, source_filename):
    """
    Save tracking data in an exdir Position group

    Parameters
    ----------
    exdir_path : string
            Path to exdir file

    tracking_data : dict
        dictionary with position and time data

    camera_id : str
            camera id

    """
    print("generating head tracking groups....")

    exdir_file = exdir.File(exdir_path)
    processing = exdir_file.require_group("processing")
    tracking = processing.require_group("tracking")
    head_tracking = tracking.require_group("head_tracking")
    camera = head_tracking.require_group(camera_id)
    camera.attrs["source_filename"] = source_filename
    position = camera.require_group("Position")

    for led, data in tracking_data.items():
        tracked_spot = position.require_group(led)
        timestamps = tracked_spot.require_dataset("timestamps", data=data["t"])
        tracked_spot.require_dataset(
            "data", data=np.column_stack((data["x"], data["y"])))


###############################################################################
#                           Plot functions
###############################################################################
def orient_raster_plots(stim_trials):
    pass
