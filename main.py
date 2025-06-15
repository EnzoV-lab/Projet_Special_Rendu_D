import csv
from geopy.distance import geodesic
import folium
from math import floor
import numpy as np
import pandas as pd
import requests

df = pd.read_csv("Data/Waypoints.csv")
north_america_codes = ['US', 'CA', 'MX']
df_na = df[df['iso_country'].isin(north_america_codes)]
waypoints = df_na[['ident', 'latitude_deg', 'longitude_deg', 'iso_country']]
print(waypoints.head())
waypoints.to_csv("Data/Waypoints.csv", index=False)



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
# Charge les identifiant et coordonnées des waypoints de la base de données
def charger_waypoints(fichier_csv):
    waypoints = []
    with open(fichier_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # sauter l'en-tête
        for ligne in reader:
            if len(ligne) < 3:
                continue
            try:
                id_wp = ligne[0]
                lat = float(ligne[1])
                lon = float(ligne[2])
                waypoints.append((id_wp, lat, lon))
            except ValueError:
                continue
    return waypoints
# Renvoie une liste de tuple ('ID', (latitude, longitude))


# Interpolation linéaire entre le point de départ et le point d'arrivée
def intercaler_points(lat1, lon1, lat2, lon2, n):
    points_intercale = []
    for i in range(1, n + 1):
        x = lat1 + i * (lat2 - lat1) / (n + 1)
        y = lon1 + i * (lon2 - lon1) / (n + 1)
        points_intercale.append((x, y))

    return points_intercale


def grille_partition(waypoints, res=(10, 10)):
    # waypoints est un dict {id: (lat, lon)}
    latitudes = [coord[0] for coord in waypoints.values()]
    longitudes = [coord[1] for coord in waypoints.values()]

    y1, y2 = min(latitudes), max(latitudes)
    x1, x2 = min(longitudes), max(longitudes)

    h = (y2 - y1) / res[1] if res[1] > 0 else 1
    l = (x2 - x1) / res[0] if res[0] > 0 else 1

    grid = {}

    for wp_id, (lat, lon) in waypoints.items():
        i = min(int(floor((lat - y1) / h)), res[1] - 1) if h > 0 else 0
        j = min(int(floor((lon - x1) / l)), res[0] - 1) if l > 0 else 0
        grid.setdefault((i, j), []).append(wp_id)

    return (res, grid), (x1, y1, x2, y2)



#Détermine le waypoint le plus proche de la localisation du point en entrée
def determiner_wp_plus_proche(point, waypoints, partition, geometry, fast=True):
    min_dist = np.inf
    wp_id = None
    coordonnees_proche = (None, None)

    if fast:
        x1, y1, x2, y2 = geometry
        res = partition[0]
        grid = partition[1]
        l = (x2 - x1) / res[0]
        h = (y2 - y1) / res[1]

        i = min(int(floor((point[0] - y1) / h)), res[1] - 1)
        j = min(int(floor((point[1] - x1) / l)), res[0] - 1)
        ids = grid.get((i, j), [])

        if len(ids) <= 1:
            ids = waypoints.keys()
    else:
        ids = waypoints.keys()

    for id_wp in ids:
        lat_wp, lon_wp = waypoints[id_wp]
        d = geodesic((point[0], point[1]), (lat_wp, lon_wp)).meters
        if d < min_dist:
            min_dist, wp_id = d, id_wp
            coordonnees_proche = waypoints[id_wp]

    return wp_id, coordonnees_proche[0], coordonnees_proche[1]


def selectionner_waypoints_plus_proches_par_segments(waypoints, depart, arrivee, partition, geometry, n_points=100):
    points_intermediaires = intercaler_points(depart[0], depart[1], arrivee[0], arrivee[1], n_points)
    cas_teste = set()
    waypoints_selectionnes = []

    for point in points_intermediaires:
        wp = determiner_wp_plus_proche(point, waypoints, partition, geometry, fast=True)
        if wp[0] not in cas_teste:
            waypoints_selectionnes.append(wp)
            cas_teste.add(wp[0])
    print(waypoints_selectionnes)
    return waypoints_selectionnes

def tracer_trajet(chemin):
    """
    Affiche un trajet sur une carte Folium et retourne l'objet carte.
    `chemin` est une liste de tuples (id, lat, lon)
    """
    if not chemin:
        raise ValueError("Le chemin est vide.")

    lat_centre = sum(p[1] for p in chemin) / len(chemin)
    lon_centre = sum(p[2] for p in chemin) / len(chemin)
    carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=5)

    for i, (id, lat, lon) in enumerate(chemin):
        couleur = "green" if i == 0 else "red" if i == len(chemin) - 1 else "blue"
        folium.Marker(location=(lat, lon), popup=id, icon=folium.Icon(color=couleur)).add_to(carte)

    folium.PolyLine([(lat, lon) for _, lat, lon in chemin], color="blue", weight=2.5).add_to(carte)
    return carte

"""# 1. Charger la liste de waypoints (liste de tuples)
waypoints_liste = charger_waypoints("Data/Waypoints.csv")

# 2. Convertir en dict {id: (lat, lon)}
waypoints_dict = {wp_id: (lat, lon) for wp_id, lat, lon in waypoints_liste}

# 3. Créer la partition spatiale
partition, geometry = grille_partition(waypoints_dict, res=(10, 10))

# 4. Appeler la fonction en passant partition et geometry
chemin = selectionner_waypoints_plus_proches_par_segments(waypoints_dict, [40.7128, -74.0060], [41.8781, -87.6298], partition, geometry)

#5 Afficher la carte
carte = tracer_trajet(chemin)
carte.save("trajet.html")"""