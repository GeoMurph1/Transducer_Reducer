# -*- coding: utf-8 -*-
"""
Created on Mon Dec 03 14:54:08 2018

@author: Michael Murphy

CHANGE LOG: 
"""
# This script resamples time series data to a specified interval, aggregating by the median or mean, plots data, and writes output csv file.
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import glob
from datetime import date
import numpy as np

####### USER SELECTED VARS ####################################################
ver ='01a'

###############################################################################
today1 = str(date.today())
# Read and append single or multiple transducer files into a single DataFrame
path= os.getcwd()
filenames = glob.glob(path + "/*.xlsx")

plots = '_'.join(["Transducer","Data", "Plots", today1, ver]) 

# Set new directory for plots if does not exist:
if os.path.exists(plots) == False:
    os.mkdir(plots)

# Instantiate pandas DataFrame, set date variables for plots
df_append =pd.DataFrame()
days = mdates.DayLocator()

# Define outlier filtering function:
def outlier_filter(df, thrsh, rng, lim):
    """"Calculate absolute value of difference for n steps in range; replace outliers > threshold with NaN, then linearly interpolate new values. \n
    Takes inputs of pandas DataFrame (df), threshold change (thrsh), steps range (rng), and limit (lim)"""
    for n in np.arange(rng)*-1:
        df['Diff'] = df.WaterLevel.diff(periods = n)
        df['WaterLevel'].mask(df.Diff.abs() > thrsh, np.NaN, inplace = True)
        df['WaterLevel'] = df['WaterLevel'].interpolate(method='linear', limit=lim)
os.chdir(plots)
for f in filenames:
    df = pd.read_excel(f,  infer_datetime_format=True, encoding='utf-8')
    date_ = df['TimeStamp']
    flow_datetimes = pd.to_datetime(date_, infer_datetime_format= True)
    df['TimeStamp'] = flow_datetimes
    interval = '15T'
    df['Location'] = df['MonitoringPoint']
    location = df['MonitoringPoint'].unique().item()
    df = df.dropna(axis=0, subset=['WaterLevel'])
    
    # Filter outliers with defined function
    outlier_filter(df, 0.75, 20, 20)
    
    #location = f[47:54] # Directory-dependent; fix with regex? change to count from end of file temporarily
    df_resamp = df.resample(interval, on='TimeStamp').mean()
    df_resamp.reset_index(inplace=True)
    df_resamp["Location"] = location
    df_resamp = df_resamp[['Location', 'TimeStamp', 'WaterLevel']]
    df_resamp.dropna(inplace=True)
    df_resamp.reset_index(drop=True)

    print(df_resamp.head())
    print(df_resamp.shape)
    today = str(date.today())
    writer = pd.ExcelWriter( location + '_' +  'resamp_on_' + interval + '_mean' + '_'+  today +'.xls')
    df_resamp.to_excel(writer, 'Sheet1' )
    writer.save()
    
    fig = plt.figure()
    fig.set_figheight(8.5)
    fig.set_figwidth(11)
    plt.plot(df_resamp['TimeStamp'], df_resamp['WaterLevel'])
    '''Turn on to reverse y-axis for plotting DTW'''
    ax= plt.axis()
    plt.axis((ax[0], ax[1], ax[3], ax[2]))
    
    plt.minorticks_on()
    plt.xticks(rotation=45)
    plt.xlabel('Date')
    plt.ylabel('Depth to Water' + '_' + location + '_' + '(ft bTOC)')
    plt.grid()
    plt.show()
    fig.savefig(location + '_on_' + interval + '_mean' + '_' + today1 + ver + '.pdf')
    
    # TODO: add Bokeh plot layout
    
os.chdir(path)
############
