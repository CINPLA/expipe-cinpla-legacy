import quantities as pq
from datetime import timedelta, datetime
import expipe
import os.path as op
from distutils.util import strtobool
import sys
import os
from ._version import get_versions

sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import USER_PARAMS, MODULES

DTIME_FORMAT = expipe.io.core.datetime_format

GIT_NOTE = {
    'registered': datetime.strftime(datetime.now(), DTIME_FORMAT),
    'note': 'Registered with the expipe cinpla plugin',
    'expipe-plugin-cinpla-version': get_versions()['version'],
    'expipe-version': expipe.__version__
}

nwb_main_groups = ['acquisition', 'analysis', 'processing', 'epochs',
                   'general']


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [[Y]/n] "
    elif default == "no":
        prompt = " [y/[N]] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def deltadate(adjustdate, regdate):
    delta = regdate - adjustdate if regdate > adjustdate else timedelta.max
    return delta


def register_depth(project, action, anatomy=None):
    regdate = action.datetime
    mod_info = MODULES['electrophysiology']
    if len(anatomy) == 0:
        assert len(action.subjects) == 1
        subject = action.subjects[0]
        try:
            adjustments = project.get_action(name=subject + '-adjustment')
        except NameError as e:
            raise NameError(
                str(e) + ', Cannot find current depth, anatomy must be given')
        adjusts = {}
        for adjust in adjustments.modules:
            values = adjust.to_dict()
            adjusts[datetime.strptime(values['date'], DTIME_FORMAT)] = adjust

        adjustdates = adjusts.keys()
        adjustdate = min(adjustdates, key=lambda x: deltadate(x, regdate))
        adjustment = adjusts[adjustdate].to_dict()
        curr_depth = {key: adjustment['depth'][key] for key in mod_info}
    else:
        curr_depth = {key: val * pq.mm for key, val in anatomy}
        adjustdate = None

    answer = query_yes_no(
        'Are the following values correct: ' +
        ', '.join('{} = {}'.format(key, val) for key, val in curr_depth.items()) +
        ' adjust date time = {}'.format(adjustdate))
    if answer is False:
        print('Aborting depth registration')
        return False
    modules_dict = action.modules.to_dict()
    for key, val in curr_depth.items():
        name = mod_info[key]
        if not name in modules_dict:
            raise NameError('Failed to acquire electrophysiology module')
        mod = modules_dict[name]
        print('Registering depth ', key, ' = ', val)
        mod['depth'] = val
        action.require_module(name=name, contents=mod, overwrite=True)
    return True


def _get_local_path(file_record, assert_exists=False, make=False):
    '''

    :param file_record:
    :return:
    '''
    import platform
    folder_name = 'expipe_temp_storage'
    local_path = file_record.local_path or op.join(os.path.expanduser('~'),
                                                   folder_name, path)
    if not op.exists(local_path) and not assert_exists and make:
        os.makedirs(local_path)
    elif not op.exists(local_path) and assert_exists:
        raise IOError('Path "' + local_path + '" does not exist.')
    return local_path


def generate_templates(action, action_templates, overwrite, git_note=None):
    '''

    :param action:
    :param action_templates:
    :param overwrite:
    :param git_note:
    :return:
    '''
    if git_note is not None:
        action.require_module(name='software_version_control_git',
                              contents=git_note, overwrite=overwrite)
    for template in action_templates:
        try:
            if template.startswith('_inherit'):
                name = '_'.join(template.split('_')[2:])
                contents = {'_inherits': '/project_modules/' +
                                         USER_PARAMS['project_id'] + '/' +
                                         name}
                action.require_module(name=name, contents=contents,
                                      overwrite=overwrite)
                print('Adding module ' + name)
            else:
                action.require_module(template=template,
                                      overwrite=overwrite)
                print('Adding module ' + template)
        except Exception as e:
            print(template)
            raise e


def _get_probe_file(system, nchan, spikesorter='klusta'):
    # TODO add naming convention for openeophys (oe) and intan (intan) - argument 'oe' or 'intan'
    fname = 'tetrodes' + str(nchan) + 'ch-' + spikesorter + '-' + system + '.prb'
    prb_path = op.join(expipe.config.config_dir, fname)
    if not op.exists(prb_path):
        prb_path = None
    return prb_path


def create_notebook(exdir_path, channel_group=0):
    import exdir
    import json
    exob = exdir.File(exdir_path)
    analysis_path = exob.require_group('analysis').directory
    currdir = op.dirname(op.abspath(__file__))
    fname = op.join(currdir, 'template_notebook.ipynb')
    with open(fname, 'r') as infile:
        notebook = json.load(infile)
    notebook['cells'][0]['source'] = ['exdir_path = r"{}"\n'.format(exdir_path),
                                      'channel_group = {}'.format(channel_group)]
    fnameout = op.join(analysis_path, 'analysis_notebook.ipynb')
    print('Generating notebook "' + fnameout + '"')
    with open(fnameout, 'w') as outfile:
            json.dump(notebook, outfile,
                      sort_keys=True, indent=4)
    return fnameout
