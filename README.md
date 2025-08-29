# Automated Halogenation of Pharmaceuticals

This repository contains the code used and described in the accompanying publication ***An automated platform for tailored late-stage halogenation of pharmaceuticals***.

## Reproducing the paper

This code accompanies:

- **Title:** An automated platform for tailored late-stage halogenation of pharmaceuticals
- **Authors:** **Callum R. John**, Eric Tan, Callum S. Begg, Andrew J. P. White, Peter Buijnsters, Jesús Alcázar, Alex M. Ganose, Rebecca L. Greenaway, and James A. Bull  
- **Journal / Year:** XXXXXX 
- **DOI:**  10.XXXX/XXXX_  
- **Preprint:** XXXXXX

## Table of Contents

- **gpr_condition_predicition:** Code used to determine optimum conditions through GPR modelling of the HTE stage 2 screening data described in the accompanying publication with results.
- **opentrons_dispense_code:** Opentrons OT-2 `.py` dispense protocols, 3D printing files, and `.json` custom labware definations used to prepare reactions and analytical samples for the accompanying publication.
- **xtb_regiochemical_prediction:** Code used to generate xTB descriptors of the scope investigated in the accompanying publication and determine a method for regiochemical predicition.
- **LICENCE:** License information for this repository (BSD-3-Clause).
-**README.md:** This file.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/callumrjohn/automated_halogenation_of_pharmaceuticals.git
cd automated_halogenation_of_pharmaceuticals
```

Each directory has its own `README.md` with environment setup and usage instructions.  
Python **3.9+** is recommended. Individual requirements files are provided in subdirectories.

---

## Citation

If you use this code or data, please cite:

- **Primary citation (paper):**  
  XXXXX

- **Code (this repository):**  
  Automated halogenation of pharmaceuticals, commit/tag: , URL: https://github.com/callumrjohn/automated_halogenation_of_pharmaceuticals 

---

## License

This project is licensed under the [BSD 3-Clause License](./LICENSE).

---

## Contact

For questions or issues, please open a GitHub issue or contact:  
- **Callum R John:** c.john21@imperial.co.uk (_lead author_)
- **Rebecca L Greenaway:** r.greenaway@imperial.ac.uk (_corresponding author_)
- **James A Bull:** j.bull@imperial.ac.uk (_corresponding author_)
