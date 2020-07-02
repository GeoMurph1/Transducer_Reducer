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
from bokeh.plotting import figure, show, output_file, ColumnDataSource
from bokeh.layouts import column
from bokeh.models import Title

####### USER SELECTED AND CONSTANTS ########################################################
ver ='01a'
today1 = str(date.today())
interval = '15T'
### Set constants for filter function ###
THRSH = 0.75 
RNG = 20 
LIM = 20
###############################################################################

# Define outlier filtering function:
def outlier_filter(df, thrsh, rng, lim):
    """"Calculate absolute value of difference for n steps in range; replace outliers > threshold with NaN, then linearly interpolate new values. Takes inputs of pandas DataFrame (df), threshold change (thrsh), steps range (rng), and limit (lim)"""
    for n in np.arange(rng)*-1:
        df['Diff'] = df.WaterLevel.diff(periods = n)
        df['WL_nan'] = df['WaterLevel'].mask(df.Diff.abs() > thrsh, np.NaN, inplace = True) # Impute nan's where the sequential difference is > threshold value
        df['WL_int'] = df['WaterLevel'].interpolate(method='linear', limit=lim) # Linearly interpolate between nan values

# Read and append single or multiple transducer files into a single DataFrame
path= os.getcwd()
filenames = glob.glob(path + "/*.xlsx")

# Read and append Excel data files into 
df_append = pd.DataFrame()
for f in filenames:
    df = pd.read_excel(f,  infer_datetime_format=True, encoding='utf-8')
    df_append = df_append.append(df)
    
# Set appended dataframe to working frame    
df1 = df_append
#df1 = df.dropna(axis=0, subset=['WaterLevel']).reset_index(drop=True)

# Additional new columns etc
date_ = df1['TimeStamp']
flow_datetimes = pd.to_datetime(date_, infer_datetime_format= True)
df1['TimeStamp'] = flow_datetimes

df1['Location'] = df1['MonitoringPoint']

# List of locations and TOC elevations to join to main frame
loc_list = ['RI-17D',	'RI-17S',	'RI-18D',	'RI-27D',	'RI-27I',	'RI-27S',	'RI-33I',	'RI-33S',	'RI-34I',	'RI-34S',	'RI-35DD',	'RI-36I',	'RI-36S',	'RI-38D',	'RI-38I',	'RI-39D',	'RI-39I',
]
toc_list = [286.26,	286.2,	293.0878,	298.0119,	298.2569,	297.9959,	297.27,	297.08,	296.45,	296.27,	296.7691,	296.93,	296.91,	296.4854,	296.6084,	296.8475,	297.0035,
]
# Change loclist to lowercase for join
loc_list = [i.lower() for i in loc_list]


# DataFrame of locations and tops of casing elevations
df_locs_tocs =  pd.DataFrame({"locs":loc_list, "tocs":toc_list})

# Inner join on location ID
df2 = df1.merge(df_locs_tocs, left_on='Location', right_on='locs', how='inner')
df2["gwe_ft_amsl"] = df2.tocs - df2.WaterLevel
df2 = df2.dropna(axis=0, subset=['WaterLevel']).reset_index(drop=True)

# Filter outliers with defined function
outlier_filter(df2, THRSH, RNG, LIM)

# Generate grouped dataframe for resampling
df_grp = df2.groupby(["Location"])
df_resamp = df_grp.resample(interval, on='TimeStamp').mean()
df_resamp.reset_index(inplace=True)
#location = df_resamp["Location"].unique()
df_resamp = df_resamp[['Location', 'TimeStamp', 'WaterLevel', 'gwe_ft_amsl']]
df_resamp.dropna(inplace=True)
df_resamp = df_resamp.reset_index(drop=True)
df_resamp['dt_str'] = df_resamp['TimeStamp'].dt.strftime('%Y-%m-%d %H:%M')

plots = '_'.join(["Transducer","Data", "Plots", today1, ver]) 

# Set new directory for plots if does not exist:
if os.path.exists(plots) == False:
    os.mkdir(plots)
    
# TODO revise bokeh plot output for updated engine   

"""
        
# blank column layout for plots        
column1 = column()
# Generate dataframes and plots:        
os.chdir(plots)

    writer = pd.ExcelWriter( location + '_' +  'resamp_on_' + interval + '_mean' + '_'+  today1 +'.xls')
    df_resamp.to_excel(writer, 'Sheet1' )
    writer.save()

    # TODO: add Bokeh plot layout
    source = ColumnDataSource(df_resamp)
    TOOLTIPS = [("Datetime", "@dt_str"), ("DTW ft-bmp", "@gwe_ft_amsl")]
    ymin = df.WL_int.min()
    ymax = df.WL_int.max()
    p = figure(height=555, width=1000, x_axis_label='Date', y_axis_label='DTW (ft bmp)', 
               x_axis_type='datetime', title = 'Depth to water, feet below measuring point at ' + location + '',
               y_range = (ymin - 0.1, ymax + 0.1), tooltips=TOOLTIPS) # Reverse ymax, ymin for DTW
    p.line('TimeStamp', 'gwe_ft_amsl', legend_label=location, alpha=0.8, source=source)
    p.inverted_triangle('TimeStamp', 'gwe_ft_amsl', legend_label=location, alpha=0.8, size=4, source=source)
    title = Title(text="Programmed by Michael J. Murphy, 2020", text_font_size='8pt', align='right')
    p.add_layout(title, 'right')
    output_file('_'.join([location, today1, ver, ".html" ]))
    show(p)
# TODO add column layout, append with each plot - get this to work
 
    column1.children.append(p)
output_file('_'.join(["Transducer","Dashboard", today1, ver, ".html"])

os.chdir(path)
############

# TODO Depecrate PDF plot output after implementing bokeh plots

fig = plt.figure()
fig.set_figheight(8.5)
fig.set_figwidth(11)
plt.plot(df_resamp['TimeStamp'], df_resamp['WL_int'])
'''Turn on to reverse y-axis for plotting DTW'''
ax= plt.axis()
plt.axis((ax[0], ax[1], ax[3], ax[2]))

plt.minorticks_on()
plt.xticks(rotation=45)
plt.xlabel('Date')
plt.ylabel('Depth to Water' + '_' + location + '_' + '(ft bmp)')
plt.grid()
plt.show()
fig.savefig(location + '_on_' + interval + '_mean' + '_' + today1 + ver + '.pdf')

"""
















