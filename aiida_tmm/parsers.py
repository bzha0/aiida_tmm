from aiida.engine import ExitCode
from aiida.orm import SinglefileData
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

Vaspcalculation = CalculationFactory('vasp_tmm.vasp')

class VaspParser(Parser):
    """
    Parse outputs and store resutls in the database
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

