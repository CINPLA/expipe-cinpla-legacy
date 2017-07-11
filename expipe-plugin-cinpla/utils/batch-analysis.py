import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq
import os
import os.path as op
from expipe_plugin_cinpla.main import CinplaPlugin
import sys
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


@click.group()
@click.pass_context
def cli(ctx):
    pass


CinplaPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    result = CliRunner().invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception
    return result


if __name__ == '__main__':
    project = expipe.get_project(USER_PARAMS['project_id'])
    for action in project.actions:
        if action.type != 'Recording':
            continue
        print('Evaluating ', action.id)
        try:
            run_command(['analyse', action.id, '-a', 'all', '--skip'])
        except PermissionError:
            print('Permission error on ', action.id,
                  'exception logged in "' + LOG_FILENAME + '"')
            logger.exception('ACTION-ID: "' + action.id + '"')
        except FileNotFoundError:
            print('File not found on ', action.id,
                  'exception logged in "' + LOG_FILENAME + '"')
            logger.exception('ACTION-ID: "' + action.id + '"')
        except Exception as e:
            print('Got exception, logged in "' + LOG_FILENAME + '"')
            logger.exception('ACTION-ID: "' + action.id + '"')
