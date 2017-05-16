# -*- coding: utf-8 -*-

"""Plugin system.

Code from http://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures  # noqa

"""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import imp
import os
import os.path as op
import glob
from six import with_metaclass
import subprocess
import platform

from .misc import _fullname



#------------------------------------------------------------------------------
# IPlugin interface
#------------------------------------------------------------------------------


class IPluginRegistry(type):
    plugins = []

    def __init__(cls, name, bases, attrs):
        if name != 'IPlugin':
            # print("Register plugin `%s`." % _fullname(cls))
            if _fullname(cls) not in (_fullname(_)
                                      for _ in IPluginRegistry.plugins):
                IPluginRegistry.plugins.append(cls)


class IPlugin(with_metaclass(IPluginRegistry)):
    """A class deriving from IPlugin can implement the following methods:

    * `attach_to_cli(cli)`: called when the CLI is created.

    """
    pass


def get_plugin(name):
    """Get a plugin class from its name."""
    for plugin in IPluginRegistry.plugins:
        if name in plugin.__name__:
            return plugin
    raise ValueError("The plugin %s cannot be found." % name)


#------------------------------------------------------------------------------
# Plugins discovery
#------------------------------------------------------------------------------

def discover_plugins():
    paths = os.environ['PATH'].split(os.pathsep)
    exs = []
    if platform.system() == "Windows":
        ext = '.exe'
    else:
        ext = ''
    for path in paths:
        exs.extend(glob.glob(op.join(path, 'plugin-expipe*' + ext)))
    if len(exs) == 0:
        return IPluginRegistry.plugins
    # TODO reveal plugin module in a non ugly way
    for executable in exs:
        process = subprocess.check_output(executable, shell=True)
        text = str(process)
        if text.startswith("b'"):
            text = text[2:]
        for output in text.split('\\n'):
            output = output.strip('\\r')
            if output.endswith('.py') and op.exists(output):
                directory, modname = op.split(output)
                modname, _ = op.splitext(modname)
                file, path, descr = imp.find_module(modname, [directory])
                if file:
                    # Loading the module registers the plugin in
                    # IPluginRegistry.
                    try:
                        mod = imp.load_module(modname, file, path, descr)  # noqa
                    except Exception as e:  # pragma: no cover
                        raise e
                    finally:
                        file.close()
    return IPluginRegistry.plugins
