
import csv
from geopy.distance import geodesic
import folium

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