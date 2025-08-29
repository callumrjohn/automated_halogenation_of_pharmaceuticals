# Gaussian Process Regression (GPR) condition optimisation of HTE halogenations

This directory contains code used to predict the optimal conditions through interpolation of HTE data for a particular halogenation. The `Halogenation` class, found in `gpr_predictions.py` is used to generate a predicted acid-yield reponse curve using GPR and extract an optimum TFA equivalent within the Jupyter Notebook `gpr_analysis_notebook.ipynb`. Outputs from this can be found in `./gpr_results`, containing the optimum conditions for the investigated halogenations

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
- `/gpr_results`**:** A directory containing `.csv` output files containing the GPR predicted optimum halogenating conditions for the scope investigated in the accompanying publication.
- `gpr_analysis_notebook.ipynb`**:** Jupyter notebook utalising the `Halogenation` class to predict optimum halogenating conditions.
-  `gpr_predictions.py`**:** File containing the `Halogenation` class, used to predict optimum halogenating conditions for a halogenation through interpolation of HTE data.
- `hte_halogenation_conversions_for_gpr`**:** `.csv` file containing stage 2 HTE halogenation conversion data for between 0 - 25 TFA equivalents.
- `hte_halogenation_yields_for_gpr`**:** `.csv` file containing stage 2 HTE halogenation yield data for between 0 - 25 TFA equivalents.
- `README.md`**:** This file.
- `requirements.txt`**:** Lists all Python packages needed to run the code in this directory.

---

## Requirements and installation

- **Python 3.9+** recommended.  
- Numpy, Pandas, SKLearn, SciPy 

```bash
# Create a dedicated environment (recommended)
conda create --name gpr_env
conda activate gpr_env

# Install the required packages
pip install -r requirements.txt

```

---

## Quick start

```python

from gpr_predictions import Halogenation
import numpy as np
from sklearn.gaussian_process.kernels import RBF

# Continuous data from HTE 
X = [0, 1, 2, 6, 10, 15] # eg. Acid equivalents
y = [0, 10, 30, 80, 70, 40] # eg. %yield

# Stack data into a 2D array to input into class (can also contain a 3rd column eg conversion)
data = np.column_stack((X, y))

# Initialise class with labels and data
h = Halogenation('Substrate', 'Reagent', data)

# Define kernel for use with the GPR model
kernel = 1.0 * RBF(length_scale=1e0, length_scale_bounds=ls_bounds)

# Run the GPR model and interpolate the data. Multiple kernels can be run with data stored within the class if required
h.gprcalculate(kernel)

# Pick the optimum from the generated curve
optimum = h.pickoptimum()

print(f'Optimum condition: {optimum[0]}, Predicted response: {optimum[1]})

```

---

# Halogenation class API

Predicts **yield** and/or **conversion** responses vs. acid equivalents for halogenation reactions using **Gaussian Process Regression (GPR)**, with optional peak picking and cross-validated MAE scoring.


## Overview

- **Inputs:** substrate (str), reagent (str), and a 2D numeric array (`acid_equiv`, `yield`, `[conversion]`).
- **Core tasks:** fit GPR models (with scaling), generate dense predictions, detect response maxima, compute LOO-CV MAE, and pick an optimum.
- **Outputs:** per-kernel dictionaries containing prediction grid, standard deviations, detected maxima, and MAE; helper methods to select best kernel and optimum conditions.


## Data format

`data`: 2D array-like of shape `(n_points, 2 or 3)`
col 0 -> acid_equiv (float)
col 1 -> yield (float, percent 0–100 recommended)
col 2 -> conversion (float, percent 0–100) [optional]

> If you plan to model both `yield` _and_ `conversion` (i.e., `dset='conv'` or `'both'`), the input must have **3 columns**.

## Constructor

### `Halogenation(substrate: str, reagent: str, data: array_like)`

**Creates** a new experiment wrapper.

- **Parameters**
  - `substrate` — name/identifier of the substrate (str)
  - `reagent` — name/identifier of the halogenating reagent (str)
  - `data` — 2D array with 2 or 3 columns (see *Data format*)

- **Side effects / state**
  - Initializes `self.yieldoutputs: dict`
  - Initializes `self.convoutputs: dict` **only if** `data` has 3 columns

---

## Properties

- `substrate: str` — substrate string  
- `reagent: str` — reagent string  
- `data: np.ndarray` — a copy of the internal data array  
- `acidequiv: np.ndarray` — shape `(n_points,)`, from `data[:, 0]`  
- `yieldvalues: np.ndarray` — shape `(n_points,)`, from `data[:, 1]`  
- `convvalues: Optional[np.ndarray]` — `(n_points,)` if 3-col input, else `None`

> **Note:** the `@property` setters in the provided code **validate** types but do not assign.

---

## Fitting & prediction

### `gprcalculate(kernel, **kwargs) -> None`

Fits GPR on the selected dataset(s), generates dense predictions, detects maxima, and stores results in `yieldoutputs` / `convoutputs`.

- **Required**
  - `kernel` — any scikit-learn GPR kernel instance (e.g., `RBF(...) + WhiteKernel(...)`)

- **Keyword arguments**
  - `kernelname: str` — name key for results (default: `str(kernel)`)
  - `scaler` — sklearn scaler used in a `Pipeline` (default: `RobustScaler()`)
  - `height: float` — minimum peak height for `find_peaks` in response units (default: `5`)
  - `dset: Literal['yield','conv','both']` — which dataset(s) to model (default: `'yield'`)

- **What it does**
  - Builds `Pipeline([('scaler', scaler), ('model', GaussianProcessRegressor(kernel=..., n_restarts_optimizer=7))])`
  - Creates a dense prediction grid `x` (1000 points between min/max acid equiv)
  - Predicts mean (`y_pred`) and std (`y_pred_std`) on `x`
  - Peak-picks the response curve (≥ `height`) and also includes the first and last grid points
  - Computes **Leave-One-Out** (LOO) MAE
  - Stores results per dataset in a dict under `kernelname`:

```python
{
  'prediction': np.ndarray,  # shape (1000, 2): [acid_equiv, mean]
  'stdevs':     np.ndarray,  # shape (1000, 2): [acid_equiv, std]
  'maxima':     np.ndarray,  # shape (k, 2):    [acid_equiv_at_peak, mean_at_peak]
  'mae':        float
}
```

- **Raises**
  - `ValueError` if dset not in `{'yield','conv','both'}`.
  - Downstream errors if dset requests conv but the input data had no conversion column.

---

## Model selection

**`best_model_yield() -> str`**  
Returns the kernel name (dict key) with the lowest MAE in `yieldoutputs`.

- **Raises:**  
  - `ValueError` / `KeyError` if `yieldoutputs` is empty.

**`best_model_conv() -> str`**  
Returns the kernel name with the lowest MAE in `convoutputs`.

- **Raises:**  
  - `ValueError` / `KeyError` if `convoutputs` is empty.

---

## Optimum selection

**`pickoptimum(**kwargs) -> np.ndarray`**  
Picks the optimum conditions from the stored predictions, preferring the highest yield (with a >5% improvement threshold between successive detected maxima). Optionally appends the corresponding conversion at the same acid equiv if a conversion model is available.

- **Keyword arguments:**  
  - `yield_kernel: Optional[str]` — kernel to use for yield (default: first key in `yieldoutputs`)  
  - `conv_kernel: Optional[str]` — kernel to use for conversion (default: first key in `convoutputs`)  

- **Returns:**  
  - If yield used: `np.array([acid_equiv, predicted_yield])`  
  - If conversion also matched on the same acid equiv: `np.array([acid_equiv, predicted_yield, predicted_conversion])`  
  - If only conversion used: `np.array([acid_equiv, predicted_conversion])`  

- **Raises:**  
  - `ValueError` if neither yield nor conversion models are available (i.e., you didn’t call `gprcalculate` first).  

- **Behavior details:**  
  - Starts at the first detected “maximum” (includes grid endpoints).  
  - Moves to the next peak only if its response exceeds the current by >5 units.  
  - For conversion appending, it looks up the same acid equiv index on the conversion prediction grid.  