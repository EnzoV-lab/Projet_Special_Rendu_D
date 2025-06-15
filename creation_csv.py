import pandas as pd


df = pd.read_csv("Data/Waypoint.csv")
north_america_codes = ['US', 'CA', 'MX']
df_na = df[df['iso_country'].isin(north_america_codes)]
waypoints = df_na[['ident', 'latitude_deg', 'longitude_deg', 'iso_country']]
print(waypoints.head())
waypoints.to_csv("Data/waypoints.csv", index=False)



import requests

class DonneesMeteo:
    def __init__(self, cle_api, coordonnees=None):
        self.coordonnees = coordonnees
        self.cle_api = cle_api
        self.donnees = None

    def fetch(self):
        if self.coordonnees:
            q = f"{self.coordonnees[0]},{self.coordonnees[1]}"
        else:
            raise ValueError("Il faut fournir des coordonnées.")

        url = f"http://api.weatherapi.com/v1/current.json?key={self.cle_api}&q={q}"
        response = requests.get(url)
        if response.status_code == 200:
            self.donnees = response.json()
        else:
            print("Erreur lors de la requête:", response.text)

    def get_donnees(self):
        if not self.donnees:
            return {}

        current = self.donnees.get("current", {})
        condition = current.get("condition", {}).get("text", "")
        return {
            "vent_kph": current.get("wind_kph"),
            "direction_cardinal": current.get("wind_dir", "N/A"),
            "direction_deg": current.get("wind_degree", 0),
            "condition": condition,
            "precip_mm": current.get("precip_mm", 0)
        }