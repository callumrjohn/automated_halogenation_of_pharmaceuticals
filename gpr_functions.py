import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate, LeaveOneOut
from scipy.signal import find_peaks
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel, RBF, Matern, ConstantKernel as C, RationalQuadratic, ExpSineSquared


'''Function to return a set of predicitions, with errors, 
for a set of compound data using a dictionary of models.
Compound data should be in pandas format, models must be
a dictionary of models...'''

# returns mean absolute error and mean squared error
def custom_scoring(tfa_pred, tfa_pred_loo):
    return (tfa_pred - tfa_pred_loo)**2, tfa_pred - tfa_pred_loo


def get_predictions(comp_data, 
                    models, 
                    scaler = RobustScalar()
                    ):
    
    model = {'GP (Matern 5/2 + White)' : GaussianProcessRegressor(
                kernel = 1.0 * Matern(length_scale=1e0, length_scale_bounds=(1e-1, 1e1), nu=3/2) + WhiteKernel(
                noise_level=1e0, noise_level_bounds=(1e1, 1e1)), n_restarts_optimizer = 10
            ),
            'GP (RBF + White)' : GaussianProcessRegressor(
                kernel = 1.0 * RBF(length_scale=1e0, length_scale_bounds=(1e-1, 1e1)) + WhiteKernel(
                    noise_level=1e0, noise_level_bounds=(1e1, 1e1)), n_restarts_optimizer = 10
            ),
            
                    }

    obs_data = {'tfa_equiv': np.array([float(i) for i in list(comp_data.columns)]), 'obs':{}}
    prediction_data = {}
    score_data = {}
    sigma_data = {}
    opt_tfa = {}

    X = obs_data['tfa_equiv'].reshape(-1, 1)
    x = np.linspace(min(X), max(X), 1000).reshape(-1, 1)

    #scoring = {'Neg MAE': 'neg_mean_absolute_error', 'Neg MSE': 'neg_mean_squared_error'}

    for i, product in enumerate(comp_data.iterrows()):

        product_obs = np.array(product[1:])
        obs_data['obs'].update({'product'+str(i) : product_obs}) # extend the dictionary for each product
        prediction_data.update({'product'+str(i) : {}})
        score_data.update({'product'+str(i) : {}})
        sigma_data.update({'product'+str(i) : {}})
        opt_tfa.update({'product'+str(i) : {}})

        y = product_obs.reshape(-1, 1)

        for name, model in models.items():

            pipe = Pipeline([('scaler', scaler), ('model', model)])
            pipe.fit(X, y)

            try:
                y_pred, sigma = pipe.predict(x, return_std=True)
            except:
                y_pred = pipe.predict(x)

            # Calculate maximum peak height

            index, _ = find_peaks(y_pred.ravel(), height = 5)
            index = [0] + list(index) + [-1]
            #print(index)
            
            #try:
            tfa_pred = float(x[index][0]), float(y_pred[index][0])

            for j in range(1, len(index)):
            
                if y_pred[index][j] > y_pred[index][j-1] + 5:
                    tfa_pred = float(x[index][j]), float(y_pred[index][j])
                    
                        

            #except:
             #   if y_pred[0] + 5 >= y_pred[-1]:
              #      tfa_pred = float(X[0]), float(y_pred[0])
#
 #               else:
  #                  tfa_pred = float(X[-1]), float(y_pred[-1])
            
            #print(tfa_pred)

            loo = LeaveOneOut()

            # Initialize a list to store negative mean and actual errors
            neg_aes = []
            neg_ses = []

            # Loop through the LeaveOneOut splits
            for train_index, test_index in loo.split(X):
                X_train, _ = X[train_index], X[test_index]
                y_train, _ = y[train_index], y[test_index]
 
                pipe.fit(X_train, y_train)
                y_pred_loo = pipe.predict(x)

                # Calculate maximum peak height
                index, _ = find_peaks(y_pred_loo.ravel(), height = 5)
                index = [0] + list(index) + [-1]
               
                
                #try:
                tfa_pred_loo = float(x[index][0])

                for j in range(1, len(index)):
                
                    if y_pred_loo[index][j] > y_pred_loo[index][j-1] + 5:
                        tfa_pred_loo = float(x[index][j])
                        
                            

                #except:
                 #   if y_pred_loo[0] + 5 >= y_pred_loo[-1]:
                  #      tfa_pred_loo = float(X[0])
#
 #                   else:
  #                      tfa_pred_loo = float(X[-1])

            

                # Calculate custom score (MSE)
                se, ae = custom_scoring(tfa_pred[0], tfa_pred_loo)
                neg_ses.append(float(-abs(se)))
                neg_aes.append(float(-abs(ae)))
                #print(neg_aes)

            # Calculate the average custom score
            mae = abs(np.mean(neg_aes))
            mse = abs(np.mean(neg_ses))
            
            
            scores = {'MAE' : mae, 'MSE' : mse}
            
            
            prediction_data['product'+str(i)].update({name : y_pred})
            score_data['product'+str(i)].update({name : scores})
            if 'sigma' in locals():
                sigma_data['product'+str(i)].update({name : sigma})
                del sigma
            opt_tfa['product'+str(i)].update({name : tfa_pred})

            
            
            
    return obs_data, prediction_data, score_data, sigma_data , opt_tfa
