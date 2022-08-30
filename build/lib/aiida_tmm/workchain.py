import numpy as np

from aiida.engine import WorkChain, submit, append_
from aiida.engine.processes.exit_code import ExitCode
from aiida.orm import Code, ArrayData, Dict, StructureData, CifData, KpointsData, SinglefileData
from aiida.plugins import DataFactory, CalculationFactory, WorkflowFactory
from aiida.common.extendeddicts import AttributeDict
from aiida.common.exceptions import NotExistent
from aiida_tmm.data import PotcarData, ChgcarData

#@calcfunction
#def get_charge_density

class DosWorkChain(WorkChain):
    """ Density of states workchain """

    _vasp_process = CalculationFactory('vasp_tmm.vasp')

    @classmethod
    def define(cls, spec):
        super(DosWorkChain, cls).define(spec)
        spec.input('code', valid_type=Code)
        #spec.expose_inputs(cls._vasp_process, include=('structure', 'potential', 'kpoints', 'charge_density', 'metadata.options.parser_name'))
        #spec.expose_inputs(cls._vasp_process, exclude=['parameters'])#, namespace='base')
        spec.input('parameters', valid_type=Dict, required=False, help='The VASP input parameters (INCAR).')
        spec.input('scf_incar', valid_type=Dict, required=False, help='INCAR file for scf calculation.') 
        spec.input('dos_incar', valid_type=Dict, required=False, help='INCAR file for dos calculation.')
        spec.input('structure', valid_type=(StructureData, CifData), help='The input structure (POSCAR).')
        spec.input('potential', valid_type=PotcarData, help='The potentials (POTCAR).')
        spec.input('kpoints', valid_type=KpointsData, help='The kpoints to use (KPOINTS).')

        spec.input('charge_density', valid_type=(ChgcarData, SinglefileData), required=False, help='The charge density. (CHGCAR)')
        #spec.input('metadata.options.parser_name', default='vasp_tmm.scf') # or vasp_tmm.dos
        #spec.input('metadata.label', valid_type=str, required=False)
        spec.outline(
                cls.initialize,# might be useful
                cls.init_scf,
                cls.run_scf,
                cls.verify_workchain,
                cls.init_dos,
                cls.run_dos,
                cls.verify_workchain,
                cls.results
                )
        #spec.expose_outputs(cls._vasp_process)
        spec.output('density_of_states', valid_type=ArrayData, required=False)
        spec.exit_code(0, 'NO_ERROR', message='everything is going well')
        spec.exit_code(505,
                'ERROR_NO_DOS_FOUND',
                message='fail to extract dos array from DOSCAR')

    def initialize(self):
        """initialize the context """
        self.report('initialize')
        self.ctx.inputs = AttributeDict()
        #self.ctx.inputs.structure = self.inputs.structure
        #self.ctx.scf_incar = self.inputs.scf_incar
        #self.ctx.dos_incar = self.inputs.dos_incar
        #self.ctx.inputs.code = self.inputs.code

    def init_scf(self):
        """ set up self.ctx.inputs """
        try:
            self.ctx.inputs
        except AttributeError as no_inputs:
            raise ValueError('No input dictionary is defined in self.ctx.inputs') from no_inputs
        #self.ctx.inputs.update(self.exposed_inputs(self._vasp_process))
        self.ctx.inputs.code = self.inputs.code
        self.ctx.inputs.parameters = self.inputs.scf_incar
        self.ctx.inputs.structure = self.inputs.structure
        self.ctx.inputs.potential = self.inputs.potential
        self.ctx.inputs.kpoints = self.inputs.kpoints

    #def run_scf(self):
    #    self.report('run_scf')
    #    #inputs = self.ctx.inputs
    #    proc = self._vasp_process
    #    future = self.submit(proc, **inputs)
    #    self.to_context(**{'scf': future})


    def run_scf(self):
        self.report('run_scf')
        proc = self._vasp_process
        #inputs = proc.get_inputs_template()
        inputs = AttributeDict()
        #code = Code.get_from_string('vasp_tmm@localhost')
        #builder = code.get_builder()
        for key in self.ctx.inputs:
            #if self.ctx.inputs[key] is not None:
            #    # exclude builder.parameters
            #    builder[key] = self.ctx.inputs[key]
            inputs[key] = self.ctx.inputs[key]
        #self.ctx.inputs.
        #inputs.parameters = self.inputs.scf_incar
        #builder.parameters = self.ctx.inputs['scf_incar']
        future = self.submit(proc, **inputs)
        #self.to_context(**{'scf': future})
        self.to_context(workchains=append_(future))

    def _copy_chgcar(self):
        """ copy CHGCAR from 'run_scf' process,
        i.e., update inputs.charge_density"""
        charge_density = self.ctx.workchains[-1].outputs['chgcar'].clone() # ChgcarData or SinglefileData
        #self.ctx['charge_density'] = charge_density
        #if self.ctx['charge_density'] is None:
        #    raise ValueError('No CHGCAR file generated from scf.')
        return charge_density

    def init_dos(self):
        """ update parameters and parser_name 
        and add charge_density """
        #self.ctx.inputs.parameters = self.inputs.dos_incar
        self.ctx.inputs.charge_density = self._copy_chgcar()

        ## UPDATE self.inputs.dos_incar based on fermi energy obtained from scf calculation
        incar = self.update_incar()
        self.ctx.inputs.parameters = incar
        # update kpoints
        kpoints = self.get_dos_kpoints()
        self.ctx.inputs.kpoints = kpoints

    def update_incar(self):
        """ add the tags 'EMAX', 'EMIN' to INCAR """
        E_fermi = self.ctx.workchains[-1].outputs['E_fermi'].value
        emin = E_fermi - 10.0
        emax = E_fermi + 4.0
        incar = self.inputs.dos_incar.get_dict()
        incar['EMIN'] = emin
        incar['EMAX'] = emax
        incar = Dict(incar)
        return incar

    def get_dos_kpoints(self):
        """ set KPOINTS with density 100 1/AA for dos"""
        KpointsData = DataFactory('array.kpoints')
        kpoints = KpointsData()
        kpoints.set_array('kpoints', np.array([100.0, 100.0, 100.0]))
        return kpoints

    #def run_dos(self):
    #    self.repost('run_dos')
    #    proc = self._vasp_process
    #    inputs = self.ctx.inputs
    #    future = self.submit(proc, **inputs)
    #    self.to_content(**{'dos': future})


    #def run_dos(self):
    #    self.report('run_dos')
    #    proc = self._vasp_process
    #    inputs = AttributeDict()
    #    for key in self.ctx.inputs:
    #        inputs[key] = self.ctx.inputs[key]
    #    inputs.metadata.options.parser_name = 'vasp_tmm.dos'
    #    future = self.submit(proc, **inputs)
    #    self.to_context(**{'dos': future})


    def run_dos(self):
        self.report('run_dos')
    #    #self._copy_chgcar()
    #    proc = CalculationFactory('vasp_tmm.vasp')
    #    inputs = proc.get_inputs_template()
        code = Code.get_from_string('vasp@localhost')
        builder = code.get_builder()
    #    #code = Code.get_from_string('vasp_tmm@localhost')
    #    code = self.inputs.code
    #    inputs.code = code
    #    #builder = code.get_builder()
        for key in self.ctx.inputs:
            try:
                builder[key] = self.ctx.inputs[key]
            except:
                pass
    #   #builder.parameters = self.ctx.inputs['dos_incar']
    #    inputs.parameters = self.inputs.dos_incar
    #    #builder.charge_density = self.ctx['charge_density']
    #    inputs.charge_density = self._copy_chgcar()
        builder.metadata.options.parser_name = 'vasp_tmm.dos'
        future = self.submit(builder)
        #self.to_context(**{'dos': future})
        self.to_context(workchains=append_(future))

    def verify_workchain(self):
        """ return non-zero exit code if the current workchain failed """
        workchain = self.ctx.workchains[-1]
        workchain_exit_status = workchain.exit_status
        workchain_exit_message = workchain.exit_message

        if workchain.is_finished_ok:
            self.ctx.exit_code = self.exit_codes.NO_ERROR
        else:
            self.ctx.exit_code = ExitCode(status=workchain_exit_status, message=workchain_exit_message)
            self.report(f"calculation failed with exit code {workchain_exit_status}")

        return self.ctx.exit_code

    def results(self):
        """ extract density of states from DOSCAR
        and store as ArrayData"""
        #workchain = self.ctx.workchain[-1]
        self.report('extract results')
        # parse DOSCAR file to get density of states
        density_of_states = self.ctx.workchains[-1].outputs.dos # ArrayData node
        
        # make sure output is not empty
        dos = density_of_states.get_array('dos_array')
        if len(dos[0]) == 0:
            self.ctx.exit_code = self.exit_codes.ERROR_NO_DOS_FOUND
            return self.ctx.exit_code

        self.out('density_of_states', density_of_states)
        self.report('finish density of states calculation!')

    #def group_results(self):
    #    """ add the WorkChainNode to a specific group 
    #    based on the exit_status """
    #    if self.ctx.exit_code == 0:
    #        group = load_group('dos_done')
    #        group.add_nodes(calc)
    #    elif self.ctx.exit_code == 400:
    #        group = load_group('scf_not_converged')
    #        group.add_nodes(calc)
    #    elif calc.exit_status == 401:
    #        group = load_group('scf_with_error')
    #        group.add_nodes(calc)
    #    else:
    #        group = load_group('dos_unfinished')
    #        group.add_nodes(calc)
