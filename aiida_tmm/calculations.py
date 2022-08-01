from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import SinglefileData, StructureData, CifData
from aiida.plugins import DataFactory

from pymatgen.io.vasp import Incar
from pymatgen.io.vasp import Poscar
from pymatgen.io.vasp import Kpoints
from ase.io.vasp import write_vasp

class MyVaspCalculation(CalcJob):
    """AiiDA calculation plugin wrapping the vasp exacutable."""
    
    _VASP_OUTPUT = 'vasp_output'
    _RETRIEVE_LIST = ['CONTCAR', 'OUTCAR', 'vasprun.xml', 'EIGENVAL', 'DOSCAR', 'CHGCAR', _VASP_OUTPUT]
    _SCF_RETRIEVE_LIST = ['CHGCAR'] # just for testing

    @classmethod
    def define(cls, spec):
        """Define inputs and the outputs of the vasp calculation. """
        # yapf: disable
        super(MyVaspCalculation, cls).define(spec)

        # define inputs
        spec.input('parameters', valid_type=get_data_class('dict'), help='The VASP input parameters (INCAR).')
        spec.input('structure', valid_type=(get_data_class('structure'), get_data_class('cif')), help='The input structure (POSCAR).')
        spec.input('potential', valid_type=get_data_class('vasp_tmm.potcar'), help='The potentials (POTCAR).')
        spec.input('kpoints', valid_type=get_data_class('array.kpoints'), help='The kpoints to use (KPOINTS).')
        spec.input('charge_density', valid_type=get_data_class('vasp_tmm.chargedensity'), required=False, help='The charge density. (CHGCAR)')
        spec.input('settings', valid_type=get_data_class('dict'), required=False, help='Additional parameters not related to VASP itself.')
        spec.inputs['metadata']['options']['resources'].default = {
                'num_machine': 1,
                'num_mpiprocs_per_machine': 24,
                }
        spec.inputs['metadata']['options']['max_wallclock_seconds'].default = 1800
        spec.inputs['metadata']['options']['account'].default = 'p0020160'
        spec.inputs['metadata']['options']['max_memory_kb'].default = 43008000 # 1750*24*1024

        # spec.input('metadata.options.parser_name', default='vasp.vasp')

        # define outputs
        # spec.output('structure', valid_type=get_data_class('structure'), required=False, help='The output structure (CONTCAR).')
        spec.output('chgcar',
                    valid_type=get_data_class('vasp_tmm.chargedensity'),
                    required=False,
                    help='The output charge density CHGCAR file.')
        # #################################################
        # Complete outputs will be added later.
        # #################################################

    def write_incar(self, out_file):
        """
        Write the INCAR.
        Passes the parameter node (Dict) to pymatgen.io for parsing and write to out_files.
        :param outpu_file: absolute path of the object to write to
        """
        parameters = self.inputs.parameter.get_dict()
        incar_content = Incar.from_dict(parameters)
        incar_content.write_file(out_file)

    def write_poscar(self, out_file):
        """
        Write the POSCAR.
        Get the content of the structure node ('structure' or 'cif') and write to out_file.
        """
        structure_node = self.inputs.structure # can be 'structure' or 'cif'
        poscar_content = structure_node.get_ase()
        write_vasp(outfile, poscar_content)

    def write_kpoints(self, out_file):
        """
        Write the KPOINTS.
        Opt1: get the content of the kpoints node ('array.kpoints') and write to out_file.
        Opt2: get automatic kpoints by setting k grid density and reading POSCAR
        """
        structure = Poscar.from_file('POSCAR').structure
        k_density = self.inputs.kpoints[0] # only one number
        kpoints = Kpoints.automatic_density(structure, k_density)
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
        potential = self.input.potential.get_content() # define in PotcarData class
        with out_file.open('wb') as out:
            out.write(potential)

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

        remote_copy_list = []

        self.write_incar(incar)
        self.write_poscar(structure)
        self.write_potcar(potentials)
        self.write_kpoints(kpoints)
        
        codeinfo = datastructures.CodeInfo()
        codeinfo.uuid = self.inputs.code.uuid
        codeinfo.code_pk = self.inputs.code.pk
        
        calcinfo = datastructures.CalcInfo()
        calcinfo.uuid = self.uuid
        calcinfo.retrieve_list = self._SCF_RETRIEVE_LIST # retrieve only CHGCR for testing
        calcinfo.codes_info = [codeinfo]
        # Combine stdout and stderr into vasp_output.
        calcinfo.codes_info[0].stdout_name = self._VASP_OUTPUT
        calainfo.codes_info[0].join_files = True
        calcinfo.remote_copy_list = remote_copylist
        calcinfo.local_copy_list = [] # These two lists are empty since input files already written in the folder

        return calcinfo

