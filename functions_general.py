import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def add_pulse(time_vector, signal_vector, t_start, t_end, amplitude):
    mask = (time_vector >= t_start) & (time_vector < t_end)
    signal_vector[mask] = amplitude
    return signal_vector

def add_pulses(impulse_list, time_data, laser_power):
    for t_start, t_end, amplitude in impulse_list:
        laser_power = add_pulse(time_data, laser_power, t_start, t_end, amplitude)
    return laser_power

# ---------------------------------------------------------------------------------------------------
# Model definition

def model_fit_double_rate_dict(time_downsampled, laser_power_downsampled, parameters_dict):
    kp1 = parameters_dict['kp1']
    kd1 = parameters_dict['kd1']
    Imax1 = parameters_dict['Imax1']
    kp2 = parameters_dict['kp2']
    kd2 = parameters_dict['kd2']
    Imax2 = parameters_dict['Imax2']

    g_signal1 = np.zeros(len(time_downsampled))
    g_signal2 = np.zeros(len(time_downsampled))

    if len(time_downsampled) != len(laser_power_downsampled):
        raise ValueError("time_downsampled and laser_power_downsampled must have the same length.")
    
    for i in range(0, len(time_downsampled)):
        signal = (laser_power_downsampled[i] > 0).astype(float)
        if i == 0:
            g_signal1[i] = 0
            g_signal2[i] = 0
        else:
            delta_t = time_downsampled[i] - time_downsampled[i-1]
            kp1_prime = kp1 * signal
            kd1_prime = kd1
            alpha_1 = kp1_prime
            beta_1 = kp1_prime+kd1_prime
            g_signal1[i] = alpha_1/beta_1+(g_signal1[i-1]-alpha_1/beta_1)*np.exp(-beta_1*delta_t)

            kp2_prime = kp2 * signal
            kd2_prime = kd2
            alpha_2 = kp2_prime
            beta_2 = kp2_prime+kd2_prime
            g_signal2[i] = alpha_2/beta_2+(g_signal2[i-1]-alpha_2/beta_2)*np.exp(-beta_2*delta_t)    
    I_signal1 = Imax1*g_signal1
    I_signal2 = Imax2*g_signal2
    I_signal = I_signal1 + I_signal2
    return I_signal, I_signal1, I_signal2

# ---------------------------------------------------------------------------------------------------
# Functions for global fit

class GlobalFitManager:
    def __init__(self, model_function, time_list, power_list, intensity_list):
        self.model_function = model_function
        self.time_list = time_list
        self.power_list = power_list
        self.intensity_list = intensity_list
        self.n_curves = len(intensity_list)
        
        if not (len(time_list) == len(power_list) == len(intensity_list)):
            raise ValueError("Time, power, and intensity lists must have the same length.")
        
        self.all_intensity = np.concatenate(intensity_list)
        self.all_time = np.concatenate(time_list)
        
        self.init_val_dict = {}
        self.var_dict = {}
        self.fit_global = {}
        self.param_map = [] 
        self.fixed_params = {}
        
    def setup_parameters(self, init_val_dict, var_dict, fit_global):
        self.init_val_dict = init_val_dict
        self.var_dict = var_dict
        self.fit_global = fit_global
        
        self.p0_list = []
        self.bounds_min = []
        self.bounds_max = []
        self.param_map = []
        
        for key in init_val_dict.keys():
            val = init_val_dict[key]
            is_fitted = var_dict.get(key, 0)
            is_global = fit_global.get(key, 0)
            
            if is_fitted == 0:
                self.fixed_params[key] = val
            else:
                if is_global == 1:
                    self.p0_list.append(val)
                    self.bounds_min.append(0)
                    self.bounds_max.append(np.inf)
                    self.param_map.append(('global', key, None))
                else:
                    for i in range(self.n_curves):
                        self.p0_list.append(val)
                        self.bounds_min.append(0)
                        self.bounds_max.append(np.inf)
                        self.param_map.append(('local', key, i))
                        
    def _wrapper_function(self, x_dummy, *flat_params):
        current_params_list = [self.fixed_params.copy() for _ in range(self.n_curves)]
        
        for idx, val in enumerate(flat_params):
            type_, name, curve_idx = self.param_map[idx]
            if type_ == 'global':
                for i in range(self.n_curves):
                    current_params_list[i][name] = val
            elif type_ == 'local':
                current_params_list[curve_idx][name] = val
                
        results = []
        for i in range(self.n_curves):
            t = self.time_list[i]
            p = self.power_list[i]
            params = current_params_list[i]
            intensity_fit = self.model_function(t, p, params)[0]
            results.append(intensity_fit)
            
        return np.concatenate(results)

    def run_fit(self):
        print(f"Starting global fit with {len(self.p0_list)} free parameters...")
        try:
            popt, pcov = curve_fit(
                self._wrapper_function,
                self.all_time,
                self.all_intensity,
                p0=self.p0_list,
                bounds=(self.bounds_min, self.bounds_max),
                method='trf',
                maxfev=1000
            )
            print("Fit completed successfully.")
            return self._process_results(popt)
        except Exception as e:
            print(f"Error during fitting: {e}")
            return None

    def _process_results(self, popt):
        final_params_list = [self.fixed_params.copy() for _ in range(self.n_curves)]
        for idx, val in enumerate(popt):
            type_, name, curve_idx = self.param_map[idx]
            if type_ == 'global':
                for i in range(self.n_curves):
                    final_params_list[i][name] = val
            elif type_ == 'local':
                final_params_list[curve_idx][name] = val
                
        results_df = pd.DataFrame(final_params_list)
        results_df.insert(0, 'Curve_Index', range(len(results_df)))
        return results_df

    def calculate_R2(self, results_df):
        r2_list = []
        for i in range(self.n_curves):
            t = self.time_list[i]
            p = self.power_list[i]
            y_exp = self.intensity_list[i]
            best_params = results_df.iloc[i].to_dict()
            y_fit = self.model_function(t, p, best_params)[0]
            
            ss_res = np.sum((y_exp - y_fit) ** 2)
            ss_tot = np.sum((y_exp - np.mean(y_exp)) ** 2)
            r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            r2_list.append(r2)
        return np.array(r2_list)