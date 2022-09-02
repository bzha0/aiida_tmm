""" Launch a mag workchain using 'vasp_tmm' plugin """

import numpy as np

from aiida.orm import Code, Computer
from aiida.plugins import DataFactory, CalculationFactory
from aiida.engine import submit
from aiida.manage.configuration import load_profile
from aiida.common.extendeddicts import AttributeDict
from aiida_tmm.utils import PotcarIo

load_profile()

cif_path = '/Users/zhaobo/Documents/GitHub/Copy/775.cif'

# Set POSCAR file
CifData = DataFactory('cif')
structure = CifData(file=cif_path)
structure.store()

# Set POTCAR file
path = '/Users/zhaobo/Documents/PBE54/'
p = PotcarIo(structure, path)
potcar_content = p.get_potcar_obj()
PotcarData = DataFactory('vasp_tmm.potcar')
potcar = PotcarData(potcar_content) # write as a node in 'potcar' data class
potcar.store()

# Set INCAR file for mag-scf
# num of atoms is needed to specify MAGMOM
n_atoms = structure.get_ase().get_global_number_of_atoms()

Dict = DataFactory('dict')
incar_dict = {
    'ISPIN': 2,
    'MAGMON': '5.0*%s'%n_atoms,
    'LASPH': True,
    'GGA_COMPAT': False,
    'VOSKOWN': 1,
    'LMAXMIX': 4
}
incar = Dict(dict=incar_dict)
incar.store()

# Set KPOINTS file, k density 50/a 1/AA
KpointsData = DataFactory('array.kpoints')
kpoints = KpointsData()
kpoints.set_array('kpoints', np.array([50.0, 50.0, 50.0]))
kpoints.store()

#######################################################
# Prepare the calculation
#######################################################

code_string = 'vasp@mycluster'
code = Code.get_from_string(code_string)
inputs = AttributeDict()
inputs.code = code
inputs.parameters = incar
inputs.structure = structure
inputs.potential = potcar
inputs.kpoints = kpoints
inputs.metadata = {
    'label': '775',
    'options': {'parser_name': 'vasp_tmm.mag'}
}

CalcFactory = CalculationFactory('vasp_tmm.vasp')

calc = submit(CalcFactory, **inputs)
group = load_group('mag_calc')
group.add_nodes(calc)
