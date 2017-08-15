from expipecli.utils.misc import lazy_import
import sys

@lazy_import
def expipe():
    import expipe
    return expipe

@lazy_import
def Mapping():
    from collections import Mapping
    return Mapping

@lazy_import
def datetime():
    from datetime import datetime
    return datetime

@lazy_import
def os():
    import os
    return os

@lazy_import
def json():
    import json
    return json

@lazy_import
def yaml():
    import yaml
    return yaml

@lazy_import
def imp():
    import imp
    return imp

@lazy_import
def deepcopy():
    from copy import deepcopy
    return deepcopy


def deep_update(d, other):
    for k, v in other.items():
        d_v = d.get(k)
        if isinstance(v, Mapping) and isinstance(d_v, Mapping):
            deep_update(d_v, v)
        else:
            d[k] = deepcopy(v)


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
    settings_file = os.path.join(expipe.config.config_dir, 'cinpla_config.yaml')
    assert os.path.exists(settings_file)
    with open(settings_file, "r") as f:
        settings = yaml.load(f)
    return settings


def give_empty_attrs(obj, *attrs):
    for attr in attrs:
        if not hasattr(obj, attr):
            setattr(obj, attr, [])


def load_parameters():
    try:
        settings = load_settings()
        PAR = load_python_module(settings['current']['parameters_path'])
    except AssertionError:
        class Dummy:
            pass
        PAR = Dummy
    except FileExistsError:
        warnings.warn('Unable to load parameters file "' +
                      settings['current']['parameters_path'] + '".')
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
