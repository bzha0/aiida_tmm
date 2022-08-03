""" Launch an scf calculation using 'vasp_tmm' plugin """
import numpy as np

from aiida.orm import Code, Computer
from aiida.plugins import DataFactory 
from aiida.engine import submit
from aiida_tmm.utils import PotcarIo

# Set POSCAR file
StructureData = DataFactory('structure')
a = 3.092
c = 5.073
lattice = [[a, 0, 0],
            [-a / 2, a / 2 * np.sqrt(3), 0],
            [0, 0, c]]
structure = StructureData(cell=lattice)
for pos_direct, symbol in zip(
            ([1. / 3, 2. / 3, 0],
             [2. / 3, 1. / 3, 0.5],
             [1. / 3, 2. / 3, 0.375822],
             [2. / 3, 1. / 3, 0.875822]), ('Si', 'Si', 'C', 'C')):
    pos_cartesian = np.dot(pos_direct, lattice)
    structure.append_atom(position=pos_cartesian, symbols=symbol)
structure.store()

# Set POTCAR file
path = '/home/bz43nogu/PBE54/'
p = PotcarIo(structure, path)
potcar_content = p.get_potcar_obj()
PotcarData = DataFactory('vasp_tmm.potcar')
potcar = PotcarData(potcar_content) # write as a node in 'potcar' data class
potcar.store()

# Set INCAR file
Dict = DataFactory('dict')
incar_dict = {
        'SYSTEM': 'test',
        'PREC': 'Accurate',
        'IBRION': -1,
        'EDIFF': 1E-8,
        'NELMIN': 5,
        'NELM': 100,
        'ENCUT': 500,
        'IALGO': 38,
        'ISMEAR': 0,
        'SIGMA': 0.01,
        'GGA': 'PS',
        'LREAL': False,
        'LCHARG': False,
        'LWAVE': False,
        }
incar = Dict(dict=incar_dict)
incar.store()

# Set KPOINTS file, k density = 2.5 1/AA^-3
KpointsData = DataFactory('array.kpoints')
kpoints = KpointsData()
kpoints.set_array('kpoints', np.array([2.5]))
kpoints.store()

#######################################################
# Prepare the calculation
#######################################################
code_string = 'vasp_tmm@localhost'
code = Code.get_from_string(code_string)
builder = code.get_builder()
builder.parameters = incar
builder.structure = structure
builder.potential = potcar
builder.kpoints = kpoints
#builder.metadata.options.custom_scheduler_commands = '#SBATCH --mem-per-cpu=3800' # 3800 MB per node

calc = submit(builder)
