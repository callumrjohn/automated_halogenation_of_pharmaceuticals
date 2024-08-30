import numpy as np
from statistics import mean
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import LeaveOneOut
from scipy.signal import find_peaks

class Halogenation:

    def __init__(self, 
                 substrate, 
                 reagent, 
                 data, 
                 ):
        self._substrate = substrate
        self._reagent = reagent
        self._data = data

        self.yieldoutputs = {}
        if self.data.shape[1] == 3:
            self.convoutputs = {}

    def __str__(self):
        return "Data for the halogenation of " + self.substrate + " with " + self.reagent
    

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


    def gprcalculate(self, 
                      kernel, 
                      **kwargs,
                      ):
        
        #default values for kwargs
        kernelname = kwargs.get('kernelname', str(kernel))
        scaler = kwargs.get('scaler', RobustScaler())
        height = kwargs.get('height', 5)
        dset = kwargs.get('dset', 'yield')

       
        X = self.acidequiv.reshape(-1, 1)
        if dset == 'yield':
            Y = [self.yieldvalues]
        elif dset == 'conv':
            Y = [self.convvalues]
        elif dset == 'both':
            Y = [self.yieldvalues, self.convvalues]
            
        else:
            raise ValueError("dset must be either 'yield', 'conv' or 'both'")

        #run the GPR model
        model = GaussianProcessRegressor(kernel = kernel, n_restarts_optimizer = 7)
        pipe = Pipeline([('scaler', scaler), ('model', model)])
        x = np.linspace(np.min(X.flatten()), np.max(X.flatten()), 1000).reshape(-1, 1)

        for i, y in enumerate(Y):
            pipe.fit(X, y)
        
            y_pred, y_pred_std = pipe.predict(x, return_std=True)

            model_pred = np.column_stack((x, y_pred))
            model_stdev = np.column_stack((x, y_pred_std))

            #find the maxima
            peak_index, _ = find_peaks(model_pred[:,1].ravel(), height = height)
            indexs = [0] + list(peak_index) + [-1]

            maxima = model_pred[indexs]


            #perfrom cross validation on each model
            loo = LeaveOneOut()

            #initialize a list to store negative mean and actual errors
            neg_aes = []

            #loop through the LeaveOneOut splits
            for train_index, test_index in loo.split(X):
                X_train, X_test = X[train_index], X[test_index]
                y_train, y_test = y[train_index], y[test_index]

                pipe.fit(X_train, y_train)
                abs_error = -abs(pipe.predict(X_test) - y_test)
                neg_aes.append(abs_error[0])
            
            #print(neg_aes)
            mae = -mean(neg_aes)


            if (dset == 'yield' or dset == 'both') and i == 0:
                self.yieldoutputs.update({kernelname : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima, 'mae': mae}})
            else:
                self.convoutputs.update({kernelname : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima, 'mae': mae}})
    
    #find the best model for yield and conversion
    def best_model_yield(self):
        bestmodel = min([self.yieldoutputs[kernel]['mae'] for kernel in self.yieldoutputs.keys()])
        bestkernel = [kernel for kernel in self.yieldoutputs.keys() if self.yieldoutputs[kernel]['mae'] == bestmodel]
        return bestkernel[0]
    
    def best_model_conv(self):
        bestmodel = min([self.convoutputs[kernel]['mae'] for kernel in self.convoutputs.keys()])
        bestkernel = [kernel for kernel in self.convoutputs.keys() if self.convoutputs[kernel]['mae'] == bestmodel]
        return bestkernel[0]

    #pick the optimum 
    def pickoptimum(self,
                    **kwargs,
                    ):
        
        try:
            yield_kernel = kwargs.get('yield_kernel', list(self.yieldoutputs.keys())[0])
            conv_kernel = kwargs.get('conv_kernel', list(self.convoutputs.keys())[0])
        
        except:
            raise ValueError("Run .gprcalculate() first to generate predictions")
        
        self.optimum = self.yieldoutputs[yield_kernel]['maxima'][0]
        for i in range(len(self.yieldoutputs[yield_kernel]['maxima'])-1):
            if self.yieldoutputs[yield_kernel]['maxima'][i][1] + 5 < self.yieldoutputs[yield_kernel]['maxima'][i+1][1]: #if there is no significant increase in yield, minimise acid equiv
                self.optimum = self.yieldoutputs[yield_kernel]['maxima'][i+1]
        
        #find corresponding conversion
        if self.convoutputs[conv_kernel] != None:
            convindex = np.where(self.yieldoutputs[yield_kernel]['prediction'] == self.optimum)
            conv = self.convoutputs[conv_kernel]['prediction'][convindex[0]][0][-1]
            self.optimum = np.append(self.optimum, conv)
        
        return self.optimum

