import numpy as np
from statistics import mean
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import LeaveOneOut
from scipy.signal import find_peaks



'''A class used to predict the yield and conversion of a halogenation reaction using Gaussian Process Regression

The class Halogenation takes in the following arguments:
substrate: str, the substrate used in the reaction
reagent: str, the reagent used in the reaction
data: np.array, a 2D array containing the columns: acid equiv, yield, and conversion (optional) of the reaction

The class can then be used to predict the yield and conversion of the reaction using Gaussian Process Regression. 

The method gprcalculate() takes in the following arguments:
kernel: the sklearn kernel to be used in the GPR model
**kwargs: additional arguments to be passed to the GPR model. These include:
kernelname: str, used to give a custom name to the kernel (default = str(kernel))
scaler: the sklearn scaler to be used in the GPR model
height: float, the minimum height of a peak within the acid/yield response curve (default = 5)
dset: str, the dataset to be used in the GPR model. Options are 'yield', 'conv', or 'both' (default = 'yield'). Seperate models will be generated for each dataset
Output: a dictionary containing predictions and metrics for each kernel used in the GPR model. (Keys: kernelname, Values: {'prediction': np.array, 'stdevs': np.array, 'maxima': np.array, 'mae': float})

The method best_model_yield() returns the model with the lowest mean absolute error for the yield dataset. The LeaveOneOut cross validation method is used to calculate this.

The method best_model_conv() returns the model with the lowest mean absolute error for the conversion dataset. The LeaveOneOut cross validation method is used to calculate this.

The method pickoptimum() returns the acid equiv, yield, and conversion (if available) values for optimum conditions. 
The optimum value is defined as the acid equiv value where the yield is maximised. If there is no significant increase in yield, the acid equiv value is minimised. 
The method takes in the following arguments:
yield_kernel: str, the kernel to be used for the yield dataset (default = first kernel in the dictionary of models)
conv_kernel: str, the kernel to be used for the conversion dataset (default = first kernel in the dictionary of models)
Output: np.array containing the acid equiv, yield, and conversion (if available) values for optimum halogenating conditions


'''

class Halogenation:

    def __init__(self,
                 substrate, 
                 reagent, 
                 data, 
                 ):
        self._substrate = substrate #str - the substrate used in the reaction
        self._reagent = reagent #str - the reagent used in the reaction
        self._data = data #can be any 2D array with 2 or 3 columns: acid equiv, yield, and conversion (optional)

        self.yieldoutputs = {} # initialise a dictionary to store the GPR predictions for yield
        if self.data.shape[1] == 3: # initialise a dictionary to store the GPR predictions for conversion if the data has 3 columns
            self.convoutputs = {}

    def __str__(self):
        return "Data for the halogenation of " + self.substrate + " with " + self.reagent
    
    # Getters and Setters
    @property
    def substrate(self):
        return self._substrate

    @substrate.setter
    def substrate(value):
        if type(value) != str:
            raise TypeError("Substrate must be of dtype str")
        
    @property
    def reagent(self):
        return self._reagent

    @reagent.setter
    def reagent(value):
        if type(value) != str:
            raise TypeError("Reagent must be of dtype str")
        
    @property
    def data(self):
        return np.array(self._data)

    @property
    def acidequiv(self):
        return np.array([float(x[0]) for x in self._data])
    
    @property
    def yieldvalues(self):
        return np.array([float(x[1]) for x in self._data])
    
    @property
    def convvalues(self):
        if self.data.shape[1] == 3:
            return np.array([float(x[2]) for x in self._data])
        else:
            return None


    # The main method use to run the GPR model. Involved using acid equiv with yield and/or conversion values to generate model(s)  
    def gprcalculate(self, 
                      kernel, 
                      **kwargs,
                      ):
        
        # Default values for kwargs
        kernelname = kwargs.get('kernelname', str(kernel))
        scaler = kwargs.get('scaler', RobustScaler()) # Default scaler, generally better at handling outliers than StandardScaler
        height = kwargs.get('height', 5) # Only pick peaks above 5% yield/conversion. Change accordingly
        dset = kwargs.get('dset', 'yield') # Use yield data only by default
       
        X = self.acidequiv.reshape(-1, 1)  # Reshape the acid equiv values for the GPR model
        if dset == 'yield':
            Y = [self.yieldvalues]
        elif dset == 'conv':
            Y = [self.convvalues]
        elif dset == 'both':
            Y = [self.yieldvalues, self.convvalues]
            
        else:
            raise ValueError("dset must be either 'yield', 'conv' or 'both'")

        # Build and run the GPR model
        model = GaussianProcessRegressor(kernel = kernel, n_restarts_optimizer = 7) # Define the GPR model
        pipe = Pipeline([('scaler', scaler), ('model', model)]) # Define the pipeline (scaler + model)
        x = np.linspace(np.min(X.flatten()), np.max(X.flatten()), 1000).reshape(-1, 1) # Define the x values for the prediction. 1000 points are used between the min and max acid equiv values

        for i, y in enumerate(Y): # Loop through yield and conversion for the halogenation reaction data
            pipe.fit(X, y) #fit the model to yield/ conversion data
        
            y_pred, y_pred_std = pipe.predict(x, return_std=True) #predict the yield/ conversion values for all 1000 x values with standard deviation for each datapoint

            model_pred = np.column_stack((x, y_pred))
            model_stdev = np.column_stack((x, y_pred_std))

            # Peak-picking
            peak_index, _ = find_peaks(model_pred[:,1].ravel(), height = height) # Use signal processing to find the peaks in the acid equiv vs yield curve above the specified height. Returns indexes of the maxima
            indexs = [0] + list(peak_index) + [-1] # Add the min and max datapoints also, for cases where the dataset has no maxima (i.e optimum at min or max acid equiv)

            maxima = model_pred[indexs] # Find the acid equiv and yield values at the indexes of maxima


            # Cross validation
            loo = LeaveOneOut() # Use LeaveOneOut cross validation to calculate the mean absolute error for each model
            neg_aes = [] #initialize a list to store negative mean and actual errors

            # Loop through the LeaveOneOut splits
            for train_index, test_index in loo.split(X):
                X_train, X_test = X[train_index], X[test_index]
                y_train, y_test = y[train_index], y[test_index]

                pipe.fit(X_train, y_train) # Run a new model for all LOO splits
                abs_error = -abs(pipe.predict(X_test) - y_test) # Calculate the absolute error for each LOO split
                neg_aes.append(abs_error[0]) # Append the negative absolute error to the list
            
            # Calculate the mean absolute error for all LOO split models
            mae = -mean(neg_aes)

            # Store the model predictions, standard deviations, maxima, and mean absolute error in dictionaries
            if (dset == 'yield' or dset == 'both') and i == 0:
                self.yieldoutputs.update({kernelname : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima, 'mae': mae}})
            else:
                self.convoutputs.update({kernelname : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima, 'mae': mae}})
    
    
    
    # Methods to select the best model for yield and conversion (ie the lowest mean absolute error)
    def best_model_yield(self):
        bestmodel = min([self.yieldoutputs[kernel]['mae'] for kernel in self.yieldoutputs.keys()]) #find the kernel with the lowest mean absolute error
        bestkernel = [kernel for kernel in self.yieldoutputs.keys() if self.yieldoutputs[kernel]['mae'] == bestmodel] #find the kernel name
        return bestkernel[0]
    
    def best_model_conv(self):
        bestmodel = min([self.convoutputs[kernel]['mae'] for kernel in self.convoutputs.keys()]) #find the kernel with the lowest mean absolute error
        bestkernel = [kernel for kernel in self.convoutputs.keys() if self.convoutputs[kernel]['mae'] == bestmodel] #find the kernel name
        return bestkernel[0]



    # Pick the optimum acid equiv with predicted yield and conversion values for specified kernels
    def pickoptimum(self, **kwargs):

        yield_kernel = kwargs.get('yield_kernel') # Use best_model_yield() for optimum across kernels screened (yield)
        conv_kernel = kwargs.get('conv_kernel') # Use best_model_conv() for optimum across kernels screened (conversion)

        # If no kernel is specified, use the first kernel in each dictionary
        if yield_kernel is None:
            try:
                print("No kernel specified for yield dataset. Defaulting to:" + list(self.yieldoutputs.keys())[0])
                yield_kernel = list(self.yieldoutputs.keys())[0]
            except (KeyError, IndexError):
                yield_kernel = None

        if conv_kernel is None:
            try:
                print("No kernel specified for conversion dataset. Defaulting to:" + list(self.yieldoutputs.keys())[0])
                conv_kernel = list(self.convoutputs.keys())[0]
            except (KeyError, IndexError):
                conv_kernel = None

        # Raise error if neither output is available
        if yield_kernel is None and conv_kernel is None:
            raise ValueError("Use self.gprcalculate() first to generate predictions.")

        if yield_kernel:
            # Select best yield maxima (same as before)
            self.optimum = self.yieldoutputs[yield_kernel]['maxima'][0] # Start with the first datapoint in the "maxima" array (0 TFA equiv)
            for i in range(len(self.yieldoutputs[yield_kernel]['maxima']) - 1): # Loop through the maxima to find the optimum acid equiv
                next_max = self.yieldoutputs[yield_kernel]['maxima'][i + 1]
                if self.optimum[1] + 5 < next_max[1]: # If the yield increases by more than 5% between maxima, update the optimum
                    self.optimum = next_max

            # Append the conversion corresponding to the optimum yield
            if conv_kernel and self.convoutputs.get(conv_kernel) is not None:
                try:
                    acid_values = self.yieldoutputs[yield_kernel]['prediction'][:, 0]
                    match_idx = np.where(acid_values == self.optimum[0])[0] # Find the index of the optimum acid equiv in the yield dataset
                    if len(match_idx) > 0:
                        conv_val = self.convoutputs[conv_kernel]['prediction'][match_idx[0]][-1] # Extract the conversion value at the same index
                        self.optimum = np.append(self.optimum, conv_val) # Append the conversion value to the optimum array
                except Exception as e:
                    print("Warning: couldn't extract conversion value:", e) # Print a warning if the conversion value can't be extracted

        elif conv_kernel:
            # If there is no yield, pick optimum based on conversion maxima
            self.optimum = self.convoutputs[conv_kernel]['maxima'][0] # Start with the first datapoint in the "maxima" array (0 TFA equiv)
            for i in range(len(self.convoutputs[conv_kernel]['maxima']) - 1): # Loop through the maxima to find the optimum acid equiv
                next_max = self.convoutputs[conv_kernel]['maxima'][i + 1]
                if self.optimum[1] + 5 < next_max[1]: # If the conversion increases by more than 5% between maxima, update the optimum
                    self.optimum = next_max

        return self.optimum # Return the optimum acid equiv with predicted yield and conversion values

