# Opentrons Dispense Protocols & Custom Labware 

This directory contains `.py` dispense protocols for the Opentrons OT-2 and the corresponding custom labware definitions (`.json`) and 3D printing files used in the accompanying publication.

---

## Reproducing the paper

This code accompanies:

- **Title:** An automated platform for tailored late-stage halogenation of pharmaceuticals
- **Authors:** **Callum R. John**, Eric Tan, Callum S. Begg, Andrew J. P. White, Peter Buijnsters, Jesús Alcázar, Alex M. Ganose, Rebecca L. Greenaway, and James A. Bull  
- **Journal / Year:** XXXXXX 
- **DOI:**  10.XXXX/XXXX_  
- **Preprint:** XXXXXX

---

## Table of contents
- `/3D_printing_files`**:** `.stl` and `.dxf` files used to manufacture custom labware.
- `/labware`**:** `.json` custom labware definations references in dispense protocols.
- `/nmr_sample_prep`**:** Opentrons OT-2 `.py` dispense protocols used to prepare NMR samples in an automated, high-throughput fasion.
- `/reaction_setup`**:** Various Opentrons OT-2 `.py` dispense protocols used to prepare arrays of reactions for screening.
- `README.md`**:** This file.

---

### Protocol → Experiment mapping

| Protocol file                        | Supplimentary information section | Description |
|-------------------------------------|--------------------|---------------------|
|**reaction_setup**
| `protocol_1(stage1_screening).py`                  | 5.3.1  | Broad stage 1 screen dispense protocol. |
| `protocol_2(stage2_0to6_chlor).py`                 | 5.3.2 - 4    | Stage 2 screening, chlorination reactions between 0 - 6 TFA equivalents. |
| `protocol_3(stage2_0to10_nis_nbs).py`              | 5.3.5    | Stage 2 screening, iodination and bromination reactions between 0 - 10 TFA equivalents. |
| `protocol_4(stage2_repeats_and_high_acidity).py`   | 5.3.6    | Stage 2 screening, repeats and reactions between 10 - 25 TFA equivalents. |
| `protocol_5(stage2_additional_repeats).py`         | 5.3.7   | Stage 2 screening, complete screening between 0 - 25 TFA equivalents. |
| `protocol_6(stage2_single_halogenation_screen).py` | 5.3.8    | Stage 2 screening, singular halogenation between 0 - 25 TFA equivalents |
| `protocol_7(automated_scaleup).py`                 |8    | Automated dispense of reagent stock solutions for optimised halogenation scale-ups (0.1 mmol). |
|**nmr_sample_prep**
| `nmr_sample_preparation.py`                        |------------------  | Dispense of DMSO-d6 internal standard solutions and top-up into a 96-well plate of reaction residues. |
| `nmr_sample_transfer.py`                           |------------------  | Transferral of NMR samples from 96-well reaction plate to a 96-tube rack of 5mm NMR tubes. |

---

## Requirements

- **Robot:** Opentrons **OT-2** 
- **API:** Opentrons Python API v2.9  
- **Software:**
  - **Robot run:** Upload protocol file and interface via the Opentrons App (recommended)  
  - **Local simulation:** Python 3.8–3.11 with `opentrons` installed

### Install for local simulation (optional)

```bash
# Create a dedicated environment (recommended)
conda create --name opentrons_env
conda activate opentrons_env

# Install the Opentrons API for SIMULATION ONLY
pip install opentrons

# Run simulation...
# Replace placeholders with actual paths
opentrons_simulate.exe <path/to/protocol.py> --custom-labware-path=<path/to/custom_labware_directory>

```

---

## Custom Labware

All custom labware JSON definations can be found in ./labware/

### Add labware to the Opentrons App

1. Open the **Opentrons App** on your computer.  
2. Go to **More → Custom Labware**.  
3. Click **Add Labware** and select the relevant `.json` from `./labware/`.  
4. Repeat for each required definition.

---

## Protocol usage

Following protocol simulation (optional)...

1. Power on the OT-2 and connect via the Opentrons App.  
2. Navigate to **Robots → [Your OT-2] → Protocols → Upload** the `.py` file.  
3. Verify:  
   - Pipettes and tip types match the protocol.  
   - Deck setup matches the protocol (stock solutions, well plates).  
   - Custom labware appears and is recognized.  
4. Calibrate labware and pipette tip offsets. 
5. Run the protocol and monitor.

---

## Best Practices & Safety

- Ensure each well contains at least 10% excess volume of stock to prevent solutions from running dry during the run.
- Consider solvent evaporation when pausing the run for an extended period of time.
- Ensure flammable/volatile reagents are compatible with your lab’s safety policy and the OT-2 enclosure.  
- If using harsh/corrosive chemicals, confirm chemical compatibility with the Opentrons and pipette tips.
- DO NOT put your hands inside the OT-2 enclosure whilst a run is active.
- Dispose of used pipette tips in contaminated sharps waste.

---

## Protocol troubleshooting

- **Syntax/runtime error after importing `.py` protocol into the Opentrons App**
  Check `.py` file in a code editor and correct where necessary. Simulate protocol with `opentrons_simulate.exe` (see above).

- **“Labware definition not found”**  
  Ensure the relevent `.json` file is in the Custom Labware folder Install the `.json` via the Opentrons App (**More → Custom Labware**) 

- **Pipette/tip mismatch**  
  Ensure the pipette models in the protocol match what’s installed; update the `load_instrument` lines if needed.

- **Clogging / air bubbles in pipette tip during dispense**  
  Ensure stock solution homogeneity, lower aspirate/dispense flow rates, or add air gaps.

- **Stock solution "bumping" into pipette**  
  Ensure pipette tip has enough clearance from the bottom of the well during aspirations. If needed, adjust the Z-axis for the affected labware so the calibration point sits slightly higher during labware and pipette offset calibration.

- **Offset alignment issues**  
  Re-run labware and pipette tip offset calibration; if issues persist, recallibrate pipettes using the Opentrons app.

- **Stock solution running dry mid run**  
  Rerun the protocol with a larger volumn of the relevent stock solution if possible.