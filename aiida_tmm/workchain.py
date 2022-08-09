import numpy as np

from aiida.engine import WorkChain, submit
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
        spec.input('metadata.options.parser_name', default='vasp_tmm.scf') # or vasp_tmm.dos
        spec.outline(
                cls.initialize,# might be useful
                cls.init_scf,
                cls.run_scf,
                cls.init_dos,
                cls.run_dos,
                cls.results
                )
        #spec.expose_outputs(cls._vasp_process)
        spec.output('density_of_states', valid_type=ArrayData)

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
        self.ctx.future = submit(proc, **inputs)
        #self.to_context(**{'scf': future})

    def _copy_chgcar(self):
        """ copy CHGCAR from 'run_scf' process,
        i.e., update inputs.charge_density"""
        charge_density = self.ctx.future.outputs['chgcar'].clone() # ChgcarData or SinglefileData
        #self.ctx['charge_density'] = charge_density
        #if self.ctx['charge_density'] is None:
        #    raise ValueError('No CHGCAR file generated from scf.')
        return charge_density

    def init_dos(self):
        """ update parameters and parser_name 
        and add charge_density """
        self.ctx.inputs.parameters = self.inputs.dos_incar
        self.ctx.inputs.charge_density = self._copy_chgcar()
        self.ctx.inputs.metadata.options.parser_name = 'vasp_tmm.dos'

    #def run_dos(self):
    #    self.repost('run_dos')
    #    proc = self._vasp_process
    #    inputs = self.ctx.inputs
    #    future = self.submit(proc, **inputs)
    #    self.to_content(**{'dos': future})


    def run_dos(self):
        self.report('run_dos')
        proc = self._vasp_process
        inputs = AttributeDict()
        for key in self.ctx.inputs:
            inputs[key] = self.ctx.inputs[key]
        self.ctx.future = submit(proc, **inputs)
        #self.to_content(**{'dos': future})


    #def run_dos(self):
    #    self.report('run_dos')
    #    #self._copy_chgcar()
    #    proc = CalculationFactory('vasp_tmm.vasp')
    #    inputs = proc.get_inputs_template()
    #    #builder = Calc.get_builder()
    #    #code = Code.get_from_string('vasp_tmm@localhost')
    #    code = self.inputs.code
    #    inputs.code = code
    #    #builder = code.get_builder()
    #    for key in self.ctx.inputs:
    #        inputs[key] = self.ctx.inputs[key]
    #   #builder.parameters = self.ctx.inputs['dos_incar']
    #    inputs.parameters = self.inputs.dos_incar
    #    #builder.charge_density = self.ctx['charge_density']
    #    inputs.charge_density = self._copy_chgcar()
    #    inputs.metadata.options.parser_name = 'vasp_tmm.dos'
    #    future = self.submit(proc, **inputs)
    #    self.to_content(**{'dos': future})

    def results(self):
        """ extract density of states from DOSCAR
        and store as ArrayData"""
        #workchain = self.ctx.workchain[-1]
        self.report('get results')
        # parse DOSCAR file to get density of states
        density_of_states = self.ctx.future.outputs['dos'] # ArrayData node
        self.out('density_of_states', density_of_states)
        self.report('finish density of states calculation!')
