"""
Find POTCAR files with corresponding elements from local POTCAR folder,
generate POTCAR for calculations
and save it as PotcarData
"""

import os

from pathlib import Path
from pymatgen.io.vasp import PotcarSingle
from ase.io.vasp import read_vasp
from aiida.orm import Data
from aiida_vasp.utils.aiida_utils import get_data_node

def get_structure():
    """Get structure from StructureData """
    structure = get_data_node('structure', ase=structure.get_ase())
    return structure

def get_symbols_from_strucutre(structure):
    """ Get species from strucutre.
    :param structure: an ase.Atom object 
    :return symbols: a list"""
    symbols = struc.get_ase().get_chemical_symbols()
    symbols = list(set(symbols))
    return symbols

def sym_pot_map(symbol):
    """ map symbol to the potential name """
    pots=['B','C','N','O','F']
    potsv=['K','Rb','Cs','Ca','Sr','Ba','Sc','Y','Zr','V']
    potpv=['Na','Nb','Ta','Ti' ]
    potd=['Ga','In','Tl','Ge','Sn','Pb','Bi']
    pot2=[]
    pot3=['Yb', 'Ce', 'Dy', 'Er', 'Eu', 'Gd', 'Ho', 'Lu', 'Nd', 'Pm', 'Pr', 'Sm', 'Tb', 'Tm']

    potarr=['pots','potsv','potpv','potd','pot2','pot3']

    for i in potarr:
        if symbol in eval(j):
            pot_name = symbol + '_' + j[3:]
        else:
            pot_name = symbol
    return pot_name

class PotcarIo():
    """ Will not be use for FeX binary compunds calculations. """

class MultiPotcarIo():
    """ Read potcars and store as vasp_tmm.potcar"""
   
   def __init__(self, potcars=None)

    
