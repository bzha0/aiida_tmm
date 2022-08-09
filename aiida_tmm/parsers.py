import numpy as np

from aiida.engine import ExitCode
from aiida.orm import SinglefileData, ArrayData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

Vaspcalculation = CalculationFactory('vasp_tmm.vasp')

class ScfParser(Parser):
    """
    Parse CHGCAR and store resutls in the database
    """
    def parse(self, **kwargs):
        """ :return ExitCode: non-zero exit code, if parsing fails """
        # check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = ['CHGCAR']
        # if 'CHGCAR' is a subset of the retrieved set
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # add output files
        self.logger.info('Parsing the output files')
        with self.retrieved.open('CHGCAR', 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('chgcar', output_node) 
        # 'chgcar' is the name of the link that connects the calculation and data node.
        return ExitCode(0)

class DosParser(Parser):
    """
    Parse DOSCAR and store the dos array in the database.
    """
    def parse(self, **kwargs):
        # check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()
        files_expected = ['DOSCAR']
        # if 'DOSCAR' is a subset of the retrieved set
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES
        
        # add output files
        self.logger.info('Parsing the output files')
        output = self._parse_doscar() # dos array
        output_node = ArrayData()
        output_node.set_array('dos_array', output)
        self.out('dos', output_node)
        return ExitCode(0)

    def _parse_doscar(self):
        energy = []
        density = []
        integral = []
        with self.retrieved.open('DOSCAR', 'rb') as f:
            lines = f.readlines()[6:]
            for line in lines:
                energy.append(float(line.split()[0]))
                density.append(float(line.split()[1]))
                integral.append(float(line.split()[2]))
        return np.array([energy, density, integral])

