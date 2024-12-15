import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import geopandas as gpd
import io
import numpy as np
import os 
import requests
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import xarray as xr

from datetime import datetime, timedelta
from matplotlib import colorbar, colors
from matplotlib.colors import to_rgba
from shapely.geometry import Polygon

#Downloads seasonal snowfall data to content/data.nc beginning in starting_year.
def get_data(starting_year):
    url = r'https://www.nohrsc.noaa.gov/snowfall_v2/data/' + str(starting_year + 1)
    url_end =  r'09/sfav2_CONUS_' + str(starting_year) + r'093012_to_' + str(starting_year + 1) + r'093012.nc'

    file_path = 'content/data.nc'
    if os.path.exists(file_path):
        os.remove(file_path)

    if (starting_year == 2020):
        url_end =  r'09/sfav2_CONUS_' + str(starting_year) + r'093012_to_' + str(starting_year + 1) + r'090112.nc'

    destination = "content/"  # Save it to the Colab working directory

    response = requests.get(url + url_end)

    if response.status_code == 200:
        filename = 'data.nc' # Extracting filename from the URL
        with open(destination + filename, "wb") as file:
            file.write(response.content)
        print(f"File downloaded successfully to {filename}")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

#Downloads daily data ending at yyyy-mm-dd 00z
#date is a string of yyyy-mm-dd
def get_daily_data(date):
    year, month, day = date.split('-')
    url = f'https://www.nohrsc.noaa.gov/snowfall_v2/data/{year}{month}/sfav2_CONUS_24h_{year}{month}{day}12.nc'

    #print(url)

    file_path = 'content/data.nc'
    if os.path.exists(file_path):
        os.remove(file_path)

    destination = "content/"

    response = requests.get(url)

    filename = 'data.nc'
    with open(destination + filename, "wb") as file:
        file.write(response.content)
        print(f"Successfully downloaded file")

#downloads a NOHRSC .nc file and uploads it to Google collab under /content/data.nc
def download_data(url):
    file_path = 'content/data.nc'
    if os.path.exists(file_path):
        os.remove(file_path)

    destination = "content/"

    response = requests.get(url)

    filename = 'data.nc'
    with open(destination + filename, "wb") as file:
        file.write(response.content)
        print(f"Successfully downloaded file")


#creates a dataset that is the average snowfall between the 2008-2009 and 2023-2024 seasons
def get_average_snowfall():
    for year in range(2008, 2023):
        get_data(year)
        if (year == 2008):
            ds = xr.open_dataset('content/data.nc')
        else:
            ds = ds + xr.open_dataset('content/data.nc')
        
    ds = ds / (2023 - 2008)

    return ds

import xarray as xr
from datetime import datetime, timedelta

#given a date of the style yyyy-mm-dd, returns the next consecutive date in the same form.
def next_date(current_date):
    current_date = datetime.strptime(current_date, '%Y-%m-%d')
    next_date = current_date + timedelta(days=1)
    return next_date.strftime('%Y-%m-%d')

#creates a snowfall map with total accumulation between startin_date and ending_date in yyyy-mm-dd format
def create_dataset(starting_date, ending_date):
    curr_date = next_date(starting_date)
    ending_date = next_date(ending_date)

    get_daily_data(curr_date)
    ds = xr.open_dataset('content/data.nc')
    curr_date = next_date(curr_date)
    while (curr_date != ending_date):
        get_daily_data(curr_date)
        ds = ds + xr.open_dataset('content/data.nc')
        curr_date = next_date(curr_date)

    return ds

########################################################
# Functions below deal with creating the maps themselves
########################################################


#NWS colors and contours
def get_contour_schema(schema):
    NOHRSClevels = [0.001, 0.1, 1, 2, 3, 4, 6, 8, 12, 18, 24, 30, 36, 48, 60, 72, 96, 120, 240]

    NOHRSCcontour_colors = ['#E4EEF4', '#BDD7E7', '#6BAED6', '#2D83BE', '#02509D', '#022194', '#FEFE96', '#FFC400', '#FE8700',
        '#DB0C00', '#9E0000', '#690000', '#330000', '#CDCDFF', '#A08DD9', '#7D51A6', '#551573', '#290030']

    if (schema == 'NOHRSC'):
        return [NOHRSClevels, NOHRSCcontour_colors]

import time 

#Creates the map 
def create_snow_map(params, bbox):
    print(f"params: {params}")
    option = params["type"]

    if option == "daily_snowfall":
        ds = create_dataset(params["sdate"], params["edate"])
    elif option == "seasonal_snowfall":
        get_data(int(params["syear"]))
        ds = xr.open_dataset('content/data.nc')
        ending_date = int(params["syear"]) + 1
    elif option == "average_snowfall":
        starting_date = "2008"
        ending_date = "2024"
        ds = get_average_snowfall()
    else:
        print("Invalid option")
        return

    box = bbox

    data_variable = ds['Data'] * 39.3701 #meters to inches
    latitudes = ds['lat']
    longitudes = ds['lon']

    # Create a Cartopy map projection
    projection = ccrs.PlateCarree()

    # Create a Matplotlib figure and axis with Cartopy projection
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(16, 12))

    ax.set_extent((box[0], box[2], box[1], box[3]))
    ax.add_feature(cartopy.feature.STATES)

    levels = get_contour_schema("NOHRSC")[0]
    contour_colors = get_contour_schema("NOHRSC")[1]

    plot = ax.contourf(longitudes, latitudes, data_variable, transform=projection, colors=contour_colors, levels=levels, extend="both")

    # Load county borders using geopandas
    url = "https://www2.census.gov/geo/tiger/GENZ2021/shp/cb_2021_us_county_5m.zip"
    gdf = gpd.read_file(url)

    # Filter counties within the specified box
    box_polygon = Polygon([(box[0], box[1]), (box[0], box[3]), (box[2], box[3]), (box[2], box[1])])
    gdf = gdf[gdf.geometry.intersects(box_polygon)]

    # Plot county borders
    gdf.boundary.plot(ax=ax, linewidth=1, linestyle=":", edgecolor='black')


    cbar = plt.colorbar(plot, ax=ax, orientation='vertical', pad=0.01, ticks=levels)
    cbar.ax.tick_params(labelsize=14)

    if option == "daily_snowfall":
        plt.title(f'Snowfall between {starting_date} 12z and {ending_date} 12z', fontsize=25, fontweight="bold")
    else:
        plt.title(f'Snowfall between {starting_date} and {ending_date}', fontsize=25, fontweight="bold")

    image_buffer = io.BytesIO()
    plt.savefig(image_buffer, format="png")
    plt.close()
    image_buffer.seek(0)

    return image_buffer

#Returns selected bbox regions
def get_bbox(name):
    name = name.lower()
    if name == "li":
        return (-74.096296,40.512183,-71.800888,41.184880)
    if name == "nyc":
        return (-75.372142,40.099855,-71.401855,41.783255)
    if name == "northeast":
        return (-81.083795,38.211089,-66.103235,47.428853)
    if name == "95":
        return (-78.123961,38.154444,-69.535399,43.754077)
    if name == "midwest":
        return (-105.868347,37.519716,-78.587034,49.326295)
    if name == "west":
        return (-126.483827,30.621623,-101.706596,50.069296)
    if name == "upperwest":
        return (-126.483827,30.621623,-101.706596,50.069296)
    if name == "southwest":
        return (-126.483827,30.621623,-101.706596,50.069296)
    if name == "southeast":
        return (-99.190331,24.935900,-74.632756,37.301083)
    if name == "plains":
        return (-106.094523,25.184924,-90.279269,45.278685)
    if name == "sne":
        return (-74.433536,40.482423,-70.084341,43.197368)
    if name == "midatl":
        return (-81.439958,36.906292,-71.182008,41.776690)
    if name == "eastern":
        return (-104.589844,28.690588,-62.490234,49.496675)