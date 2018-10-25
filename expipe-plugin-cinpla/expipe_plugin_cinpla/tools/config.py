from expipe_plugin_cinpla.imports import *


def deep_update(d, other):
    for k, v in other.items():
        d_v = d.get(k)
        if (isinstance(v, collections.Mapping) and
            isinstance(d_v, collections.Mapping)):
            deep_update(d_v, v)
        else:
            d[k] = copy.deepcopy(v)


def validate_cluster_group(ctx, param, cluster_group):
    try:
        tmp = []
        for cl in cluster_group:
            group, cluster, sorting = cl.split(' ', 3)
            tmp.append((int(group), int(cluster), sorting))
        out = {cl[0]: dict() for cl in tmp}
        for cl in tmp:
            out[cl[0]].update({cl[1]: cl[2]})
        return out
    except ValueError:
        raise click.BadParameter(
            'cluster-group needs to be contained in "" and ' +
            'separated with white space i.e ' +
            '<channel_group cluster_id good|noise|unsorted> (ommit <>).')


def validate_depth(ctx, param, depth):
    if depth == 'find':
        return depth
    try:
        out = []
        for pos in depth:
            key, num, z, unit = pos.split(' ', 4)
            out.append((key, int(num), float(z), unit))
        return tuple(out)
    except ValueError:
        raise click.BadParameter('Depth need to be contained in "" and ' +
                                 'separated with white space i.e ' +
                                 '<"key num depth physical_unit"> (ommit <>).')


def validate_position(ctx, param, position):
    try:
        out = []
        for pos in position:
            key, num, x, y, z, unit = pos.split(' ', 6)
            out.append((key, int(num), float(x), float(y), float(z), unit))
        return tuple(out)
    except ValueError:
        raise click.BadParameter('Position need to be contained in "" and ' +
                                 'separated with white space i.e ' +
                                 '<"key num x y z physical_unit"> (ommit <>).')

def validate_angle(ctx, param, position):
    try:
        out = []
        for pos in position:
            key, angle, unit = pos.split(' ', 3)
            out.append((key, float(angle), unit))
        return tuple(out)
    except ValueError:
        raise click.BadParameter('Angle need to be contained in "" and ' +
                                 'separated with white space i.e ' +
                                 '<"key angle physical_unit"> (ommit <>).')

def validate_adjustment(ctx, param, position):
    try:
        out = []
        for pos in position:
            key, num, z, unit = pos.split(' ', 4)
            out.append((key, int(num), float(z), unit))
        return tuple(out)
    except ValueError:
        raise click.BadParameter('Position need to be contained in "" and ' +
                                 'separated with white space i.e ' +
                                 '<"key num z physical_unit"> (ommit <>).')


def optional_choice(ctx, param, value):
    options = param.envvar
    assert isinstance(options, list)
    if value is None:
        if param.required:
            raise ValueError('Missing option "{}"'.format(param.opts))
        return value
    if param.multiple:
        if len(value) == 0:
            if param.required:
                raise ValueError('Missing option "{}"'.format(param.opts))
            return value
    if len(options) == 0:
        return value
    else:
        if isinstance(value, (str, int, float)):
            value = [value,]
        for val in value:
            if not val in options:
                raise ValueError(
                    'Value "{}" not in "{}".'.format(val, options))
            else:
                if param.multiple:
                    return value
                else:
                    return value[0]


def give_attrs_val(obj, value, *attrs):
    for attr in attrs:
        if not hasattr(obj, attr):
            setattr(obj, attr, value)


def set_empty_if_no_value(PAR=None):
    if PAR is None:
        class Parameters:
            pass
        PAR = Parameters()
    give_attrs_val(
        PAR, list(),
        'POSSIBLE_TAGS',
        'POSSIBLE_LOCATIONS',
        'POSSIBLE_CELL_LINES')
    give_attrs_val(
        PAR, dict(),
        'TEMPLATES')
    return PAR


def load_parameters():
    from expipecli.main import load_config
    config = load_config()
    if (config['local_root'], config['user_root']) == (None, None):
        warnings.warn('Unable to find "project-id", some commands will fail.')
        PAR = set_empty_if_no_value(None)
        PAR.PROJECT_ID, PAR.USERNAME = None, None
        return PAR
    project_id = config['local']['project_id']
    PAR = set_empty_if_no_value()
    PAR.PROJECT_ID = project_id
    PAR.USERNAME = config['user'].get('username')
    PAR.LOCATION = config['user'].get('location')
    return PAR
