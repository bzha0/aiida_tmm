from pathlib import Path

from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import ArrayData, SinglefileData, StructureData, CifData, Dict, KpointsData, Float
from aiida.plugins import DataFactory
#from aiida_tmm.utils import PotcarIo 
from aiida_tmm.data import PotcarData, ChgcarData, WavecarData

from pymatgen.io.vasp import Incar
from pymatgen.io.vasp import Poscar
from pymatgen.io.vasp import Kpoints
from ase.io.vasp import write_vasp

class MyVaspCalculation(CalcJob):
    """AiiDA calculation plugin wrapping the vasp exacutable."""
    
    _VASP_OUTPUT = 'vasp_output'
    _RETRIEVE_LIST = ['CONTCAR', 'OUTCAR', 'vasprun.xml', 'EIGENVAL', 'DOSCAR', 'CHGCAR', _VASP_OUTPUT]
    _DOS_RETRIEVE_LIST = ['CHGCAR', 'DOSCAR'] # just for testing
    #_POT_PATH = '/home/bz43nogu/PBE54/'

    @classmethod
    def define(cls, spec):
        """Define inputs and the outputs of the vasp calculation. """
        # yapf: disable
        super(MyVaspCalculation, cls).define(spec)

        # define inputs
        spec.input('parameters', valid_type=Dict, help='The VASP input parameters (INCAR).')
        #spec.input_namespace('structure', valid_type=(StructureData, CifData), help='The input structure (POSCAR).', dynamic=True)
        spec.input('structure', valid_type=(StructureData, CifData), help='The input structure (POSCAR).')
        spec.input('potential', valid_type=PotcarData, help='The potentials (POTCAR).')
        spec.input('kpoints', valid_type=KpointsData, help='The kpoints to use (KPOINTS).')
        spec.input('charge_density', valid_type=(ChgcarData, SinglefileData), required=False, help='The charge density. (CHGCAR)')
        spec.input('settings', valid_type=Dict, required=False, help='Additional parameters not related to VASP itself.')
        spec.inputs['metadata']['options']['resources'].default = {
                'num_machines': 1,
                'num_mpiprocs_per_machine': 24,
                }
        spec.inputs['metadata']['options']['max_wallclock_seconds'].default = 1800
        spec.inputs['metadata']['options']['account'].default = 'p0020160'
        spec.inputs['metadata']['options']['custom_scheduler_commands'].default = '#SBATCH --mem-per-cpu=3800' # 3800 MB per node
        #spec.inputs['metadata']['options']['cmdline_parameters'].default = "srun"
        #spec.input('metadata.options.output_filename', valid_type=str)

        spec.input('metadata.options.parser_name', default='vasp_tmm.scf') # or vasp_tmm.dos

        # define outputs
        # spec.output('structure', valid_type=get_data_class('structure'), required=False, help='The output structure (CONTCAR).')
        spec.output('E_fermi', 
                valid_type=Float, 
                required=False, 
                help='The Fermi energy')
        spec.output('chgcar',
                    valid_type=(ChgcarData, SinglefileData),
                    required=False,
                    help='The output charge density CHGCAR file.')
        spec.output('dos', 
                valid_type=ArrayData, 
                required=False, 
                help='The outpu dos data.')
        # #################################################
        # Complete outputs will be added later.
        # #################################################

    def write_incar(self, out_file):
        """
        Write the INCAR.
        Passes the parameter node (Dict) to pymatgen.io for parsing and write to out_files.
        :param outpu_file: absolute path of the object to write to
        """
        parameters = self.inputs.parameters.get_dict()
        incar_content = Incar.from_dict(parameters)
        incar_content.write_file(out_file)

    def write_poscar(self, out_file):
        """
        Write the POSCAR.
        Get the content of the structure node ('structure' or 'cif') and write to out_file.
        """ 
        structure_node = self.inputs.structure # 'structure' or 'cif' type
        poscar_content = structure_node.get_ase()
        write_vasp(out_file, poscar_content)


    def write_kpoints(self, out_file, poscar_path):
        """
        Write the KPOINTS.
        Opt1: get the content of the kpoints node ('array.kpoints') and write to out_file.
        Opt2: get automatic kpoints by setting k grid density and reading POSCAR
        """
        poscar = poscar_path
        structure = Poscar.from_file(poscar).structure
        k_density = self.inputs.kpoints.get_array('kpoints')[0] # only one number
        kpoints = Kpoints.automatic_density(structure, k_density, force_gamma=True) # gamma-centered mesh
        # kpoints_node = self.inputs.kpoints # kpoints mesh
        # kpoints_content = kpoints_node 
        kpoints.write_file(out_file)

    def write_potcar(self, out_file):
        """
        Write the POTCAR.
        Get the content of the potential node (vasp_tmm.potcar) 
        (should already contain multi potcars with the right symbol oder)
        and write to out_file.
        :param outpu_file: absolute path of the object to write to
        """
        #pot_path = self._POT_PATH
        #potcar = PotcarIo(pot_path)
        potential = self.inputs.potential.get_content() # define in PotcarData class
        #potential = potential.encode('utf-8')
        path = Path(out_file)
        with path.open('w', encoding='utf-8') as out:
            out.write(potential)

    #def write_chgcar(self, out_file):
    #    """
    #    Write the CHGCAR for dos calculations.
    #    """
    #    charge_density = self.inputs.charge_density.get_content() # clone from outputs.chgcar of scf #calculations
    #    path = Path(out_file)
    #    with path.open('w', encoding='utf-8') as out:
    #        out.write(charge_density)
    

    def prepare_for_submission(self, folder):
        """
        Prepare the four VASP input files.
        Write the output files as listed in _RETRIEVE_LIST.
        :param folder: an `aiida.common.folders.Folder` where the plugin should temporarily place all foldes needed by the calculation.
        :return calcinfo: `aiida.common.datastructures.CalcInfo` instance
        """
        # Prepare input files
        incar = folder.get_abs_path('INCAR')
        structure = folder.get_abs_path('POSCAR')
        potentials = folder.get_abs_path('POTCAR')
        kpoints = folder.get_abs_path('KPOINTS')
        #chgcar = folder.get_abs_path('CHGCAR')

        remote_copy_list = []

        self.write_incar(incar)
        self.write_poscar(structure)
        self.write_potcar(potentials)
        self.write_kpoints(kpoints, structure)
        #self.write_chgcar(chgcar)
        
        codeinfo = datastructures.CodeInfo()
        codeinfo.withmpi = True
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.code_pk = self.inputs.code.pk
        
        calcinfo = datastructures.CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.retrieve_list = self._RETRIEVE_LIST
        calcinfo.codes_info = [codeinfo]
        calcinfo.codes_info[0].prepend_cmdline_params = ["srun", "-k"]
        # Combine stdout and stderr into vasp_output.
        calcinfo.codes_info[0].stdout_name = self._VASP_OUTPUT
        calcinfo.codes_info[0].join_files = True
        calcinfo.remote_copy_list = remote_copy_list
        calcinfo.local_copy_list = [] # These two lists are empty since input files already written in the folder
        self.write_additional(folder, calcinfo)

        return calcinfo

    def write_additional(self, folder, calcinfo):
        """ write CHGCAR if needed """
        if self._need_chgcar():
            charge_density = self.inputs.charge_density
            calcinfo.local_copy_list.append((charge_density.uuid, charge_density.filename, 'CHGCAR'))

    def _need_chgcar(self):
        """ get the `ICHARG` key in the self.input.parameters.
        If ICHARG = 1 or 11, return True"""
        parameters = self.inputs.parameters.get_dict()
        try:
            parameters['ICHARG']
            icharg = parameters['ICHARG']
            return bool(icharg in [1, 11])
        except:
            return False

