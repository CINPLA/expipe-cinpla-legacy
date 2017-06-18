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
