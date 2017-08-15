# -*- coding: utf-8 -*-

"""Plugin system.

Code from http://eli.thegreenplace.net/2012/08/07/fundamental-concepts-of-plugin-infrastructures  # noqa

"""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import imp
import os
from pkg_resources import load_entry_point
from six import with_metaclass
import platform
import sys

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
    import subprocess
    path = os.path.dirname(sys.executable)
    if platform.system() == "Windows":
        ext = '.exe'
    else:
        ext = ''
    executables = [exe + ext for exe in os.listdir(path)
                   if exe.startswith('plugin-expipe')]
    if len(executables) == 0:
        return IPluginRegistry.plugins
    # TODO reveal plugin module in a non ugly way
    for executable in executables:
        module = imp.load_source(executable, os.path.join(path, executable))
        load_entry_point(module.__requires__, 'console_scripts', executable)()
    return IPluginRegistry.plugins
