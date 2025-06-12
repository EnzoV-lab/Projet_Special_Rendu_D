import pandas as pd


df = pd.read_csv("Data/Waypoint.csv")
north_america_codes = ['US', 'CA', 'MX']
df_na = df[df['iso_country'].isin(north_america_codes)]
waypoints = df_na[['ident', 'latitude_deg', 'longitude_deg', 'iso_country']]
print(waypoints.head())
waypoints.to_csv("Data/waypoints.csv", index=False)