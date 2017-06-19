import pytest
import expipe
import sys
import os.path as op
expipe.ensure_testing()

sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    raise IOError('No "expipe_params.py" found.')
from expipe_params import (USER_PARAMS, TEMPLATES, UNIT_INFO, POSSIBLE_TAGS,
                           POSSIBLE_LOCATIONS, OBLIGATORY_TAGS)

# TODO ADD ALL TEMPLATES

PROJECT_ID = USER_PARAMS['project_id']
ACTION_ID = 'action-plugin-test'
MODULE_ID = 'module-plugin-test'
RAT_ID = 'test-rat'


def pytest_namespace():
    return {"PROJECT_ID": PROJECT_ID,
            "ACTION_ID": ACTION_ID,
            "MODULE_ID": MODULE_ID,
            "RAT_ID": RAT_ID,
            "USER_PAR": USER_PARAMS,
            "POSSIBLE_TAGS": POSSIBLE_TAGS,
            "OBLIGATORY_TAGS": OBLIGATORY_TAGS}


def run_command(command_list, inp=None):
    result = CliRunner().invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception
    return result


@pytest.fixture(scope='function')
def teardown_setup_project():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
    project = expipe.require_project(PROJECT_ID)
    for key, val in TEMPLATES.items():
        for template in val:
            if template.startswith('_inherit'):
                name = '_'.join(template.split('_')[2:])
                try:
                    project.require_module(name=name, contents={'test': 'cont'})
                except NameError:
                    pass
    action = project.require_action(ACTION_ID)
    yield project, action


@pytest.fixture(scope='module')
def teardown_setup_project_setup_surgery():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
    project = expipe.require_project(PROJECT_ID)
    for key, val in TEMPLATES.items():
        for template in val:
            if template.startswith('_inherit'):
                name = '_'.join(template.split('_')[2:])
                try:
                    project.require_module(name=name, contents={'test': 'cont'})
                except NameError:
                    pass

    from expipe_plugin_cinpla.main import CinplaPlugin
    CinplaPlugin().attach_to_cli(cli)


    # make surgery action
    run_command(['register-surgery', pytest.RAT_ID,
                 '--weight', '500',
                 '--birthday', '21.05.2017',
                 '--procedure', 'implantation',
                 '-d', '21.01.2017T14:40',
                 '-a', 'mecl', 1.9,
                 '-a', 'mecr', 1.8])

    # init adjusment
    run_command(['adjust', pytest.RAT_ID,
                 '-a', 'mecl', 50,
                 '-a', 'mecr', 50,
                 '-d', 'now',
                 '--init'], inp='y')
    yield project


@pytest.fixture
def setup_project_action():
    project = expipe.require_project(PROJECT_ID)
    for key, val in TEMPLATES.items():
        for template in val:
            if template.startswith('_inherit'):
                name = '_'.join(template.split('_')[2:])
                try:
                    project.require_module(name=name, contents={'test': 'cont'})
                except NameError:
                    pass
    project.delete_action(ACTION_ID)
    action = project.require_action(ACTION_ID)
    yield project, action
