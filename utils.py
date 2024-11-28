import pandas as pd
from datetime import datetime
from sklearn.neighbors import BallTree
import numpy as np
from geopy.geocoders import Nominatim

UA = 'FindComps/1.3 csoto701@uchicago.edu'
FLIPS = pd.read_csv('comps.csv')

def common_elm_in_lists(lists):
    # Convert the first list to a set to use set operations
    common_elements = set(lists[0])
    
    # Intersect the common elements with the rest of the lists
    for lst in lists[1:]:
        common_elements &= set(lst)
    
    return list(common_elements)

def get_min_actors(df, actor, min, start_year,end_year):
    """
    Returns actors (buyers or sellers) who have bought or sold a min num of deals
    from start_year to end_year

    Args:
        df: DataFrame that contains data
        actor: str Either 'seller' or 'buuyer'
        min: int min number of deals to fiter
        start_year: int start year to search
        end_year: int end year to search

    Returns:
        DataFrame 
    """
    if actor == 'seller': actor = 'sale_seller_name'
    else: actor = 'sale_buyer_name'
    m_ls = []
    for year in range(start_year, end_year+1):
        df = df[df['year']==year]
        df = df.value_counts(subset=actor,ascending=False)
        df = df[df >= min]
        m_ls.append(df.index.tolist())
    
    return common_elm_in_lists(m_ls)

def get_loc(user_agent, address):
    """
    Returns latitude and longitude of address

    Args:
        user_agent: str the user_agent string to use Nominatim geolocator
        address: str
    Returns:
        loc List[Latitude, Longitude] for a given address
    """
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(address)
    if location:
        print(f"Location Found! Address: {address} Latitude: {location.latitude}, Longitude: {location.longitude}")
        return location.latitude, location.longitude
    else:
        print("Location not found.")
        return None, None

def haversine_distance(loc1, loc2):
    """
    Calculate the Haversine distance between two points on Earth
    """
    loc1= [np.radians(l) for l in loc1]
    loc2= [np.radians(l) for l in loc2]
    dlat = loc2[0] - loc1[0]
    dlon = loc2[1] - loc1[1]
    
    a = np.sin(dlat / 2.0) ** 2 + np.cos(loc1[0]) * np.cos(loc2[0]) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return 3959 * c  # Return distance in miles

def makeTree(df):
    """
    Understand what this is doing

    """
    loc = df[['latitude', 'longitude']].values
    loc_radians = np.radians(loc)
    return BallTree(loc_radians, metric='haversine')

# default is start_date=datetime.now().date() but for now will be dif
def get_comps(address, df=FLIPS, start_date=datetime(2023,10,1).date(), radius=0.5, months=6, end_date=None,loc=None):
    """
    Returns a DataFrame of comps given loc and criteria  

    Args:
        loc: List[Latitude, Longitude]
        df: DataFrame() that contains that properties to search for comps
        start_date: pd.datatime the date from which to go back N months to search for comps
        months = int the number of months to go back 
        radius: float the radius in miles to search for comps from loc
        end_date: pd.datetime if you want to specify end_date manually
    
    Returns:
        DataFrame
    
    """
    if loc is None:
        loc = get_loc(UA, address)
    
    if end_date is None:
        end_date = (start_date - pd.DateOffset(months=months)).date()

    df['sale_date'] = pd.to_datetime(df['sale_date'])
    time_app = df[(df['sale_date'].dt.date >=  end_date) & (df['sale_date'].dt.date <= start_date)]
    if len(time_app)==0:
        print('No comps found in date range')
        return None
    subject_point = np.radians([[loc[0], loc[1]]])
    radius_radians = radius / 3959

    tree = makeTree(time_app)
    indices = tree.query_radius(subject_point, r=radius_radians)
    comps = time_app.iloc[indices[0]].copy()
    
    comps.loc[:, 'distance'] = comps.apply(
        lambda row: haversine_distance(loc, row[['latitude','longitude']]), axis=1
    )
    comps = comps.sort_values(by='sale_price',ascending=False)
    comps = comps.reset_index(drop=True)
    return comps