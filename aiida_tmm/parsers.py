import numpy as np

from aiida.engine import ExitCode
from aiida.orm import SinglefileData, ArrayData, Float, Dict
from aiida.parsers.parser import Parser
from aiida.plugins import CalculationFactory

from parsevasp.outcar import Outcar

Vaspcalculation = CalculationFactory('vasp_tmm.vasp')

class ScfParser(Parser):
    """
    Parse CHGCAR and store resutls in the database
    """
    def parse(self, **kwargs):
        """ :return ExitCode: non-zero exit code, if parsing fails """

        # check that folder content is as expected
        files_retrieved = self.retrieved.list_object_names()

        # parser OUTCAR file to check if calculation finished or converged
        run_status = self.parse_outcar(files_retrieved)
        if run_status['finished'] and not run_status['electronic_converged']:
            return self.exit_codes.ERROR_MAX_STEP_REACHED
        elif not run_status['finished']:
            # check vasp_output, if it is caused by time limit
            if self.time_limit():
                return self.exit_codes.ERROR_NOT_CONVERGED
            else:
                return self.exit_codes.ERROR_COULD_NOT_FINISH

        # parser DOSCAR for Fermi energy
        efermi = self.parse_Efermi(files_retrieved)
        # parse CHGCAR
        chgcar = self.parse_chgcar(files_retrieved)

        if efermi and chgcar:
            return ExitCode(0)
        else:
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

    def parse_outcar(self, files_retrieved):
        files_expected = ['OUTCAR']
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return False
        with self.retrieved.open('OUTCAR', 'r') as handle:
            outcar_parser = Outcar(file_handler=handle)
            run_status = outcar_parser.get_run_status()
            return run_status

    def time_limit(self):
        time_limit = False
        with self.retrieved.open('vasp_output', 'r') as handle:
            for line in handle.readlines():
                if 'DUE TO TIME LIMIT' in line:
                    time_limit = True
        return time_limit

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
        try:
            output = self._parse_doscar() # dos array
            output_node = ArrayData()
            output_node.set_array('dos_array', output)
            self.out('dos', output_node)
            return ExitCode(0)
        except:
            return self.exit_codes.ERROR_UNKNOWN

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

class MagParser(Parser):
    """
    Parse magnetic properties out of
    a spin polarized self-consistent calculation
    and store in the database
    """
    def parse(self, **kwargs):
        files_retrieved = self.retrieved.list_object_names()
        files_expected = ['OUTCAR']
        # if 'OUTCAR' is a subset of the retrieved set
        if not set(files_expected) <= set(files_retrieved):
            self.logger.error(f"Found files '{files_retrieved}', expected to find '{files_expected}'")
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        # parser OUTCAR file to check if calculation finished or converged
        run_status = self.parse_outcar(files_retrieved)
        if run_status['finished'] and not run_status['electronic_converged']:
            try:
                magnetization = self.get_mag(files_retrieved)
                self.out('magnetization', magnetization)
            except:
                pass
            return self.exit_codes.ERROR_MAX_STEP_REACHED
        elif not run_status['finished']:
            # check vasp_output, if it is caused by time limit
            if self.time_limit():
                try:
                    magnetization = self.get_mag(files_retrieved)
                    self.out('magnetization', magnetization)
                except:
                    pass
                return self.exit_codes.ERROR_NOT_CONVERGED
            else:
                try:
                    magnetization = self.get_mag(files_retrieved)
                    self.out('magnetization', magnetization)
                except ValueError:
                    pass
                return self.exit_codes.ERROR_COULD_NOT_FINISH

        # parse magnetic moment from OUTCAR
        magnetization = self.get_mag(files_retrieved)

        if magnetization is not None:
            magnetization = Dict(magnetization)
            self.out('magnetization', magnetization)
            return ExitCode(0)
        else:
            return self.exit_codes.ERROR_MAGNETIZATION_NOT_FOUND

    def get_mag(self, files_retrieved):
        self.logger.info('Parsing the magnetic data')
        return self.parse_outcar(files_retrieved, mag=True)

    def parse_outcar(self, files_retrieved, mag=False):
        """ parse either run status or magnetization """
        with self.retrieved.open('OUTCAR', 'r') as handle:
            outcar_parser = Outcar(file_handler=handle)
            if not mag:
                run_status = outcar_parser.get_run_status()
                return run_status
            # get magnetization info as a dict
            if mag:
                magnetization = outcar_parser.get_magnetization()#['full_cell']
                #magnetization = np.mean(magnetizations)
                return magnetization

    def time_limit(self):
        time_limit = False
        with self.retrieved.open('vasp_output', 'r') as handle:
            for line in handle.readlines():
                if 'DUE TO TIME LIMIT' in line:
                    time_limit = True
        return time_limit