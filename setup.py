from setuptools import setup

with open('aiida_tmm/__init__.py') as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split('"')[1]

setup(
        name='aiida_tmm',
        version=version,
        author="Bo Zhao",
        author_email="bo.zhao@tmm.tu-darmstadt.de",
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
                "vasp_tmm.scf = aiida_tmm.parsers:ScfParser",
                "vasp_tmm.dos = aiida_tmm.parsers:DosParser"
                ],
            'aiida.workflows':[
                "vasp_tmm.dos = aiida_tmm.workchain:DosWorkChain"
                ]
            }
        )
