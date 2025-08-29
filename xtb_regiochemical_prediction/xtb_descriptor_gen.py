from aqme.csearch import csearch
from pathlib import Path
from aqme.qdescp import qdescp

def gen_aqme_descriptors(input_path, destination_dir, conformer_gen = 'rdkit', optimisation = 'xtb'):

    csearch(input=input_path, program=conformer_gen, output=destination_dir)

    csearch_dir = Path(destination_dir) / 'CSEARCH'
    conformer_files = [str(filepath) for filepath in csearch_dir.glob('*.sdf')]

    qdescp(files=conformer_files,
        program=optimisation,
        boltz=True,
        destination=destination_dir)

def main():

    input_path = 'smiles.csv'
    destination_dir = 'descriptors'

    # Ensure destination directory exists
    Path(destination_dir).mkdir(parents=True, exist_ok=True)

    gen_aqme_descriptors(input_path, destination_dir)
    print(f"Raw AQME xTB descriptors generated and saved to {destination_dir}")

if __name__ == "__main__":
    main()