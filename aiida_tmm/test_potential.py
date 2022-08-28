from pymatgen.ext.matproj import MPRester
from aiida_tmm.utils import PotcarIo
from aiida.plugins import DataFactory

path = '/home/bz43nogu/PBE54/'

with MPRester('Kthv8UMOBNI07gXx') as m:
    structure = m.get_structure_by_material_id('mp-30641')

StructureData = DataFactory('structure')
structure = StructureData(pymatgen=structure)
p = PotcarIo(structure, path)
pot_list = p.get_pot_list()
print(pot_list)
