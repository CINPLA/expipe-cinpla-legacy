from collections import Mapping
from copy import deepcopy
import imp
import expipe
import os.path as op
import yaml


def deep_update(d, other):
    for k, v in other.items():
        d_v = d.get(k)
        if isinstance(v, Mapping) and isinstance(d_v, Mapping):
            deep_update(d_v, v)
        else:
            d[k] = deepcopy(v)


def load_python_module(module_path):
    directory, modname = op.split(module_path)
    modname, _ = op.splitext(modname)
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
    settings_file = op.join(expipe.config.config_dir, 'cinpla_config.yaml')
    assert op.exists(settings_file)
    with open(settings_file, "r") as f:
        settings = yaml.load(f)
    return settings


def give_empty_attrs(obj, *attrs):
    for attr in attrs:
        if not hasattr(obj, attr):
            setattr(obj, attr, [])


def load_parameters():
    settings = load_settings()
    PAR = load_python_module(settings['current']['parameters_path'])
    give_empty_attrs(PAR,
                     'POSSIBLE_TAGS',
                     'POSSIBLE_LOCATIONS',
                     'POSSIBLE_OPTO_TAGS',
                     'POSSIBLE_BRAIN_AREAS',
                     'POSSIBLE_LOCATIONS')
    return PAR
