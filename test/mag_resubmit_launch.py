""" Restart calculation of magnetization """

import numpy as np
import os
import pandas as pd

from aiida.orm import Code, Computer
from aiida.plugins import DataFactory, CalculationFactory
from aiida.engine import submit
from aiida.manage.configuration import load_profile
from aiida.common.extendeddicts import AttributeDict
from aiida_tmm.utils import PotcarIo

load_profile()

#mag_data = pd.read_csv('magmom_new.csv')
#cif_list = mag_data['cif']
#magmom_list = mag_data['magmom']

group_resubmit = load_group('mag_not_done')
for n in group_resubmit.nodes:
    # adjust MAGMOM for INCAR file
    #incar_dict = n.inputs.parameters.get_dict()
    #idx = np.where(cif_list == n.label)[0]
    #if len(idx) == 1:
    #    cif = cif_list[idx].values[0]
    #    incar_dict['MAGMOM'] = list(magmom_list[idx].values)[0]
    #    incar_dict['NELM'] = 200
    #    incar = Dict(dict=incar_dict)
    #    incar.store()
    if n.exit_status == 500:
        cif = n.label
        #store the other input nodes
        structure = n.inputs.structure.clone()
        structure.store()
        potcar = n.inputs.potential.clone()
        potcar.store()
        kpoints = n.inputs.kpoints.clone()
        kpoints.store()
        # set MAGMOM for INCAR
        n_atoms = structure.get_ase().get_global_number_of_atoms()
        incar_dict = n.inputs.parameters.get_dict()
        incar_dict['MAGMOM'] = '5.0*%s' %n_atoms
        incar = Dict(incar_dict)
        incar.store()

        #######################################################
        # Prepare the calculation
        #######################################################
        inputs = AttributeDict()
        inputs.code = n.inputs.code.clone()
        inputs.parameters = incar
        inputs.structure = structure
        inputs.potential = potcar
        inputs.kpoints = kpoints
        inputs.metadata = {
            'label': cif,
            'options': {
                'parser_name': 'vasp_tmm.mag',
                'max_wallclock_seconds': 86400
            }
        }

        CalcFactory = CalculationFactory('vasp_tmm.vasp')
        calc = submit(CalcFactory, **inputs)
        group = load_group('mag_500_resubmit')
        group.add_nodes(calc)
        #group = load_group('mag_not_done')
        #group.remove_nodes(n)
