
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


"""# ======== UTILISATION ========
# 1. Charger la liste de waypoints (liste de tuples)
waypoints_liste = charger_waypoints("Data/waypoints.csv")

# 2. Convertir en dict {id: (lat, lon)}
waypoints_dict = {wp_id: (lat, lon) for wp_id, lat, lon in waypoints_liste}

# 3. Créer la partition spatiale
partition, geometry = grille_partition(waypoints_dict, res=(10, 10))

# 4. Trouver le waypoint le plus proche d'un point donné (ex : New York)
point_test = (40.7128, -74.0060)
wp_id, lat, lon = determiner_wp_plus_proche(point_test, waypoints_dict, partition, geometry, fast=True)

print(f"Waypoint le plus proche: {wp_id}, coordonnées: ({lat}, {lon})")"""