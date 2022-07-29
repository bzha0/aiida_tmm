"""
Define all the new data type
"""

import os

from pathlib import Path
from pymatgen.io.vasp import PotcarSingle
from ase.io.vasp import read_vasp
from aiida.orm import Data, SinglefileData
from aiida_vasp.utils.aiida_utils import get_data_node

class PotcarData(SinglefileData):
    """
    Store POTCAR as a node in the repository.
    Use PotcarData(PotcarIo()) to call this class. 
    PotcarIo reads structure object and writes POTCAR object. 
    """
    pass

class ChgcarData(SinglefileData):
    """
    Store CHGCAR as a node in the repository.
    """
    pass

class WavecarData(SinglefileData):
    """
    Store WAVECAR as a node in the repository.
    """
    pass
