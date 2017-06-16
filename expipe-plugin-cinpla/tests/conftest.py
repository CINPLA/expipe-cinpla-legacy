import pytest
import expipe
import sys
import os.path as op
expipe.ensure_testing()

sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    raise IOError('No "expipe_params.py" found.')
from expipe_params import (user_params, templates, unit_info, possible_tags,
                           possible_locations, obligatory_tags)

# TODO ADD ALL TEMPLATES

PROJECT_ID = user_params['project_id']
ACTION_ID = 'action-plugin-test'
MODULE_ID = 'module-plugin-test'
RAT_ID = 'test-rat'


def pytest_namespace():
    return {"PROJECT_ID": PROJECT_ID,
            "ACTION_ID": ACTION_ID,
            "MODULE_ID": MODULE_ID,
            "RAT_ID": RAT_ID,
            "USER_PAR": user_params,
            "POSSIBLE_TAGS": possible_tags,
            "OBLIGATORY_TAGS": obligatory_tags}


@pytest.fixture(scope='function')
def setup_project_action():
    try:
        expipe.delete_project(PROJECT_ID, remove_all_childs=True)
    except NameError:
        pass
    project = expipe.require_project(PROJECT_ID)
    action = project.require_action(ACTION_ID)
    yield project, action
