
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
    w = (x2 - x1) / res[0] if res[0] > 0 else 1

    grid = {}

    for wp_id, (lat, lon) in waypoints.items():
        i = min(int(floor((lat - y1) / h)), res[1] - 1) if h > 0 else 0
        j = min(int(floor((lon - x1) / w)), res[0] - 1) if w > 0 else 0
        grid.setdefault((i, j), []).append(wp_id)

    return (res, grid), (x1, y1, x2, y2)