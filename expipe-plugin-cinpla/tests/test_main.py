import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner

expipe.ensure_testing()


@click.group()
@click.pass_context
def cli(ctx):
    pass

from expipe_plugin_cinpla.main import CinplaPlugin
CinplaPlugin().attach_to_cli(cli)

def test_annotate(setup_project_action):
    project, action = setup_project_action
    runner = CliRunner()
    result = runner.invoke(cli, ['annotate', pytest.ACTION_ID,
                                 '--tag', pytest.POSSIBLE_TAGS[0],
                                 '-t', pytest.POSSIBLE_TAGS[1],
                                 '--message', 'first message',
                                 '-m', 'second message'])
    assert result.exit_code == 0, result.output
    assert action.tags[0] == pytest.POSSIBLE_TAGS[0]
    assert action.tags[1] == pytest.POSSIBLE_TAGS[1]
    assert action.messages.messages[0]['message'] == 'first message'
    assert action.messages.messages[1]['message'] == 'second message'
    assert action.messages.messages[0]['user'] == pytest.USER_PAR['user_name']

    result = runner.invoke(cli, ['annotate', pytest.ACTION_ID,
                                 '--user', 'test_user',
                                 '-m', 'third message'])
    assert result.exit_code == 0, result.output
    assert action.messages.messages[2]['message'] == 'third message'
    assert action.messages.messages[2]['user'] == 'test_user'


def test_reg_rat_init_depth_adjustment(setup_project_action):
    project, _ = setup_project_action
    runner = CliRunner()
    # make surgery action
    result = runner.invoke(cli, ['register-surgery', pytest.RAT_ID,
                                 '--weight', '500',
                                 '--birthday', '21.05.2017',
                                 '--procedure', 'implantation',
                                 '-d', '21.01.2017T14:40',
                                 '-l', 1.9,
                                 '-r', 1.8])
    assert result.exit_code == 0, result.output

    # init
    result = runner.invoke(cli, ['adjust', pytest.RAT_ID,
                                 '-l', '50',
                                 '-r', '50',
                                 '-d', 'now',
                                 '--init'])
    assert result.exit_code == 0, result.output

    # adjust more
    result = runner.invoke(cli, ['adjust', pytest.RAT_ID,
                                 '-l', '50',
                                 '-r', '50',
                                 '-d', 'now'])
    assert result.exit_code == 0, result.output
    action = project.require_action(pytest.RAT_ID + '-adjustment')
    l, r = 1.9, 1.8
    for adjustment in action.modules:
        ad = adjustment.to_dict()
        l += 0.05
        r += 0.05
        assert ad['depth']['left']['value'] == l
        assert ad['depth']['right']['value'] == r
