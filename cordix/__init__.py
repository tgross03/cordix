from . import version
from rich import traceback

from cordix.core import GlobalVariables

traceback.install(show_locals=GlobalVariables.get_variable("exceptions.show_locals"))

__version__ = version.__version__
