# Regiochemical predictions of late-stage halogenations using xTB atomic descriptors

This directory contains code used to generate xTB descriptors for molecules from a SMILES string, descriptors of the pharmaceutical substrates invesitgated in the accompanying publication, and subsiquent studies to invesitgate if the descriptors could be used to predict the regioselectivity of electrophilic aromatic C-H halogenation.

---

## Reproducing the paper

This code accompanies:

- **Title:** An automated platform for tailored late-stage halogenation of pharmaceuticals
- **Authors:** **Callum R John**, Eric Tan, Callum S Begg, Andrew J P White, Peter Buijnsters, Jesús Alcázar, Alex M Ganose, Rebecca L Greenaway, and James A Bull  
- **Journal / Year:** XXXXXX 
- **DOI:**  10.XXXX/XXXX_  
- **Preprint:** XXXXXX

---

## Table of contents
- `/descriptors`**:** Directory containing the outputs of `xtb_descriptor_gen.py`.
- `f_values_top1.csv`**:** F-scores for the minimum and maximum values of xTB descriptors when the correct C-H halogenation regeochemistry is correctly predicted.
- `f_values_top2.csv`**:** F-scores for the minimum and maximum values of xTB descriptors when the correct C-H halogenation regeochemistry is within the top two predictions.
- `README.md`**:** This file.
- `smiles.csv`**:** SMILES strings and names of all the substrates investigated in the accompanying publication.
- `xtb_descriptor_gen.py`**:** Program used to generate xTB descriptors for the compounds in `smiles.csv`.
- `xtb_desciptors_regiochem.ipynb`**:** Jupyter notebook containing investigation of how xTB atomic descriptors can be used to predict the regiochemistry of electrophilic aromatic C-H halogenations.

---

## Requirements and installation

- **Python 3.10** recommended.  
- Numpy, Pandas, AQME, OpenBabel, RDKit

***Note:*** For xTB descriptor generation using AQME, OpenBabel must be installed, which requires a Unix-based OS (macOS/Linux).

```bash
# Create a dedicated environment (recommended)
conda create --name xtb_env python=3.10
conda activate xtb_env

# Install the required packages
pip install -r requirements.txt

```

---

## Usage

### Input format

The directory must contain a file named `smiles.csv` with two columns:  
- **`SMILES`** — SMILES strings of the compounds  
- **`code_name`** — names or labels assigned to each compound

### Running the script
From the command line:
```bash
python xtb_descriptor_gen.py
```
This will...
1. Run conformer generation with **RDKit** (`csearch`) on each SMILES in `smiles.csv`.  
2. Save conformers to `descriptors/CSEARCH/`.  
3. Run **xTB optimisation and descriptor calculation** (`qdescp`) on all conformers.  
4. Save descriptor files into `descriptors/`.
