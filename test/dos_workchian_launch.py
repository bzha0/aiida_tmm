""" Launch a dos workchain using 'vasp_tmm' plugin """
import numpy as np

from aiida.orm import Code, Computer
from aiida.plugins import DataFactory, WorkflowFactory 
from aiida.engine import submit
from aiida.manage.configuration import load_profile
from aiida.common.extendeddicts import AttributeDict
from aiida_tmm.utils import PotcarIo

load_profile()

# Set POSCAR file
StructureData = DataFactory('structure')
alat = 3.9
lattice = np.array([[.5, .5, 0], [0, .5, .5], [.5, 0, .5]]) * alat
structure = StructureData(cell=lattice)
positions = [[0.0, 0.0, 0.0]]
for pos_direct in positions:
    pos_cartesian = np.dot(pos_direct, lattice)
    structure.append_atom(position=pos_cartesian, symbols='Si')
structure.store()

# Set POTCAR file
path = '/home/bz43nogu/PBE54/'
p = PotcarIo(structure, path)
potcar_content = p.get_potcar_obj()
PotcarData = DataFactory('vasp_tmm.potcar')
potcar = PotcarData(potcar_content) # write as a node in 'potcar' data class
potcar.store()

# Set INCAR file for scf
Dict_scf = DataFactory('dict')
incar_dict = {
        'SYSTEM': 'test',
        'PREC': 'Accurate',
        'NELMIN': 5,
        'NELM': 100,
        'ENCUT': 240,
        'IALGO': 38,
        'ISMEAR': 0,
        'SIGMA': 0.01,
        'GGA': 'PS',
        'LREAL': False,
        'LCHARG': True,
        'LWAVE': False,
        }
incar_scf = Dict_scf(dict=incar_dict)
incar_scf.store()

# Set KPOINTS file, k density = 2.5 1/AA^-3
KpointsData = DataFactory('array.kpoints')
kpoints = KpointsData()
kpoints.set_array('kpoints', np.array([50.0]))
kpoints.store()

# Set INCAR file for dos
Dict_scf = DataFactory('dict')
incar_dict = {
        'SYSTEM': 'test',
        'PREC': 'Accurate',
        'ENCUT': 240,
        'IALGO': 38,
        'ISMEAR': -5,
        'ICHARG': 11,
        'GGA': 'PS',
        'LREAL': False,
        'LCHARG': False,
        'LWAVE': False,
        }
incar_dos = Dict_scf(dict=incar_dict)
incar_dos.store()

#######################################################
# Prepare the calculation
#######################################################
#base = AttributeDict()
#base.structure = structure
#base.potential = potcar
#base.kpoints = kpoints

workchain = WorkflowFactory('vasp_tmm.dos')
#builder = workchain.get_builder()
code_string = 'vasp@localhost'
code = Code.get_from_string(code_string)
inputs = AttributeDict()
inputs.code = code
inputs.scf_incar = incar_scf
inputs.dos_incar = incar_dos
inputs.structure = structure
inputs.potential = potcar
inputs.kpoints = kpoints
#builder.base = base
#builder.metadata.options.custom_scheduler_commands = '#SBATCH --mem-per-cpu=3800' # 3800 MB per node

calc = submit(workchain, **inputs)
