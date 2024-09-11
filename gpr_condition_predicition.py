import os
import pip
import sys

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.gaussian_process.kernels import RBF, Matern, RationalQuadratic, ExpSineSquared, WhiteKernel
from sklearn.preprocessing import StandardScaler, RobustScaler
from gpr_functions import get_predictions, model_selector, plot_predicitions
from gpr_predictions import Halogenation


#load data

yield_csv_path = input("Enter the path to the yield data: ").strip('"').strip("'")
conv_csv_path = input("Enter the path to the conversion data: ").strip('"').strip("'")

destination = input("Enter the path to the destination folder: ").strip('"').strip("'")

length_scale_bounds = input("Enter the length scale bounds (in the form lower,upper): ")
length_scale_bounds = tuple([float(x) for x in length_scale_bounds.split(',')])

compound_yield_csv = pd.read_csv(yield_csv_path, index_col='Unnamed: 0')
compound_conv_csv = pd.read_csv(conv_csv_path, index_col='Unnamed: 0')

compound_yield= compound_yield_csv.iloc[:,:-1]
compound_conv= compound_conv_csv.iloc[:,:-1]

compound_exp_yield = compound_yield_csv.iloc[:,-1].fillna(0)
compound_exp_conv = compound_conv_csv.iloc[:,-1].fillna(0)

if not os.path.exists(destination + "\compound_plots"):
    os.mkdir(destination + "\compound_plots")


#run the model for each set of data
compound_df = pd.DataFrame(columns=['pred_opt_tfa', 
                            'pred_opt_yield',
                            'pred_opt_conv',
                            'kernel_yield',
                            'kernel_yield_error',
                            'kernel_conv',
                            'kernel_conv_error',
                            'length_scale_bounds',


                           ])

#chlorination predictions
labels = compound_yield.index
for label in labels:

    print("Running predictions for " + label)

    kernels = {'Radial basis function (RBF)': 1.0 * RBF(length_scale=1e0, length_scale_bounds=length_scale_bounds)+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          'Matern (nu = 3/2)': 1.0 * Matern(length_scale=1e0, length_scale_bounds=length_scale_bounds, nu=3/2)+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          'Matern (nu = 5/2)': 1.0 * Matern(length_scale=1e0, length_scale_bounds=length_scale_bounds, nu=5/2)+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          #'Rational quadratic (RQ)': 1.0 * RationalQuadratic(length_scale=1e0, length_scale_bounds=length_scale_bounds),+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          #'Exponential sine squared (ESS)': 1.0 * ExpSineSquared(length_scale=1e0, length_scale_bounds=length_scale_bounds),, periodicity=1.0, periodicity_bounds=length_scale_bounds),+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),),
          }

    substrate = pd.concat([compound_yield.loc[label], compound_conv.loc[label]], axis=1)
    substrate.columns = ['Yield', 'Conversion']
    substrate = np.array(substrate.reset_index())

    compound = Halogenation(label, 'X', substrate)

    for kernel_name, kernel in kernels.items():
        compound.gprcalculate(kernel, dset= 'both', kernelname = kernel_name)
    
    yield_model = compound.best_model_yield()
    #print(yield_model)
    #print(type(yield_model))
    conv_model = compound.best_model_conv()

    optimum_tfa = compound.pickoptimum(yield_kernel = yield_model, 
                                   conv_kernel = conv_model)
    
    #print(optimum_tfa)

    compound_df.loc[label] = [optimum_tfa[0], 
                              optimum_tfa[1], 
                              optimum_tfa[2], 
                              yield_model, 
                              compound.yieldoutputs[yield_model]['mae'], 
                              conv_model, 
                              compound.convoutputs[conv_model]['mae'], 
                              length_scale_bounds]
    #export to csv
    

    #plotting
    

    x = compound.yieldoutputs[yield_model]['prediction'][:,0]
    y = compound.yieldoutputs[yield_model]['prediction'][:,1]

    x_c = compound.convoutputs[conv_model]['prediction'][:,0]
    y_c = compound.convoutputs[conv_model]['prediction'][:,1]

    x_exp = compound.acidequiv
    y_exp = compound.yieldvalues
    y_exp_c = compound.convvalues
    

    fig, ax = plt.subplots(1,2,figsize=(17, 5), gridspec_kw={'width_ratios': [9,10], 'wspace': 0.3})

    ax[0].plot(x,y, zorder = 3, color = 'tab:blue')
    ax[0].plot(x_c, y_c, zorder = 1, color = 'tab:orange')
    ax[0].scatter(optimum_tfa[0], optimum_tfa[1], marker='x', color = 'tab:red', zorder = 5)
    ax[0].scatter(optimum_tfa[0], compound_exp_conv.loc[label], marker='d', color = 'tab:green', zorder = 7)
    ax[0].scatter(x_exp, y_exp, marker='.', zorder = 4, color = 'tab:blue')
    ax[0].scatter(x_exp, y_exp_c, marker='.', zorder = 2, color = 'tab:orange')

    if optimum_tfa[1] > 100:    
        ax[0].set_ylim(0, optimum_tfa[1]+20)
        ax[0].vlines(optimum_tfa[0], colors='tab:red', linestyles='dashed', ymin=0, ymax=optimum_tfa[1]+20, linewidth=0.5, zorder = 6)
    else:
        ax[0].set_ylim(0, 100)
        ax[0].vlines(optimum_tfa[0], colors='tab:red', linestyles='dashed', ymin=0, ymax=100, linewidth=0.5, zorder = 6)
    
    ax[0].set_xlabel('TFA equivalents')
    ax[0].set_ylabel('NMR yield/Conversion (%)')

    ax[0].legend(['NMR yield (GPR)', 'Conversion (GPR)','GPR Optimum', 'Isolated yield'], 
            loc='lower right', 
            bbox_to_anchor=(1, -0.3),
            frameon=False,
            fontsize = 8)
    
    ax[0].text(optimum_tfa[0]+0.2, 
            optimum_tfa[1]+4, 
            str(round(optimum_tfa[0], 1))+' equiv.\n' + str(int(round(optimum_tfa[1], 0))) + "% NMR yield\n"+ str(int(round(compound.pickoptimum(kernel = conv_model)[2], 0))) + "% Conversion", 
            color = 'tab:red')
    
   
    ax[0].text(-2.2, -19, "NMR yield - Kernel: "+ compound.best_model_yield() + " + White" + ', Length scale bounds: ' + str(length_scale_bounds), fontsize=8)
    ax[0].text(-2.2, -23, "Conversion - Kernel: "+ compound.best_model_conv() + " + White" + ', Length scale bounds: ' + str(length_scale_bounds), fontsize=8)
        

    iso_yield = compound_exp_yield.loc[label]
    iso_conv = compound_exp_conv.loc[label]
    best_index = np.argmax(substrate[:,1])
    best_hte = int(substrate[best_index][0])
    hte_conv = substrate[best_index][2]
    gpr_conv = optimum_tfa[2]

    data = {'Best HTE Conversion\n(' + str(best_hte) + ' equiv.)': hte_conv, 'Predicted optimial\nconversion': gpr_conv, 'Scale-up conversion': iso_conv, 'Isolated Yield': iso_yield}
    names = list(data.keys())
    values = list(data.values())

    colors = ['tab:orange', 'tab:red', 'tab:green', 'tab:purple']

    ax[1].barh(names, values, height=0.5, color = colors)
    ax[1].invert_yaxis()
    ax[1].set_xlabel('Yield/Conversion (%)')
    ax[1].set_xlim(0, 100)

    plt.savefig(destination + "\compound_plots\\" + label + "_plot.png")




compound_df.to_csv(destination + "\compound_predictions.csv")