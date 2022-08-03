import re
import io
import subprocess

from aiida.orm import StructureData

class PotcarIo(object):
    """
    Read the structure, find the corresponding POTCAR files
    and put them together to be ready to pass to PotcarData.
    """

    # _PATH = '/home/bz43nogu/PBE54/'

    def __init__(self, structure, path):
        """ structure can either be passed directly to the class or get as a node from database (added later) """
        self.structure = structure
        #if self.structure is None:
        #    self.structure = self.get_structure()
        #if self.structure is None:
        #    raise ValueError('cannot find any structure in the aiida repository')
        self.pot_list = self.get_pot_list()
        self.path = path
    
    #def get_structure(self):
    #    struc_node = StructureData(ase=structure.get_ase())
    #    return struc_node

    def get_pot_list(self):
        """ Get species from strucuture node.
        :return symbols: a list"""
        symbols = self.structure.get_ase().get_chemical_symbols()
        symbols = list(set(symbols))
        return self.sym_pot_map(symbols)

    def sym_pot_map(self, symbols):
        """ 
        map symbols to the potential name 
        :param symbols: a list of symbols, eg. ['Na', 'Cl']
        :return pot_list: a list of potential names eg. ['Na_pv', 'Cl_GW']
        """
        pots=['B','C','N','O','F']
        potsv=['K','Rb','Cs','Ca','Sr','Ba','Sc','Y','Zr','V']
        potpv=['Na','Nb','Ta','Ti' ]
        potd=['Ga','In','Tl','Ge','Sn','Pb','Bi']
        pot2=[]
        pot3=['Yb', 'Ce', 'Dy', 'Er', 'Eu', 'Gd', 'Ho', 'Lu', 'Nd', 'Pm', 'Pr', 'Sm', 'Tb', 'Tm']

        potarr=['pots','potsv','potpv','potd','pot2','pot3']

        pot_list = []

        for sym in symbols:
            for j in potarr:
                if sym in eval(j):
                    pot_name = sym + '_' + j[3:]
                else:
                    pot_name = sym
            pot_list.append(pot_name)
        return pot_list

    def get_potcar_obj(self):
        """
        Reads potential files from your local path.
        :param path: path on your local computer that stores all the potential folders
        """
        #potcars = []
        input_list = []

        for sym in self.pot_list:
            POTCAR_path = self.path + sym + '/POTCAR'
            input_list.append(POTCAR_path)
            #with open(POTCAR_path, 'r', encoding='utf8') as potcar_fo:
                #potcar_string = potcar_fo.readlines()
            #    potcar_string = re.compile(r'\n?(\s*.*?End of Dataset\n)', re.S).findall(potcar_fo.read())
            #potcars.append(potcar_string)

        my_cmd = ['cat'] + input_list
        potcar_obj = subprocess.check_output(my_cmd, stderr=subprocess.DEVNULL)
        #potcar = "\n".join([str(pot).strip("\n") for pot in potcars]) + "\n"
        #potcar_obj = io.BytesIO(str.encode(potcar))
        potcar_obj = io.BytesIO(potcar_obj)
        return potcar_obj # potcar string to be passed to PotcarData
