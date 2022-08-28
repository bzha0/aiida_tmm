""" Launch a dos workchain using 'vasp_tmm' plugin """
import numpy as np
from time import sleep

from aiida.orm import Code
from aiida.plugins import DataFactory
from aiida.engine import submit
from aiida.common.extendeddicts import AttributeDict
from aiida_tmm.utils import PotcarIo

def launch_scf(structure, potcar, code_string):
    """ launch an scf calculation """
    structure = structure
    potcar = potcar
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

    # set kpoints, k density = 11 1/AA^-3
    KpointsData = DataFactory('array.kpoints')
    kpoints = KpointsData()
    kpoints.set_array('kpoints', np.array([50.0]))

    code = Code.get_from_string(code_string)
    builder = code.get_builder()
    builder.structure = structure
    builder.parameters = incar_scf
    builder.potential = potcar
    builder.kpoints = kpoints
    builder.metadata.label = 'scf step'

    node = submit(builder)
    return node

def launch_dos(structure, potcar, code_string, charge_density):
    structure = structure
    potcar = potcar
    # Set INCAR file for scf
    Dict_dos = DataFactory('dict')
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
    incar_dos = Dict_dos(dict=incar_dict)

    # set kpoints, k density = 2.5 1/AA^-3
    KpointsData = DataFactory('array.kpoints')
    kpoints = KpointsData()
    kpoints.set_array('kpoints', np.array([80.0]))

    code = Code.get_from_string(code_string)
    builder = code.get_builder()
    builder.structure = structure
    builder.parameters = incar_dos
    builder.potential = potcar
    builder.kpoints = kpoints
    builder.charge_density = charge_density
    builder.metadata.options.parser_name = 'vasp_tmm.dos'
    builder.metadata.label = 'dos step'

    node = submit(builder)
    return node

def main(structure, potcar, code_string, sleep_seconds=60):
    node_scf = launch_scf(structure, potcar, code_string)

    while True:
        if node_scf.is_terminated:
            break
        print('Waiting for scf calculation to be done.')
        sleep(sleep_seconds)

    if node_scf.is_finished_ok:
        charge_density = node_scf.outputs.chgcar.clone()

        node_dos = launch_dos(structure, potcar, code_string, charge_density)
    else:
        print('Scf calculation failed, workflow stopped.')


# Set POSCAR file
StructureData = DataFactory('structure')
alat = 3.9
lattice = np.array([[.5, .5, 0], [0, .5, .5], [.5, 0, .5]]) * alat
structure = StructureData(cell=lattice)
positions = [[0.0, 0.0, 0.0]]
for pos_direct in positions:
    pos_cartesian = np.dot(pos_direct, lattice)
    structure.append_atom(position=pos_cartesian, symbols='Si')


# Set POTCAR file
path = '/home/bz43nogu/PBE54/'
p = PotcarIo(structure, path)
potcar_content = p.get_potcar_obj()
PotcarData = DataFactory('vasp_tmm.potcar')
potcar = PotcarData(potcar_content)
 
if __name__ == '__main__':
    code_string = 'vasp_tmm@localhost'
    
    main(structure, potcar, code_string)
