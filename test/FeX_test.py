""" Launch a dos workchain using 'vasp_tmm' plugin """
import numpy as np
import pandas as pd
from pymatgen.ext.matproj import MPRester

from aiida.orm import Code, Computer
from aiida.plugins import DataFactory, WorkflowFactory 
from aiida.engine import submit
from aiida.manage.configuration import load_profile
from aiida.common.extendeddicts import AttributeDict
from aiida_tmm.utils import PotcarIo

load_profile()

data = pd.read_csv('mpid_full.csv')

for mpid in data['mpid'][0:100]:
    # Set POSCAR file
    StructureData = DataFactory('structure')
    with MPRester('Kthv8UMOBNI07gXx') as m:
        structure = m.get_structure_by_material_id(mpid)
    structure = StructureData(pymatgen=structure)
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
        'System': 'Fex',
        'LWAVE': False,
        'LCHARG': True,
        'LVTOT': False,
        'EDIFF': 1e-06,
        'EDIFFG': -0.001,
        'ENCUT': 500,
        'NELM': 300,
        'IBRION': -1,
        'PREC': 'Accurate',
        'ISTART': 0,
        'ISMEAR': 1,
        'SIGMA': 0.1,
        'AMIX': 0.1,
        'BMIX': 0.01,
        'AMIX_MAG': 0.2,
        'BMIZ_MAG': 0.02,
        'ALGO': 'Normal',
        'LREAL': 'Auto' 
         }
    incar_scf = Dict_scf(dict=incar_dict)
    incar_scf.store()

    # Set KPOINTS file for scf 
    KpointsData = DataFactory('array.kpoints')
    kpoints = KpointsData()
    kpoints.set_array('kpoints', np.array([50.0, 50.0, 50.0]))
    kpoints.store()

    # Set INCAR file for dos
    Dict_scf = DataFactory('dict')
    incar_dict = {
        'System': 'Fex',
        'LWAVE': False,
        'LCHARG': True,
        'LVTOT': False,
        'EDIFF': 1e-06,
        'EDIFFG': -0.001,
        'ENCUT': 500,
        'NELM': 300,
        'IBRION': -1,
        'PREC': 'Accurate',
        'ISTART': 0,
        'ISMEAR': -5,
        'SIGMA': 0.1,
        'ALGO': 'Normal',
        'ICHARG': 11,
        'NEDOS': 512,
        'LREAL': 'Auto'
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
    group = load_group('dos_calc')
    group.add_nodes(calc)

#while True:
#    if calc.is_terminated:
#        break

# group the worchain node based on the exit code
#if calc.exit_status == 0:
#    group = load_group('dos_done')
#    group.add_nodes(calc)
#elif calc.exit_status == 400:
#    group = load_group('scf_not_converged')
#    group.add_nodes(calc)
#elif calc.exit_status == 401:
#    group = load_group('scf_with_error')
#    group.add_nodes(calc)
#else:
#    group = load_group('dos_unfinished')
#    group.add_nodes(calc)
