import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import math
from statistics import mean

from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_validate, LeaveOneOut
from scipy.signal import find_peaks
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import DotProduct, WhiteKernel, RBF, Matern, ConstantKernel as C, RationalQuadratic, ExpSineSquared


'''Function to return a set of predicitions, with errors, 
for a set of compound data using a dictionary of kernels.
Compound data should be in pandas format, kernels must be
a dictionary of kernels...'''

# returns mean absolute error and mean squared error
def custom_scoring(tfa_pred, tfa_pred_loo):
    return (tfa_pred - tfa_pred_loo)**2, tfa_pred - tfa_pred_loo


def get_predictions(X,
                    y, 
                    kernels, 
                    scaler = RobustScaler()
                    ):

    results = []
    print(X)
    print(y)
    x = np.linspace(np.min(X.flatten()), np.max(X.flatten()), 1000).reshape(-1, 1)

    for kernel_name, kernel in kernels.items():

        model = GaussianProcessRegressor(kernel = kernel, n_restarts_optimizer = 7)
        pipe = Pipeline([('scaler', scaler), ('model', model)])
        pipe.fit(X, y)
        y_pred, y_pred_std = pipe.predict(x, return_std=True)
       

        # Calculate maximum peak height

        peak_index, _ = find_peaks(y_pred.ravel(), height = 5)
        indexs = [0] + list(peak_index) + [-1]
        
        index_values = [y_pred[x] for x in indexs]

        #index_values[0] = index_values[0] + 5 # if there is no significant improvement upon adition of reagent, choose the lowest value.

        peak_index = index_values.index(max(index_values))

        x_peak, y_peak = x[peak_index], y_pred[peak_index]
            

        #perfrom cross validation on each model    
        loo = LeaveOneOut()

        # Initialize a list to store negative mean and actual errors
        neg_aes = []

        # Loop through the LeaveOneOut splits
        for train_index, test_index in loo.split(X):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]

            pipe.fit(X_train, y_train)
            abs_error = -abs(pipe.predict(X_test) - y_test)
            neg_aes.append(abs_error[0])
        
        print(neg_aes)
        mae = -mean(neg_aes)



        model_results = {'kernel' : kernel_name, 'optimum': (x_peak, y_peak), 'predictions' : (x.flatten(), y_pred), 'pred_std' : y_pred_std, 'mae' : mae}

        results.append(model_results)
            
    return results



def model_selector(model_results):
    print(model_results[0]['mae'])
    best_model_dic = min(model_results, key = lambda x: x['mae'], default=None)
    #best_model = best_model_dic.values()[0]
    #best_model.update({'kernel_name' : best_model_dic.keys()[0]})
    return best_model_dic


'''Plot each set of predictions'''
def plot_predicitions(data,  # list of dictionaries
                      xlabel, 
                      ylabel):
    
    #no_comp = len(set([x['compound'].split(' ')[0] for x in data])) #get the number of starting materials, so the dimentions are correct when plotting multiple products

    color_count = 0
    colors = ['blue','red','green']

    for i, comp_data in enumerate(data):

        x = comp_data['predictions'][0]
        y = comp_data['predictions'][1]
        stdev = comp_data['pred_std']

        plt.plot(x, y, color = colors[color_count])

        # Calculate the lower and upper bounds for the confidence interval
        lower_bound = y - 1.9600 * stdev
        upper_bound = y + 1.9600 * stdev

        # Plot the shaded area
        plt.fill_between(x, lower_bound, upper_bound, alpha=0.3, facecolor='blue', edgecolor='None')

        if i == len(data) - 1 or data[i]['compound'].split(' ')[0] != data[i+1]['compound'].split(' ')[0]:
            plt.title(comp_data['compound'])
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.savefig(comp_data['compound'] + '_plot.png')
            plt.clf()
            color_count = 0

        else:
            color_count += 1
        


