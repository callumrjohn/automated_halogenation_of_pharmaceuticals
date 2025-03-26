import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.gaussian_process.kernels import RBF, Matern, RationalQuadratic, ExpSineSquared, WhiteKernel
from gpr_predictions import Halogenation
import warnings

warnings.filterwarnings("ignore") # Ignore convergence warnings when running the GPR models


# load data and set up parameters based on user input

yield_csv_path = input("Enter the path to the yield data: ").strip()
conv_csv_path = input("Enter the path to the conversion data: ").strip()

yield_csv_path = yield_csv_path.strip('"').strip("'")  # Remove extra quotes if present
conv_csv_path = conv_csv_path.strip('"').strip("'")  # Remove extra quotes if present

destination = input("Enter the path to the destination folder: ").strip()

length_scale_bounds = input("Enter the length scale bounds in the form lower,upper (default: 0.1,10): ").strip()
length_scale_bounds = tuple([float(x) for x in length_scale_bounds.split(',')])

if len(length_scale_bounds) != 2: # Check if the user has entered valid length scale bounds
    print("Invalid length scale bounds. Defaulting to 0.1,10")
    length_scale_bounds = (0.1, 10)

try: # Check if the files exist
    compound_yield_csv = pd.read_csv(yield_csv_path, index_col='Unnamed: 0')
    compound_conv_csv = pd.read_csv(conv_csv_path, index_col='Unnamed: 0')
except FileNotFoundError as e:
    print(f"Error: {e}")
    sys.exit(1) # Exit if the files do not exist

if compound_yield_csv.index.all() != compound_conv_csv.index.all(): # Check if substrates of the yield and conversion data files match
    print("Error: The indices of the yield and conversion data do not match")
    sys.exit(1) # Exit if the substrates do not match accross yield and conversion values

# seperate HTE data from experimental values - comment out all lines if .csv only contians HTE data
compound_yield= compound_yield_csv.iloc[:,:-1]
compound_conv= compound_conv_csv.iloc[:,:-1]
compound_exp_yield = compound_yield_csv.iloc[:,-1].fillna(0)
compound_exp_conv = compound_conv_csv.iloc[:,-1].fillna(0)

if not os.path.exists(os.path.join(destination, "compound_plots")): # Create a folder to store the plots
    os.mkdir(os.path.join(destination, "compound_plots"))


#define kernels
kernels = {'RBF': 1.0 * RBF(length_scale=1e0, length_scale_bounds=length_scale_bounds)+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          'Matern (nu = 3/2)': 1.0 * Matern(length_scale=1e0, length_scale_bounds=length_scale_bounds, nu=3/2)+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          'Matern (nu = 5/2)': 1.0 * Matern(length_scale=1e0, length_scale_bounds=length_scale_bounds, nu=5/2)+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          #'Rational quadratic (RQ)': 1.0 * RationalQuadratic(length_scale=1e0, length_scale_bounds=length_scale_bounds),+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),
          #'Exponential sine squared (ESS)': 1.0 * ExpSineSquared(length_scale=1e0, length_scale_bounds=length_scale_bounds),, periodicity=1.0, periodicity_bounds=length_scale_bounds),+ WhiteKernel(noise_level=1e0, noise_level_bounds=length_scale_bounds),),
          #UNCOMMENT THE ABOVE LINES TO USE OTHER KERNELS (see README for more information)
          }


# initialise dataframe to store predictions
compound_df = pd.DataFrame(columns=['pred_opt_tfa', 
                            'pred_opt_yield',
                            'pred_opt_conv',
                            'kernel_yield',
                            'kernel_yield_error',
                            'kernel_conv',
                            'kernel_conv_error',
                            'length_scale_bounds',
                           ])

# initialise lists to store GPR predictions for csv export
gpr_predictions_yield = []
gpr_predictions_conv = []

# predictions
substrates = compound_yield.index

for label in substrates: # Iterate through the substrates, run predictions and plot the data


    # RUN THE MODEL

    print("Running predictions for " + label)

    substrate = pd.concat([compound_yield.loc[label], compound_conv.loc[label]], axis=1)
    substrate.columns = ['Yield', 'Conversion']
    substrate = np.array(substrate.reset_index())

    compound = Halogenation(label, 'X', substrate) # Initialise the Halogenation class

    for kernel_name, kernel in kernels.items(): # Iterate through the kernels and calculate the GPR predictions
        compound.gprcalculate(kernel, dset= 'both', kernelname = kernel_name) 
    
    yield_model = compound.best_model_yield() # Get the best kernel for yield
    conv_model = compound.best_model_conv() # Get the best kernel for conversion

    optimum_tfa = compound.pickoptimum(yield_kernel = yield_model, # Get the optimum TFA, yield, and conversion values using the best kernels
                                   conv_kernel = conv_model)
    
    #print(optimum_tfa)

    # append GPR data to dataframe
    compound_df.loc[label] = [optimum_tfa[0], # optimum TFA
                              optimum_tfa[1], # optimum yield
                              optimum_tfa[2], # optimum conversion
                              yield_model, # best kernel (lowest MAE) for yield
                              compound.yieldoutputs[yield_model]['mae'], # MAE values for all yield predictions 
                              conv_model, # best kernel (lowest MAE) for conversion
                              compound.convoutputs[conv_model]['mae'], # MAE values for all conversion predictions
                              length_scale_bounds] # length scale bounds

    
    # PLOT THE DATA

    # GPR predictions
    x = compound.yieldoutputs[yield_model]['prediction'][:,0]
    y = compound.yieldoutputs[yield_model]['prediction'][:,1]

    x_c = compound.convoutputs[conv_model]['prediction'][:,0]
    y_c = compound.convoutputs[conv_model]['prediction'][:,1]

    gpr_predictions_yield.append(y)
    gpr_predictions_conv.append(y_c)

    # experimental data
    x_exp = compound.acidequiv
    y_exp = compound.yieldvalues
    y_exp_c = compound.convvalues


    # plot a graph of the GPR predictions and experimental yield and conversion data for each halogenation reactions, inlcuding the optimum TFA
    fig, ax = plt.subplots(1,2,figsize=(17, 5), gridspec_kw={'width_ratios': [1,1], 'wspace': 0.3})

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
    
    #ax[0].set_title(f"Predictions for {label}")
    ax[0].set_xlabel('TFA equivalents')
    ax[0].set_ylabel('Yield/Conversion (%)')

    ax[0].legend(['NMR yield (GPR)', 'Conversion (GPR)','GPR Optimum', 'Isolated yield'], 
            loc='lower right', 
            bbox_to_anchor=(1.05, -0.3),
            frameon=False,
            fontsize = 8)
    
    ax[0].text(optimum_tfa[0]+0.2, 
            optimum_tfa[1]+4, 
            str(round(optimum_tfa[0], 1))+' equiv.\n' + str(int(round(optimum_tfa[1], 0))) + "% NMR yield\n"+ str(int(round(optimum_tfa[2], 0))) + "% Conversion", 
            color = 'tab:red')
    
   
    ax[0].text(-2.5, -19, "NMR yield - Kernel: "+ compound.best_model_yield() + " + White" + ', Length scale bounds: ' + str(length_scale_bounds), fontsize=8)
    ax[0].text(-2.5, -23, "Conversion - Kernel: "+ compound.best_model_conv() + " + White" + ', Length scale bounds: ' + str(length_scale_bounds), fontsize=8)
        

    # plot a bar graph of the best HTE conversion, predicted optimal conversion, scale-up conversion, and isolated yield for each halogenation reaction
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


    # save the plot to the destination folder
    plot_filename = os.path.join(destination, "compound_plots", f"{label}_plot.png")
    plt.savefig(plot_filename, bbox_inches='tight')



#export information on optimums, kernels, and yield/conversion responses to csv
gpr_predictions_yield_df = pd.DataFrame(gpr_predictions_yield, columns = x, index=substrates)
gpr_predictions_conv_df = pd.DataFrame(gpr_predictions_conv, columns = x, index=substrates)

compound_df_file = os.path.join(destination, "compound_predictions.csv")
gpr_predictions_yield_file = os.path.join(destination, "gpr_predictions_yield.csv")
gpr_predictions_conv_file = os.path.join(destination, "gpr_predictions_conv.csv")

compound_df.to_csv(compound_df_file)
gpr_predictions_yield_df.to_csv(gpr_predictions_yield_file)
gpr_predictions_conv_df.to_csv(gpr_predictions_conv_file)
