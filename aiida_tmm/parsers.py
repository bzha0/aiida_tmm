import numpy as np

from aiida.engine import ExitCode
from aiida.orm import SinglefileData, ArrayData, Float
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

        # parser DOSCAR for Fermi energy
        efermi = self.parse_Efermi(files_retrieved)
        # parse CHGCAR
        chgcar = self.parse_chgcar(files_retrieved)

        if efermi and chgcar:
            return ExitCode(0)
        else:
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

    def parse_Efermi(self, files_retrieved):
        files_expected = ['DOSCAR']
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return False

        self.logger.info('Parsing the output files')
        output = self._get_Efermi()
        self.out('E_fermi', output)
        return True

    def _get_Efermi(self):
        with self.retrieved.open('DOSCAR', 'rb') as handle:
            line = handle.readlines()[5]
            Efermi = float(line.split()[3])
            Efermi = Float(Efermi)
        return Efermi

    def parse_chgcar(self, files_retrieved):
        files_expected = ['CHGCAR']
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return False

        # add output files
        self.logger.info('Parsing the output files')
        with self.retrieved.open('CHGCAR', 'rb') as handle:
            output_node = SinglefileData(file=handle)
        self.out('chgcar', output_node)
        # 'chgcar' is the name of the link that connects the calculation and data node.
        return True


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

