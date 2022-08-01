from setuptools import setup

setup(
        name='aiida_tmm',
        packages=['aiida_tmm'],
        entry_points={
            'aiida.calculations': [
                "vasp_tmm.vasp = aiida_tmm.calculations:MyVaspCalculation"
                ],
            'aiida.data': [
                "vasp_tmm.potcar = aiida_tmm.data:PotcarData",
                "vasp_tmm.chargedensity = aiida_tmm.data:ChgcarData",
                "vasp_tmm.wavefun = aiida_tmm.data:WavecarData"
                ],
            'aiida.parsers': [
                "vasp_tmm.vasp = aiida_tmm.parsers:VaspParser"
                ],
            }
        )
