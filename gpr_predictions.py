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
        self._substrate = substrate #str
        self._reagent = reagent #str
        self._data = data #can be any 2D array with 2 or 3 columns: acid equiv, yield, and conversion (optional)

        self.yieldoutputs = {}
        if self.data.shape[1] == 3:
            self.convoutputs = {}

    def __str__(self):
        return "Data for the halogenation of " + self.substrate + " with " + self.reagent
    
    #getters and setters
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




    #method to run the GPR model
    def gprcalculate(self, 
                      kernel, 
                      **kwargs,
                      ):
        
        #default values for kwargs
        kernelname = kwargs.get('kernelname', str(kernel))
        scaler = kwargs.get('scaler', RobustScaler())
        height = kwargs.get('height', 5)
        dset = kwargs.get('dset', 'yield')

       
        X = self.acidequiv.reshape(-1, 1) #reshape the acid equiv values for the GPR model
        if dset == 'yield':
            Y = [self.yieldvalues]
        elif dset == 'conv':
            Y = [self.convvalues]
        elif dset == 'both':
            Y = [self.yieldvalues, self.convvalues]
            
        else:
            raise ValueError("dset must be either 'yield', 'conv' or 'both'")

        #run the GPR model
        model = GaussianProcessRegressor(kernel = kernel, n_restarts_optimizer = 7) #define the GPR model
        pipe = Pipeline([('scaler', scaler), ('model', model)]) #define the pipeline (scaler + model)
        x = np.linspace(np.min(X.flatten()), np.max(X.flatten()), 1000).reshape(-1, 1) #define the x values for the prediction. 1000 points are used between the min and max acid equiv values

        for i, y in enumerate(Y): #loop through the datasets (yield and conversion)
            pipe.fit(X, y) #fit the model to yield/ conversion data
        
            y_pred, y_pred_std = pipe.predict(x, return_std=True) #predict the yield/ conversion values for all 1000 x values with standard deviation for each datapoint

            model_pred = np.column_stack((x, y_pred))
            model_stdev = np.column_stack((x, y_pred_std))

            #find the maxima
            peak_index, _ = find_peaks(model_pred[:,1].ravel(), height = height) #use some signal processing to find the peaks in the acid equiv vs yield curve above the specified height. Returns indexes of the maxima
            indexs = [0] + list(peak_index) + [-1] #add the min and max datapoints also, for cases where the dataset has no maxima (optimum at min or max acid equiv)

            maxima = model_pred[indexs] #find the acid equiv and yield values at the indexes of maxima


            #perfrom cross validation on each model
            loo = LeaveOneOut() 

            #initialize a list to store negative mean and actual errors
            neg_aes = []

            #loop through the LeaveOneOut splits
            for train_index, test_index in loo.split(X):
                X_train, X_test = X[train_index], X[test_index]
                y_train, y_test = y[train_index], y[test_index]

                pipe.fit(X_train, y_train) #run a new model for all LOO splits
                abs_error = -abs(pipe.predict(X_test) - y_test)
                neg_aes.append(abs_error[0])
            
            #calculate the mean absolute error for all LOO split models
            mae = -mean(neg_aes)


            if (dset == 'yield' or dset == 'both') and i == 0:
                self.yieldoutputs.update({kernelname : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima, 'mae': mae}})
            else:
                self.convoutputs.update({kernelname : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima, 'mae': mae}})
    
    
    
    #select the best model for yield and conversion (ie the best kernel)
    def best_model_yield(self):
        bestmodel = min([self.yieldoutputs[kernel]['mae'] for kernel in self.yieldoutputs.keys()]) #find the kernel with the lowest mean absolute error
        bestkernel = [kernel for kernel in self.yieldoutputs.keys() if self.yieldoutputs[kernel]['mae'] == bestmodel] #find the kernel name
        return bestkernel[0]
    
    def best_model_conv(self):
        bestmodel = min([self.convoutputs[kernel]['mae'] for kernel in self.convoutputs.keys()]) #find the kernel with the lowest mean absolute error
        bestkernel = [kernel for kernel in self.convoutputs.keys() if self.convoutputs[kernel]['mae'] == bestmodel] #find the kernel name
        return bestkernel[0]



    #pick the optimum condnitions for the reaction
    def pickoptimum(self,
                    **kwargs,
                    ):
        
        #ensure the GPR model has been run before picking the optimum conditions
        try:
            yield_kernel = kwargs.get('yield_kernel', list(self.yieldoutputs.keys())[0])
            conv_kernel = kwargs.get('conv_kernel', list(self.convoutputs.keys())[0])
        
        except:
            raise ValueError("Run .gprcalculate() first to generate predictions") #raise an error if the GPR model has not been run
        
        
        self.optimum = self.yieldoutputs[yield_kernel]['maxima'][0] #initialise the optimum value as the first maxima (ie the min acid equiv value)
        for i in range(len(self.yieldoutputs[yield_kernel]['maxima'])-1): #loop through the maxima found in the acid/yield curve
            if self.optimum[1] + 5 < self.yieldoutputs[yield_kernel]['maxima'][i+1][1]: #if there is a significant increase in yield (+5%) for subsiquent maxima.... 
                self.optimum = self.yieldoutputs[yield_kernel]['maxima'][i+1] #chainge the optimum value to the acid equiv value at this maxima
        
        #find corresponding conversion to the YIELD maxima
        if self.convoutputs[conv_kernel] != None:
            convindex = np.where(self.yieldoutputs[yield_kernel]['prediction'] == self.optimum)
            conv = self.convoutputs[conv_kernel]['prediction'][convindex[0]][0][-1]
            self.optimum = np.append(self.optimum, conv)
        
        return self.optimum #return the optimum acid equiv with predicted yield and conversion values

