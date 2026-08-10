from aqme.csearch import csearch
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem
from aqme.qdescp import qdescp
import pandas as pd


def _detect_column(columns, candidates):
    """Find first matching column name from candidates."""
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _write_fallback_sdfs(csv_path, destination_dir):
    """Generate conformer SDFs from CSV using RDKit if CSEARCH fails."""
    destination_dir = Path(destination_dir)
    df = pd.read_csv(csv_path)
    
    smiles_col = _detect_column(df.columns, ["SMILES", "smiles", "SMILES_1", "SMILES_alk", "SMILES_phosph"])
    name_col = _detect_column(df.columns, ["code_name", "name", "Code_name", "CODE_NAME"])

    if smiles_col is None:
        raise ValueError("No SMILES column found in CSV")

    csearch_dir = destination_dir / "CSEARCH"
    csearch_dir.mkdir(parents=True, exist_ok=True)

    sdf_files = []
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        if pd.isna(smiles) or str(smiles).strip() == "":
            continue

        mol = Chem.MolFromSmiles(str(smiles))
        if mol is None:
            print(f"  Warning: Could not parse SMILES for row {idx}: {smiles[:60]}")
            continue

        mol = Chem.AddHs(mol)
        params = AllChem.ETKDGv3()
        params.randomSeed = 0xC0FFEE
        if AllChem.EmbedMolecule(mol, params) == -1:
            print(f"  Warning: Could not embed conformer for row {idx}")
            continue

        if AllChem.MMFFHasAllMoleculeParams(mol):
            AllChem.MMFFOptimizeMolecule(mol)
        else:
            AllChem.UFFOptimizeMolecule(mol)

        code_name = str(row[name_col]) if name_col and not pd.isna(row[name_col]) else f"mol_{idx + 1}"
        sdf_path = csearch_dir / f"{code_name}_rdkit.sdf"

        mol.SetProp("_Name", code_name)
        mol.SetProp("SMILES", str(smiles))
        mol.SetProp("Real charge", str(Chem.GetFormalCharge(mol)))
        mol.SetProp("Mult", str(sum(atom.GetNumRadicalElectrons() for atom in mol.GetAtoms()) + 1))

        writer = Chem.SDWriter(str(sdf_path))
        writer.write(mol)
        writer.close()
        sdf_files.append(str(sdf_path))

    return sdf_files


def gen_aqme_descriptors(input_path, destination_dir, conformer_gen='rdkit', optimisation='xtb'):
    destination_dir = Path(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    conformer_files = []
    
    try:
        print(f"Running CSEARCH with {conformer_gen}...")
        csearch(input=input_path, program=conformer_gen, destination=destination_dir)
        csearch_dir = destination_dir / 'CSEARCH'
        conformer_files = [str(fp) for fp in csearch_dir.glob('*.sdf')]
        print(f"CSEARCH generated {len(conformer_files)} SDF file(s)")
    except Exception as e:
        print(f"CSEARCH failed: {e}")
        conformer_files = []

    # Fallback: generate SDFs locally if CSEARCH produced nothing
    if not conformer_files:
        print("Falling back to RDKit conformer generation...")
        conformer_files = _write_fallback_sdfs(input_path, destination_dir)
        print(f"Generated {len(conformer_files)} SDF file(s) with RDKit")

    if not conformer_files:
        raise RuntimeError("No conformer SDF files were generated")

    print(f"Running QDESCP with {optimisation}...")
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