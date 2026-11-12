from . import version
from rich import traceback

from cordix.core import VariableLibrary

traceback.install(show_locals=VariableLibrary.get_variable("exceptions.show_locals"))

__version__ = version.__version__
