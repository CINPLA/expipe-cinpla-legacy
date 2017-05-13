import quantities as pq


axona_templates = [
    'mikkel_electrophysiology_L',
    'mikkel_electrophysiology_R', 'mikkel_notes',
    'hardware_inherit_axona_tracker',
    'hardware_inherit_axona_daq',
    'hardware_inherit_axona_camera_objective',
    'mikkel_inherit_tracking_environment',
    'mikkel_inherit_housing_environment',
    'mikkel_inherit_optic_fibre', 'mikkel_inherit_tetrode',
    'mikkel_inherit_drive_optetrode'
]

openephys_templates = [
    'mikkel_electrophysiology_L',
    'mikkel_electrophysiology_R', 'mikkel_notes',
    'hardware_inherit_openephys_daq',
    'hardware_inherit_intan_headstage',
    'hardware_inherit_pointgrey_camera_objective',
    'software_inherit_bonsai_gui',
    'software_inherit_openephys_gui',
    'mikkel_inherit_tracking_environment',
    'mikkel_inherit_housing_environment',
    'mikkel_inherit_optic_fibre', 'mikkel_inherit_tetrode',
    'mikkel_inherit_drive_optetrode'
]

opto_openephys_templates = [
    'hardware_inherit_openephys_optogenetics',
    'hardware_inherit_pulse_pal',
    'hardware_inherit_blue_laser',
    'hardware_inherit_laser_measure_device',
    'mikkel_laser_settings',
    'mikkel_pulse_pal_settings',
    'mikkel_optogenetics_paradigm',
    'mikkel_optogenetics_anatomical_location'
]

opto_axona_templates = [
    'hardware_inherit_axona_optogenetics',
    'hardware_inherit_pulse_pal',
    'hardware_inherit_blue_laser',
    'hardware_inherit_laser_measure_device',
    'mikkel_laser_settings',
    'mikkel_pulse_pal_settings',
    'mikkel_optogenetics_paradigm',
    'mikkel_optogenetics_anatomical_location'
]

possible_brain_areas = ['MECR', 'MECL', 'MS']
possible_locations = ['room2', 'room1']
obligatory_tags = ['no', 'yes', 'maybe']
possible_tags = ['GC', 'PC', 'BC', 'SC', 'HD', 'TC', 'theta'] + obligatory_tags

surgery_implantation_templates = [
    'mikkel_implant_drive_L', 'mikkel_implant_drive_R',
    'mikkel_implant_fibre', 'mikkel_subject',
    'mikkel_notes', 'mikkel_anaesthesia', 'mikkel_analgesia',
    'mikkel_analgesia_post', 'mikkel_anaesthesia_local',
    'mikkel_inherit_optic_fibre', 'mikkel_inherit_tetrode',
    'mikkel_inherit_drive_optetrode',
    'mikkel_inherit_housing_environment',
    'mikkel_inherit_surgery_station_environment'
]

surgery_injection_templates = [
    'mikkel_notes', 'mikkel_anaesthesia', 'mikkel_analgesia',
    'mikkel_analgesia_post', 'mikkel_anaesthesia_local',
    'mikkel_subject', 'mikkel_injection_1',
    'mikkel_injection_2',
    'mikkel_inherit_housing_environment',
    'mikkel_inherit_surgery_station_environment'
]

unit_info = {
    'info_waveform': {
        'alternatives': {
            'BS': 'definition: broad spiking waveform (putative excitatory)',
            'NS': 'definition: narrow spiking waveform (putative inhibitory)'
        },
        'type': 'string',
        'value': ""
    },
    'info_notes': {
        'type': 'string',
        'value': ""
    },
    'info_flag': {
        'alternatives': {
            'true': 'definition: this is an interesting unit',
            'false': 'definition: not worth looking into again'
        },
        'type': 'bolean',
        'value': "false"
    },
    'info_pheno_type': {
        'alternatives': {
            'GC': 'definition: grid cell',
            'PC': 'definition: place cell'
        },
        'type': 'string',
        'value': ""
    }
}

analysis_params = {
    'speed_filter': 5 * pq.m / pq.s,
    'pos_fs': 100 * pq.Hz,
    'f_cut': 6 * pq.Hz,
    'spat_binsize': 0.02 * pq.m,
    'spat_smoothing': 0.025,
    'grid_stepsize': 0.1 * pq.m,
    'box_xlen': 1 * pq.m,
    'box_ylen': 1 * pq.m,
    'ang_binsize': 4,
    'ang_n_avg_bin': 4,
    'imgformat': '.png',
    'corr_bin_width': 0.01 * pq.s,
    'corr_limit': 1. * pq.s,
    'isi_binsize': 1 * pq.ms,
    'isi_time_limit': 100 * pq.ms,
}

user_params = {
    'project_id': 'mikkel_septum_entorhinal',
    'user_name': None,
    'location': None,
    'laser_device_id': None
}
templates = {
    'axona': axona_templates,
    'opto_axona': opto_axona_templates,
    'openephys': openephys_templates,
    'opto_openephys': opto_openephys_templates,
    'surgery_implantation': surgery_implantation_templates,
    'surgery_injection': surgery_injection_templates,
    'adjustment': 'mikkel_drive_depth_adjustment'
}
