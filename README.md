# Modeling Light-Induced Synaptic Behavior (PAZO)

This repository contains Python codes and Jupyter Notebooks designed to model and fit the light-induced synaptic response of PAZO. The models utilize rate balance equations (single-rate and double-rate models) to fit experimental synaptic intensity curves under different optical stimulation profiles.

---

## Repository Structure

The project consists of the following key files:

* **[functions_general.py](./functions_general.py)**: The core helper module containing:
  * The double-rate balance model (`model_fit_double_rate_dict`).
  * `GlobalFitManager`: A class designed to handle parameter optimization across one or multiple experimental curves simultaneously.
  * Pulse creation helper functions (`add_pulse`, `add_pulses`).
* **[Example_global_fit_power.ipynb](./Example_global_fit_power.ipynb)**: Global fitting of synaptic curves across different laser power densities.
* **[Example_global_fit_impulses_PPF.ipynb](./Example_global_fit_impulses_PPF.ipynb)**: Global fitting under Paired-Pulse Facilitation (PPF) conditions, fitting across multiple pulse interval times ($t_{off}$).
* **[Example_single_impulses_fit.ipynb](./Example_single_impulses_fit.ipynb)**: Single curve fitting specifically configured for analyzing the synaptic response to a train of 10 laser impulses.
* **[requirements.txt](./requirements.txt)**: List of Python packages required to run the code.

---

## Installation & Setup

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed on your system.

### 2. Install Dependencies
Clone or download this repository, navigate to the folder, and run:
```bash
pip install -r requirements.txt
```

### 3. Notebook Interactive Plots
The notebooks use `%matplotlib widget` (via the `ipympl` package) to render interactive plots inside your IDE (e.g., VS Code or JupyterLab). If you are using classic Jupyter Notebook or experience issues rendering plots, you can change `%matplotlib widget` to `%matplotlib inline` at the top of the notebooks.

---

## Usage Guide

The code supports three different fitting workflows:

### 1. Global Fitting across Power Densities
Use `Example_global_fit_power.ipynb` when you have multiple intensity response curves corresponding to different laser powers (e.g. from a single dataset file).
1. Place your data file (e.g., `Ton_10min_Toff_30min_ND0_preprocessed_data.txt`) in the `./Input data for fitting/` folder.
2. Define your laser pulse timeline in the notebook using the `impulse_list` parameter (specifying `t_start`, `t_end`, and `amplitude`).
3. Set the downsampling factor (e.g., `downsampling_factor = 50`) to adjust fitting performance.
4. Configure the fitting dictionaries:
   * `init_val_dict`: Starting values for parameters (`kp1`, `kd1`, `Imax1`, `kp2`, `kd2`, `Imax2`).
   * `var_dict`: Set to `1` to fit a parameter, or `0` to keep it fixed.
   * `fit_global`: Set to `1` if the parameter should be shared globally across all curves, or `0` if it is local (independent).
5. Run the cells to perform the global optimization and visualize the fits and parameter trends.

### 2. Global Fitting for Paired-Pulse Facilitation (PPF)
Use `Example_global_fit_impulses_PPF.ipynb` to fit synaptic behavior under double pulse stimulation with varying interval periods ($t_{off}$).
1. Place the experimental files in `./Input data for fitting/Impulses_PPF/`.
2. The notebook uses **Dynamic Downsampling**:
   * It creates a high-resolution mask around the pulse intervals (using `buffer_time_s` and `buffer_time_s_before`) to preserve critical rise/decay dynamics.
   * It uses a lower-resolution mask for flat regions to speed up calculations.
3. Configure the initial parameter guesses and run the fit.
4. The output will show a summary table of the global fit parameters for each $t_{off}$ interval and plot combined and separate fits.

### 3. Single Curve Fitting (10 Impulses Train)
Use `Example_single_impulses_fit.ipynb` to fit a single experimental curve representing the response to a long train of pulses (e.g. 10 laser impulses).
1. Place the single curve data file in `./Input data for fitting/`.
2. The notebook is preconfigured with the 10 pulses' timeline (`impulse_list` containing 10 items).
3. Set `downsampling_factor = 1` to use all points for maximum precision, or increase it if needed.
4. Run the optimizer to fit the double-rate balcance equation model parameters and visualize the fit.

---

## Model Description

The synaptic response $I(t)$ is modeled as the sum of intensities representing different decay rates.

### Double-Rate Model
The total intensity is represented as:
$$I(t) = I_{max,1} \cdot g_1(t) + I_{max,2} \cdot g_2(t)$$

Where $g_i(t)$ represents the normalized internal state of PAZO, governed by the balance equation:
$$\frac{dg_i}{dt} = k_{p,i} \cdot S(t) \cdot (1 - g_i) - k_{d,i} \cdot g_i$$

* $S(t)$: Optical stimulation signal (binary `1` when laser is ON, `0` when laser is OFF).
* $k_{pi}$: Potentiation rate constant (associated with the rise phase under light).
* $k_{di}$: Depression/decay rate constant (associated with the relaxation phase).
* $I_{maxi}$: Maximum current amplitude of the pathway.
