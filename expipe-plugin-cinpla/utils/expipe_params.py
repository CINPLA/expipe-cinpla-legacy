import quantities as pq

'''
This is an example parameter file to use with expipe-plugin-cinpla.

If you add _inherit_ before the name of a template it is asumed that you
want to "inherit" this module from the project. This is for modules
that are general and which you dont want to repeat in every action.
Note that you can modify these modules afterwords, then the modification
will be overloaded for that particular action.
'''


#  these are templates you want to add to each recording perfomed with axona
axona_templates = [
    'mikkel_electrophysiology_L',
    'mikkel_electrophysiology_R',
    '_inherit_hardware_axona_tracker',
    '_inherit_hardware_axona_daq',
    '_inherit_hardware_axona_camera_objective',
    '_inherit_environment_open_field_tracking',
    '_inherit_environment_rat_housing',
    '_inherit_hardware_optic_fibre', '_inherit_hardware_tetrode',
    '_inherit_hardware_microdrive_optetrode'
]


#  these are templates you want to add to each recording perfomed with
#  open ephys
openephys_templates = [
    'mikkel_electrophysiology_L',
    'mikkel_electrophysiology_R',
    '_inherit_hardware_openephys_daq',
    '_inherit_hardware_intan_headstage',
    '_inherit_hardware_pointgrey_camera_objective',
    '_inherit_software_bonsai_gui',
    '_inherit_software_openephys_gui',
    '_inherit_environment_open_field_tracking',
    '_inherit_environment_rat_housing',
    '_inherit_hardware_optic_fibre', '_inherit_hardware_tetrode',
    '_inherit_hardware_microdrive_optetrode'
]


#  these are templates you want to add to each optogenetics session perfomed
#  with openephys
opto_openephys_templates = [
    '_inherit_hardware_openephys_optogenetics',
    '_inherit_hardware_pulse_pal',
    '_inherit_hardware_blue_laser',
    '_inherit_hardware_laser_measure_device',
    'mikkel_laser_settings',
    'mikkel_pulse_pal_settings',
    'mikkel_optogenetics_paradigm',
    'mikkel_optogenetics_anatomical_location'
]

#  these are templates you want to add to each optogenetics session perfomed
#  with axona
opto_axona_templates = [
    '_inherit_hardware_axona_optogenetics',
    '_inherit_hardware_pulse_pal',
    '_inherit_hardware_blue_laser',
    '_inherit_hardware_laser_measure_device',
    'mikkel_laser_settings',
    'mikkel_pulse_pal_settings',
    'mikkel_optogenetics_paradigm',
    'mikkel_optogenetics_anatomical_location'
]

#  thse are e.g. the brain areas you investigate, this ensures that you
#  register with with the same nomenclature for every recording
POSSIBLE_BRAIN_AREAS = ['MECR', 'MECL', 'MS']
POSSIBLE_LOCATIONS = ['room2', 'room1']

#  obligatory tags will be enforced uppon transfer, this is to ensure you
#  have a minimum of tags for each action
OBLIGATORY_TAGS = ['no', 'yes', 'maybe']
POSSIBLE_TAGS = ['GC', 'PC', 'BC', 'SC', 'HD', 'TC', 'theta'] + OBLIGATORY_TAGS

#  thse are the templates you want to load to each suregery implantation
#  procedure
surgery_implantation_templates = [
    'mikkel_implant_drive_L', 'mikkel_implant_drive_R',
    'mikkel_implant_fibre', 'mikkel_subject',
    'mikkel_anaesthesia', 'mikkel_analgesia',
    'mikkel_analgesia_post', 'mikkel_anaesthesia_local',
    '_inherit_mikkel_optic_fibre', '_inherit_mikkel_tetrode',
    '_inherit_mikkel_drive_optetrode',
    '_inherit_environment_rat_housing',
    '_inherit_environment_surgery_station'
]

# thse are the templates you want to load to each suregery injection procedure
surgery_injection_templates = [
    'mikkel_anaesthesia', 'mikkel_analgesia',
    'mikkel_analgesia_post', 'mikkel_anaesthesia_local',
    'mikkel_subject', 'mikkel_injection_1',
    'mikkel_injection_2',
    '_inherit_environment_rat_housing',
    '_inherit_mikkel_surgery_station_environment'
]

# this is how you represent each unit when you use expipe register-units
UNIT_INFO = {
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

# these are the analysis parameters you pass to exana
ANALYSIS_PARAMS = {
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

# this is personal user parameters
USER_PARAMS = {
    'project_id': 'mikkel_septum_entorhinal',
    'user_name': 'Mikkel Elle Lepperød',
    'location': 'room2',
    'laser_device': {'name': 'hardware_blue_laser', 'id': 4}
}

# this is a placeholder for all your templates
TEMPLATES = {
    'axona': axona_templates,
    'opto_axona': opto_axona_templates,
    'openephys': openephys_templates,
    'opto_openephys': opto_openephys_templates,
    'surgery_implantation': surgery_implantation_templates,
    'surgery_injection': surgery_injection_templates,
    'adjustment': 'mikkel_drive_depth_adjustment'
}
