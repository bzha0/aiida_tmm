from aiida_tmm.utils import PotcarIo

# Set POTCAR file
p = PotcarIo(structure, path)
potcar_content = p.get_potcar_obj()
potcar_file = DataFactory('potcar')
potcar = potcar_file(potcar_content) # write as a node in 'potcar' data class
potcar.store()
