import expipe
import subprocess
import quantities as pq
import os
import os.path as op
from expipe_plugin_cinpla.main import CinplaPlugin
import sys
import logging
import shlex
import logging
sys.path.append(expipe.config.config_dir)
if not op.exists(op.join(expipe.config.config_dir, 'expipe_params.py')):
    print('No config params file found, use "expipe' +
          'copy-to-config expipe_params.py"')
else:
    from expipe_params import (USER_PARAMS, TEMPLATES, UNIT_INFO, POSSIBLE_TAGS,
                               POSSIBLE_LOCATIONS, OBLIGATORY_TAGS, MODULES,
                               ANALYSIS_PARAMS)

LOG_FILENAME = '/tmp/exception.log'
if op.exists(LOG_FILENAME):
    os.remove(LOG_FILENAME)

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(LOG_FILENAME)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)



def run_shell_command(command_line):
    if isinstance(command_line, str):
        command_line_args = shlex.split(command_line)
    elif isinstance(command_line, list):
        command_line_args = command_line
        command_line = ' '.join(command_line)
    else:
        raise TypeError('str or list')

    logging.info('Subprocess: "' + command_line + '"')

    try:
        command_line_process = subprocess.Popen(
            command_line_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    except (OSError, CalledProcessError) as exception:
        logger.info('Exception occured: ' + str(exception))
        logger.info('Subprocess failed')
        return False
    else:
        # no exception was raised
        logger.info('Subprocess finished')

    return True

project = expipe.get_project(USER_PARAMS['project_id'])
for action in project.actions:
    if action.type != 'Recording':
        continue
    # if 'no' in action.tags:
    #     continue
    print('Evaluating ', action.id)
    run_shell_command(['expipe', 'analyse', action.id, '-a',
                             'spatial', '--skip'])
