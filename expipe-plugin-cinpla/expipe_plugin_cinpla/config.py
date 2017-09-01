from .imports import *


settings_file_path = os.path.join(os.path.expanduser('~'), '.config', 'expipe',
                             'cinpla_config.yaml')
if not os.path.exists(settings_file_path):
    warnings.warn('No config file found, import errors will occur, please ' +
                  'use "expipe env set <project-id> --params ' +
                  '<path-to-params-file>" (ommit <>)')


def deep_update(d, other):
    for k, v in other.items():
        d_v = d.get(k)
        if (isinstance(v, collections.Mapping) and
            isinstance(d_v, collections.Mapping)):
            deep_update(d_v, v)
        else:
            d[k] = copy.deepcopy(v)


def validate_depth(ctx, param, depth):
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


def load_python_module(module_path):
    if not os.path.exists(module_path):
        raise FileExistsError('Path "' + module_path + '" does not exist.')
    directory, modname = os.path.split(module_path)
    modname, _ = os.path.splitext(modname)
    file, path, descr = imp.find_module(modname, [directory])
    if file:
        try:
            mod = imp.load_module(modname, file, path, descr)  # noqa
        except Exception as e:  # pragma: no cover
            raise e
        finally:
            file.close()
    return mod


def load_settings():
    assert os.path.exists(settings_file_path)
    with open(settings_file_path, "r") as f:
        settings = yaml.load(f)
    return settings


def give_attrs_val(obj, value, *attrs):
    for attr in attrs:
        if not hasattr(obj, attr):
            setattr(obj, attr, value)


def load_parameters():
    try:
        settings = load_settings()
        PAR = load_python_module(settings['current']['params'])
    except AssertionError:
        class Dummy:
            pass
        PAR = Dummy
    except FileExistsError:
        warnings.warn('Unable to load parameters file "' +
                      settings['current']['params'] + '".')
        class Dummy:
            pass
        PAR = Dummy
    give_attrs_val(PAR, list(),
                 'POSSIBLE_TAGS',
                 'POSSIBLE_LOCATIONS',
                 'POSSIBLE_OPTO_TAGS',
                 'POSSIBLE_BRAIN_AREAS',
                 'POSSIBLE_LOCATIONS',
                 'POSSIBLE_CELL_LINES')
    give_attrs_val(PAR, dict(),
                     'UNIT_INFO',
                     'TEMPLATES')
    return PAR
