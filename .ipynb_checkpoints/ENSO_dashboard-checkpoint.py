import pandas as pd
import numpy as np
import panel as pn
import plotly.express as px

pn.extension('tabulator')

import hvplot.pandas
import holoviews as hv

def nino_nomalies_df():

    nino34_df = pd.read_fwf('https://portal.nersc.gov/project/dasrepo/AGU_ML_Tutorial/nino34.long.anom.data.txt', colspecs="infer", header=None)
    # Add column names
    nino34_df.columns = ['YEAR', 'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    # Melt the dataframe to long format
    df_long = nino34_df.melt(id_vars='YEAR', var_name='MONTH', value_name='ANOM')

    # Extract the month number from the month column
    df_long['MONTH'] = pd.to_datetime(df_long['MONTH'], format='%b').dt.month

    # Create a datetime index
    df_long['DATE'] = pd.to_datetime(df_long[['YEAR', 'MONTH']].assign(DAY=1))

    # Drop the YEAR and MONTH columns
    df_long = df_long.drop(columns=['YEAR', 'MONTH'])

    # Sort Values by DATE
    df_long = df_long.sort_values(by='DATE')

    df_long = df_long.query('DATE < "2019"')

    # Create variable and order columns
    nino34_df = df_long[['DATE', 'ANOM']].reset_index(drop=True)

    # Read the data from the NOAA website
    anom_temp_df = pd.read_fwf('https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt', colspecs="infer")

    # Group by 'Year' and add a sequential month number starting from 1
    anom_temp_df['MONTH'] = anom_temp_df.groupby('YR').cumcount() + 1

    # add a leading zero to the month number if it is less than 2 digits
    anom_temp_df['MONTH'] = anom_temp_df['MONTH'].apply(lambda x: '{0:0>2}'.format(x))

    # create a new column 'DATE' by concatenating the 'YR' and 'MONTH' columns
    anom_temp_df['DATE'] = anom_temp_df['YR'].astype(str) + '-' + anom_temp_df['MONTH'].astype(str)

    # drop the 'YR' and 'MONTH' columns and convert the 'DATE' column to datetime format
    anom_temp_df['DATE'] = pd.to_datetime(anom_temp_df['DATE'], format='%Y-%m')

    nino34_comb = anom_temp_df[['DATE', 'TOTAL', 'ANOM']].copy()

    nino34_comb.rename(columns = {'TOTAL':'TEMP'}, inplace = True)


    # Create a new dataframe with necessary columns
    data = anom_temp_df[['DATE', 'ANOM']].copy()


    nino34_df1 = data.query('DATE > "2018"')

    nino34_anom = pd.concat([nino34_df, nino34_df1], ignore_index=True)

    nino34_anom.drop_duplicates(subset='DATE', keep='first', inplace=True)
    nino34_comb.drop_duplicates(subset='DATE', keep='first', inplace=True)

    
    # nino34 is a dataframe with only anomalies, data is a dataframe with anomalies and temperatures
    return nino34_anom, nino34_comb


anom, comb = nino_nomalies_df()

comb['YEAR'] = comb['DATE'].dt.year
anom['YEAR'] = anom['DATE'].dt.year



# Make DataFrame Pipeline Interactive
idf_both = comb.interactive()

start_year = comb.DATE.dt.year.min()
end_year = comb.DATE.dt.year.max()

year_slider_start_comb = pn.widgets.IntSlider(name='Year Slider Start', start=start_year, end=end_year, step=1, value=1990)
year_slider_end_comb = pn.widgets.IntSlider(name='Year Slider End', start=start_year, end=end_year, step=1, value=2020)


both_pipeline = (
    idf_both[
        (idf_both.YEAR >= year_slider_start_comb) &
        (idf_both.YEAR <= year_slider_end_comb)
    ]
    .reset_index()
    .sort_values(by='DATE')  
    .reset_index(drop=True)
)


df_plot = both_pipeline.hvplot(x = 'DATE', y='TEMP',line_width=2, title="Sea Surface Temperatures", color = 'SlateGray')


anoms = anom
anoms['YEAR'] = anoms['DATE'].dt.year

anoms_idf = anoms.interactive()

start_year1 = anom.DATE.dt.year.min()
end_year1 = anom.DATE.dt.year.max()

year_slider_start_anom = pn.widgets.IntSlider(name='Year Slider Start', start=start_year1, end=end_year1, step=1, value=1990)
year_slider_end_anom = pn.widgets.IntSlider(name='Year Slider End', start=start_year1, end=end_year1, step=1, value=2020)


anom_pipeline = (
    anoms_idf[
        (anoms_idf.YEAR >= year_slider_start_anom) &
        (anoms_idf.YEAR <= year_slider_end_anom)
        ]
    .reset_index()
    .sort_values(by='DATE')  
    .reset_index(drop=True)
)



bar_plot = anom_pipeline.hvplot.bar(
    x = 'DATE', 
    y = 'ANOM', 
    color='ANOM', 
    colorbar=True, 
    clabel="ANOMALIES", 
    cmap="coolwarm",
    title='SST Anomalies',
    width=1500
)


red_line = hv.HLine(0.5).opts(color='red', line_width=2)
blue_line = hv.HLine(-0.5).opts(color='blue', line_width=2)

final_plot = bar_plot * red_line * blue_line


template = pn.template.FastListTemplate(
    
    title='SST Anomalies Dashboard', 
    
    sidebar=[pn.pane.Markdown("# Sea Surface Temperatures and Anomalies "), 
             pn.pane.Markdown("#### El Niño/ Southern Oscillation (ENSO) is the dominant mode of variability that affects the climate on seasonal time scales.  It is measured by the Nino3.4 index, a rolling 3-month average of equatorial Pacific temperatures.  ENSO is an oscillation and is marked by two phases: El Niño, with anomalously warm equatorial Pacific temperatures, and La Niña, with anomalously cold temperatures.  Because El Niño is tied to many weather patterns around the world, such as the Indian monsoon, hurricanes in the Atlantic, and North American temperature, accurate ENSO forecasts are valuable for climate-sensitive sectors (such as agriculture, water, and energy)."), 
             pn.pane.Markdown(""),
             pn.pane.Markdown(""),
             pn.pane.Markdown(""),
             pn.pane.Markdown(""), 
             pn.pane.PNG('climate_day.png', sizing_mode='scale_both')
            ],
    
    main=[
        pn.Row(
            pn.Column(
                year_slider_start_comb, 
                year_slider_end_comb,
                df_plot.panel(width=1250), 
                margin=(0,25)
            )  
        ),
        pn.Row(
            pn.Column(
                year_slider_start_anom,
                year_slider_end_anom,
                final_plot.panel(width=1250), 
                margin=(0,25)
            ) 
        ),
        pn.Row(
            pn.Column(
                pn.pane.Markdown("## Own Anomalies"),
                pn.pane.GIF('own_anomalies.gif', width=700, height=500)
            ),
            pn.Column(
                pn.pane.Markdown("## NERSC Anomalies"),
                pn.pane.GIF('nersc_anomalies.gif', width=700, height=500)
            )                                
        ),
        pn.Row(
            pn.Column(
                pn.pane.Video('complete_anomalies.mp4', width=1250, height=800)
            )
        )
            
        ],
    
    accent_base_color="#2E86C1",
    header_background="#2E86C1",
)
#template.show()
template.servable();