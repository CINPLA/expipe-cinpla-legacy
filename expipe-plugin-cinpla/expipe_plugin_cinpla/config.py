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
        if isinstance(v, collections.Mapping) and isinstance(d_v, collections.Mapping):
            deep_update(d_v, v)
        else:
            d[k] = copy.deepcopy(v)


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


def give_empty_attrs(obj, *attrs):
    for attr in attrs:
        if not hasattr(obj, attr):
            setattr(obj, attr, [])


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
    give_empty_attrs(PAR,
                     'POSSIBLE_TAGS',
                     'POSSIBLE_LOCATIONS',
                     'POSSIBLE_OPTO_TAGS',
                     'POSSIBLE_BRAIN_AREAS',
                     'POSSIBLE_LOCATIONS',
                     'POSSIBLE_CELL_LINES')
    return PAR
