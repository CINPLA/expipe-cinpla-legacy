from .imports import *
from ._version import get_versions
from .config import load_parameters

nwb_main_groups = ['acquisition', 'analysis', 'processing', 'epochs',
                   'general']


def get_git_info():
    DTIME_FORMAT = expipe.io.core.datetime_format

    GIT_NOTE = {
        'registered': datetime.strftime(datetime.now(), DTIME_FORMAT),
        'note': 'Registered with the expipe cinpla plugin',
        'expipe-plugin-cinpla-version': get_versions()['version'],
        'expipe-version': expipe.__version__
    }
    return GIT_NOTE


def query_yes_no(question, default="yes", answer=None):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    if answer is True:
        return True
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


def register_depth(project, action, depth=None, answer=False):
    DTIME_FORMAT = expipe.io.core.datetime_format
    regdate = action.datetime
    mod_info = PAR.MODULES['implantation']
    depth = depth or []
    if len(depth) == 0:
        assert len(action.subjects) == 1
        subject = action.subjects[0]
        try:
            adjustments = project.get_action(name=subject + '-adjustment')
        except NameError as e:
            raise NameError(
                str(e) + ', Cannot find current depth, depth must be given ' +
                'in adjustments with "expipe adjust subject-id --init".')
        adjusts = {}
        for adjust in adjustments.modules:
            values = adjust.to_dict()
            adjusts[datetime.strptime(values['date'], DTIME_FORMAT)] = adjust

        adjustdates = adjusts.keys()
        adjustdate = min(adjustdates, key=lambda x: deltadate(x, regdate))
        adjustment = adjusts[adjustdate].to_dict()
        curr_depth = {key: adjustment['depth'].get(key) for key in mod_info
                      if adjustment['depth'].get(key) is not None}
    else:
        curr_depth = {key: val * pq.mm for key, val in depth}
        adjustdate = None

    def last_num(x):
        return '%.3d' % int(x.split('_')[-1])
    correct = query_yes_no(
        'Are the following values correct: ' +
        ' adjust date time = {}\n'.format(adjustdate) +
        ''.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                for key, val in curr_depth.items()
                for pos_key in sorted(val, key=lambda x: last_num(x)))
        , answer=answer)
    if not correct:
        print('Aborting depth registration')
        return False
    if len(action.subjects) == 1:
        surgery_action_id = action.subjects[0] + '-surgery-implantation'
        try:
            surgery = project.get_action(surgery_action_id)
        except NameError as e:
            raise NameError(str(e) + 'There are no surgery-implantation ' +
                            'registered for this animal. Please insert depth' +
                            'manually')
    else:
        raise ValueError('Multiple subjects registered for this action, ' +
                         'unable to get surgery.')
    for key, name in mod_info.items():
        if key not in curr_depth: # module not used in surgery
            continue
        mod = surgery.get_module(name=name).to_dict()
        for pos_key, val in curr_depth[key].items():
            if np.isnan(val):
                raise ValueError('Depth cannot be NaN')
            print('Registering depth:', key, pos_key, '=', val)
            mod[pos_key][2] = val
        action.require_module(name=name, contents=mod, overwrite=True)
    return True


def _get_local_path(file_record, assert_exists=False, make=False):
    '''

    :param file_record:
    :return:
    '''
    folder_name = 'expipe_temp_storage'
    local_path = file_record.local_path or os.path.join(os.path.expanduser('~'),
                                                   folder_name, path)
    if not os.path.exists(local_path) and not assert_exists and make:
        os.makedirs(local_path)
    elif not os.path.exists(local_path) and assert_exists:
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
                try:
                    action.project.require_module(template=name)
                    print('Adding module to project ' + name)
                except (NameError, ValueError):
                    pass
                contents = {'_inherits': '/project_modules/' +
                                         action.project.id + '/' +
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
    prb_path = os.path.join(expipe.config.config_dir, fname)
    if not os.path.exists(prb_path):
        prb_path = None
    return prb_path


def create_notebook(exdir_path, channel_group=0):
    exob = exdir.File(exdir_path)
    analysis_path = str(exob.require_group('analysis').directory)
    currdir = os.path.dirname(os.path.abspath(__file__))
    fname = os.path.join(currdir, 'template_notebook.ipynb')
    with open(fname, 'r') as infile:
        notebook = json.load(infile)
    notebook['cells'][0]['source'] = ['exdir_path = r"{}"\n'.format(exdir_path),
                                      'channel_group = {}'.format(channel_group)]
    fnameout = os.path.join(analysis_path, 'analysis_notebook.ipynb')
    print('Generating notebook "' + fnameout + '"')
    with open(fnameout, 'w') as outfile:
            json.dump(notebook, outfile,
                      sort_keys=True, indent=4)
    return fnameout
