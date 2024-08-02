import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler
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
    def acid_equiv(self):
        return np.array([x[0] for x in self.data])

    
    @property
    def yieldvalues(self):
        return np.array([x[1] for x in self.data])
    
    @property
    def convvalues(self):
        if self.data.shape[1] == 3:
            return np.array([x[2] for x in self.data])
        else:
            return None


    def gprcalculate(self, 
                      kernel, 
                      scaler = RobustScaler(),
                      height = 5,
                      dset = 'yield',
                      ):
        #run the GPR model
        X = self.acid_equiv.reshape(-1, 1)
        if dset == 'yield':
            Y = [self.yieldvalues]
        elif dset == 'conv':
            Y = [self.convvalues]
        elif dset == 'both':
            Y = [self.yieldvalues, self.convvalues]
            
        else:
            raise ValueError("dset must be either 'yield', 'conv' or 'both'")

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

            if (dset == 'yield' or dset == 'both') and i == 0:
                self.yieldoutputs.update({model.kernel_ : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima}})
            else:
                self.convoutputs.update({model.kernel_ : {'prediction': model_pred, 'stdevs': model_stdev, 'maxima': maxima}})


    def pickoptimum(self,
                    kernel,
                    ):
        
        self.optimum = kernel['maxima'][0]
        for i in range(len(kernel['maxima'])-1):
            if kernel['maxima'][i][1] + 5 < kernel['maxima'][i+1][1]: #if there is no significant increase in yield, minimise acid equiv
                self.optimum = kernel['maxima'][i+1]
        
        #find corresponding conversion
        if self.convoutputs[kernel] != None:
            convindex = np.where(self.yieldoutputs[kernel]['prediction'] == self.optimum)
            conv = self.convoutputs[kernel]['prediction'][convindex[0]]
            self.optimum = np.column_stack((self.optimum, conv))
        
        return self.optimum

