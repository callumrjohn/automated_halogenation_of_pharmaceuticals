import os
import pip
import sys

#check if the user has the correct packages installed
'''if 'sklearn' not in sys.modules:
    sk_install = input('sklearn not installed. Install? (y/n): ')
    sk_install = sk_install[0].lower()
    while sk_install not in ['y', 'n']:
        sk_install = input('Please enter y or n: ')
        sk_install = sk_install[0].lower()
    if sk_install == 'y':
        pip.main(['install', 'sklearn'])
    else:
        print('Exiting program...')
        exit()

if 'pandas' not in sys.modules:
    pd_install = input('pandas not installed. Install? (y/n): ')
    pd_install = pd_install[0].lower()
    while pd_install not in ['y', 'n']:
        pd_install = input('Please enter y or n: ')
        pd_install = pd_install[0].lower()
    if pd_install == 'y':
        pip.main(['install', 'pandas'])
    else:
        print('Exiting program...')
        exit()'''

import pandas as pd
from sklearn.gaussian_process.kernels import RBF, Matern, RationalQuadratic, ExpSineSquared, WhiteKernel
from sklearn.preprocessing import StandardScaler, RobustScaler
from gpr_functions import get_predictions, model_selector, plot_predicitions

#import kernels from sklearn


'''import the data. This should be a .csv file
with the first row containing an independent continuous 
variable, the first column containing labels of compounds,
conditions etc. and the rest of the data consisting of
numberical values'''

try:
    print("Make sure your data is in the correct format (see README.md)")
    data = input('Enter the path of the file containing the data (.csv): ')

except(FileNotFoundError, PermissionError):
    data = False

import_error_count = 0

while not os.path.exists(data) and not data.endswith('.csv'):
    import_error_count += 1

    if import_error_count >= 6: # if the user has tried to import the data 6 times, exit the program
        print('Exiting program, too many tries...')
        exit()

    print('Please enter a valid file path')


    if import_error_count == 2:
        print('Hint: Double check the file path...')

    if import_error_count == 3:
        print('Hint: Check to see if the file is in the correct format...')

    if import_error_count == 4:
        print('Hint: If your file path has spaces in it, try putting it all in quotes...')
    

    data = input('Enter the path of the file containing the data (.csv): ')


#import the data as a pandas dataframe
print('Importing data...')

df = pd.read_csv(data, index_col = 0)

#final sanity check for the data - returns the shape of the df
data_shape_check = input('Data imported successfully! The shape of the data is: ' + str(df.shape) + '. Does this sound right? (y/n): ')
data_shape_check = data_shape_check[0].lower()
while data_shape_check not in ['y', 'n']:
    data_shape_check = input('Please enter y or n: ')
    data_shape_check = data_shape_check[0].lower()


if data_shape_check == 'n':
    print('Exiting program...')
    exit()
else:
    print('Continuing...')


#ask the user which kernels they want to use
print('Select which kernel(s) would you like to use? (consider computational costs): ')
print('1. Radial basis function (RBF) - recommended for general use')
print('2. Matern (nu = 3/2)')
print('3. Matern (nu = 5/2)')
print('4. Rational quadratic (RQ)')
print('5. Exponential sine squared (ESS) - recommended for periodic data')
print('6. All of the above')

model_numbers = input('')
if '6' in model_numbers:
    model_numbers = '1 2 3 4 5'

if ',' in model_numbers:
    model_numbers = model_numbers.split(',')

if ' ' in model_numbers:
    model_numbers = model_numbers.split(' ')

kernels = {'1' : ('Radial basis function (RBF)', 1.0 * RBF(length_scale=1e0, length_scale_bounds=(1e-1, 1e1))),
          '2' : ('Matern (nu = 3/2)', 1.0 * Matern(length_scale=1e0, length_scale_bounds=(1e-1, 1e1), nu=3/2)),
          '3' : ('Matern (nu = 5/2)', 1.0 * Matern(length_scale=1e0, length_scale_bounds=(1e-1, 1e1), nu=5/2)),
          '4' : ('Rational quadratic (RQ)', 1.0 * RationalQuadratic(length_scale=1e0, length_scale_bounds=(1e-1, 1e1))),
          '5' : ('Exponential sine squared (ESS)', 1.0 * ExpSineSquared(length_scale=1e0, length_scale_bounds=(1e-1, 1e1), periodicity=1.0, periodicity_bounds=(1e-1, 1e1)))
          }

selected_kernels = {kernels[model][0] : kernels[model][1] for model in model_numbers}


#ask about the noise in the data (whether to use White Kernel also)

noise_yn = input('Is there likely to be some noise in the data (if unsure, assume there is)? (y/n): ')
noise_yn = noise_yn[0].lower()

while noise_yn not in ['y', 'n']:
    noise_yn = input('Please enter y or n: ')


if noise_yn == 'y':
    print('Added White Kernel to all kernels...')

    for model in selected_kernels:
        selected_kernels[model] += (WhiteKernel(noise_level=1e0, noise_level_bounds=(1e1, 1e1)))
else:
    print('White kernel not added to kernels...')

#run the model for each set of data
plot_data = []
model_selections = pd.DataFrame(columns = ['best_model', 'mae(loo)','pred_opt_condition','pred_max_yield'])    

for index, row in df.iterrows():
    print('Running model for ' + str(index + '...'))

    row_trim = row.dropna() #discard any missing values
    #x = row.index.astype(float).reshape(-1, 1)
    x = row.index.values.astype(float).reshape(-1, 1)
    y = row.values
    model_results = get_predictions(X = x, y = y, kernels = selected_kernels, scaler = RobustScaler())
    #print(model_results)
    best_model_results = model_selector(model_results)



    plot_data.append({'compound' : index} | best_model_results)
    model_selections.loc[index] = [best_model_results['kernel'], best_model_results['mae'], best_model_results['optimum'][0], best_model_results['optimum'][1]]

plot_predicitions(plot_data, 'TFA equivalents','NMR Yield (%)')

model_selections.to_csv('model_stats.csv')







    


