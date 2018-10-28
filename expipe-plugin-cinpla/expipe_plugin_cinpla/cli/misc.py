from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.tools.action import (
    generate_templates, query_yes_no)
from expipe_plugin_cinpla.tools import config


def attach_to_cli(cli):
    @cli.command('annotate', short_help='Parse info about recorded units')
    @click.argument('action-id', type=click.STRING)
    @click.option('-t', '--tag',
                    multiple=True,
                    type=click.STRING,
                    callback=config.optional_choice,
                    envvar=PAR.POSSIBLE_TAGS,
                    help='Add tags to action.',
                    )
    @click.option('--message', '-m',
                  multiple=True,
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the annotation.',
                  )
    def annotate(action_id, tag, message, user):
        project = expipe.get_project(PAR.PROJECT_ROOT)
        action = project.actions[action_id]
        user = user or PAR.USERNAME
        if user is None:
            raise ValueError('Please add user name')
        users = list(set(action.users))
        if user not in users:
            users.append(user)
        action.users = users
        for m in message:
            action.create_message(text=m, user=user, datetime=datetime.now())
        action.tags.extend(tag)

    @cli.command('spikesort', short_help='Spikesort with klustakwik.')
    @click.argument('action-id', type=click.STRING)
    @click.option('--no-local',
                  is_flag=True,
                  help='Store temporary on local drive.',
                  )
    def spikesort(action_id, no_local):
        # anoying!!!!
        import logging
        from phycontrib.neo.model import NeoModel
        logger = logging.getLogger('phy')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)

        project = expipe.get_project(PAR.PROJECT_ROOT)
        action = project.require_action(action_id)
        exdir_path = PAR.PROJECT_ROOT / action.data[0]
        print('Spikesorting ', exdir_path)
        model = NeoModel(exdir_path)
        channel_groups = model.channel_groups
        for channel_group in channel_groups:
            if not channel_group == model.channel_group:
                model.load_data(channel_group)
            print('Sorting channel group {}'.format(channel_group))
            clusters = model.cluster(np.arange(model.n_spikes), model.channel_ids)
            model.save(spike_clusters=clusters)
