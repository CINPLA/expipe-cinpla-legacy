from .main import CinplaPlugin
from .axona import AxonaPlugin
from .openephys import OpenEphysPlugin
from .intan import IntanPlugin
# from .intan import IntanPlugin
from .optogenetics import OptoPlugin
from.electrical_stimulation import ElectricalStimulationPlugin
from .make_spatiality_overview import make_spatiality_overview
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
