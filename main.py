# Ces modules sont à télécharger avant d'exécuter le script
import csv
from geopy.distance import geodesic
import folium #ce module permet de générer une carte intéractive
from math import floor #floor permet d'arrondir à l'entier inférieure
import numpy as np
import pandas as pd
import requests # Nécessaire afin d'effectuer des requêtes  http
import os # Permet une meilleure gestion du chemin des fichiers

#La clé API est utilisée pour accéder aux données météo depuis le service weatherapi.com
cle_api ="d9ac5ac56f3d4768abd232315250506"

#------Chargement--des--WAYPOINTS
filepath = os.path.join("Data", "Waypoints.csv")
df = pd.read_csv(filepath)
# On conserve que les waypoints en amérique du Nord
north_america_codes = ['US', 'CA', 'MX']

#Selection de l'identifiant et des données de latitude et de longitudes
df_na = df[df['iso_country'].isin(north_america_codes)]
waypoints = df_na[['ident', 'latitude_deg', 'longitude_deg', 'iso_country']]
print(waypoints.head())
#Nouvelle écriture des données dans le même fichier csv
waypoints.to_csv("Data/Waypoints.csv", index=False)


#Création de la classe et des fonctions qui permettent de gérer la météo
class DonneesMeteo:
    #Initialisation de la clé API et des coordonnés
    def __init__(self, cle_api, coordonnees=None):
        self.coordonnees = coordonnees
        self.cle_api = cle_api
        self.donnees = None

    #Cette fonction permet de récupérer les données météos actuelles
    def fetch(self):
        #Vérification de la présence ou nom de coordonnées
        if self.coordonnees:
            #formatage des données en une chaine "lat,lon"
            q = f"{self.coordonnees[0]},{self.coordonnees[1]}"
        else:
            raise ValueError("Impossible de récupérer les données.")

        #Utilisation de l'url spécifique pour récupérer les données météo
        url = f"http://api.weatherapi.com/v1/current.json?key={self.cle_api}&q={q}"
        reponse = requests.get(url)
        if reponse.status_code == 200:
            self.donnees = reponse.json() #Récupération des données météos au format JSON
        else:
            print("Erreur lors de la requête:", reponse.text) #Affiche l'erreur si nécessaire

    #Extraction des données nécessaires
    def get_donnees(self):
        if not self.donnees:
            return {}
        #Extraction des données actuelles
        current = self.donnees.get("current", {})
        condition = current.get("condition", {}).get("text", "")
        return {
            "vent_km_h": current.get("wind_kph"), #Extraction des données sur la vitesse du vent
            #Extraction des données sur la direction du vent
            "direction_cardinal": current.get("wind_dir", "N/A"),
            "direction_deg": current.get("wind_degree", 0),
            #Extraction des conditions (venteux, nuageux...)

            "condition": condition,
            "precip_mm": current.get("precip_mm", 0)
        }
# Charge les identifiant et coordonnées des waypoints de la base de données
def charger_waypoints(fichier_csv):
    waypoints = []
    with open(fichier_csv, newline='', encoding='utf-8') as csvfile:

        lecteur = csv.reader(csvfile) #lit le fichier ligne par ligne
        next(lecteur)  # Ignore l'en-tête et les lignes incomplètes
        for ligne in lecteur:
            if len(ligne) < 3:
                continue #ignore les lignes incomplètes de moins de 3 colonnes
            try:
                id_wp = ligne[0] #la première colonne représente l'identifiant du waypoint
                lat = float(ligne[1]) #la deuxième colonne représente la latitude
                lon = float(ligne[2]) #la troisième colonne représente la longitude
                waypoints.append((id_wp, lat, lon)) #ajoute les éléments précedents à la liste
            except ValueError:
                continue
    return waypoints # Renvoie une liste de tuple ('ID', (latitude, longitude))
""""
Interpolation linéaire entre le point de départ et le point d'arrivée
permet de générer des points intermédiaires entre deux coordonnées géographiques
"""
def intercaler_points(lat1, lon1, lat2, lon2, n):
    points_intercale = [] # on stocke les points ici

    for i in range(1, n + 1):
        x = lat1 + i * (lat2 - lat1) / (n + 1)
        y = lon1 + i * (lon2 - lon1) / (n + 1)
        points_intercale.append((x, y))


    return points_intercale #retourne la liste de points intermédiares

"""
permet de découper la carte en case afin d'y placer chaque point dans la bonne case
le but étant de trouver rapidement le point le plus proche d'un endroit
"""
def grille_partition(waypoints, res=(10, 10)):
    # waypoints est un dict {id: (lat, lon)}
    #res est la résolution de la case
    latitudes = [coord[0] for coord in waypoints.values()] #liste des latitudes
    longitudes = [coord[1] for coord in waypoints.values()] #liste des longitudes

    #Délimite la zone géographique qui contient tous les waypoints
    y1, y2 = min(latitudes), max(latitudes) #point du sud au nord
    x1, x2 = min(longitudes), max(longitudes) #de l'ouest à l'est

    h = (y2 - y1) / res[1] if res[1] > 0 else 1 #hauteur d'une case
    l = (x2 - x1) / res[0] if res[0] > 0 else 1 #largeur d'une case

    grid = {} #permet de stocker les cases de la grille

    for wp_id, (lat, lon) in waypoints.items():
        i = min(int(floor((lat - y1) / h)), res[1] - 1) if h > 0 else 0 #ligne de la case où se trouve le point
        j = min(int(floor((lon - x1) / l)), res[0] - 1) if l > 0 else 0 #colonne de la case où se trouve le point
        grid.setdefault((i, j), []).append(wp_id)
    #la fonction retourne la grille de répartition et les coordonnées géographiques

    return (res, grid), (x1, y1, x2, y2)




#Détermine le point de navigation (waypoint) le plus proche de la localisation du point en entrée
def determiner_wp_plus_proche(point, waypoints, partition, geometry, fast=True):
    min_dist = np.inf #initialisation de la distance minimale entre deux waypoints
    wp_id = None #initialisation de l'identifiant du point de navigation le plus proche
    coordonnees_proche = (None, None) #coordonnée du point le plus proche

    #recherche locale des waypoints les plus proches
    if fast:
        x1, y1, x2, y2 = geometry #on prend les coordonnées des points au coin de la case
        res = partition[0] #résolution
        grid = partition[1] # on récupère la liste des waypoints dans la case
        l = (x2 - x1) / res[0] #largeur (longitude)
        h = (y2 - y1) / res[1] #hauteur (latitude)
        #identification de la case (i,j) où se trouve le point de navigation
        i = min(int(floor((point[0] - y1) / h)), res[1] - 1)
        j = min(int(floor((point[1] - x1) / l)), res[0] - 1)
        ids = grid.get((i, j), []) #liste des identifiants des waypoints

        #Dans le cas où le nombre de waypoints inf à 1 on élargie la recherche
        if len(ids) <= 1:
            ids = waypoints.keys()

    else:
        """
        Dans le cas où le nombre de waypoints inf à 1 on élargie la recherche
        on ignore la grille donc le temps de recherche est plus elevé
        """
        ids = waypoints.keys()
    """
    Pour chaque point de navigation (waypoints) dans l'ids on calcule la distance entre le point
    et le way point et on prend la distance la plus petite
    """
    for id_wp in ids:
        lat_wp, lon_wp = waypoints[id_wp] # récupération des coordonnées
        d = geodesic((point[0], point[1]), (lat_wp, lon_wp)).meters #calcul de la distance en mètre
        if d < min_dist:
            #mis à jour de la distance minimale
            min_dist, wp_id = d, id_wp
            coordonnees_proche = waypoints[id_wp]

    #renvoie l'identifiant, la latitude et la longitude du waypoint le plus proche
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

def tracer_trajet_meteo_dynamique(chemin, cle_api, avion):
    if not chemin:
        raise ValueError("Le chemin n'existe pas")

    lat_centre = sum(p[1] for p in chemin) / len(chemin)
    lon_centre = sum(p[2] for p in chemin) / len(chemin)
    carte = folium.Map(position=(lat_centre, lon_centre), eom_start=5)

    for i, (id_wp, lat, lon) in enumerate(chemin):
        # On récupère les données météo
        meteo = DonneesMeteo(cle_api, (lat, lon))
        meteo.fetch()
        infos = meteo.get_donnees()

        popup_text = (
            f"ID:{id_wp}"
            f" Vent: {infos.get('vent_kph', 'N/A')} km/h {infos.get('direction_cardinal', '')}"
            f" Condition: {infos.get('condition', 'N/A')}"
            f" Précipitations: {infos.get('precip_mm', 'N/A')} mm"
        )


        # Déterminer la couleur du marker
        if not avion.en_capaciter_de_voler(infos.get('vent_kph', 0)):
            couleur = "red"


        else:
            couleur = "green"
        folium.Marker(
            location=(lat, lon),
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color=couleur)
        ).add_to(carte)

    folium.PolyLine([(lat, lon) for _, lat, lon in chemin], color="blue", weight=2.5).add_to(carte)
    return carte


class Avion:
    def __init__(self, nom, vitesse_vent_max, categorie, vitesse_croisiere):
        """
        Initialise un objet Avion.

        :param nom: Nom ou modèle de l'avion (str)
        :param vitesse_vent_max: Vitesse maximale de vent tolérée (en km/h)
        :param categorie: Type d'avion (hélice, turbopropulseur)
        :param vitesse_croisiere: Vitesse de croisière en km/h (float)
        """
        self.nom = nom
        self.vitesse_vent_max = vitesse_vent_max
        self.categorie = categorie
        self.vitesse_croisiere = vitesse_croisiere

    def en_capaciter_de_voler(self, vent_km_h):

        """
        Vérifie si l'avion peut voler avec la vitesse de vent donnée.

        :param vent_kph: vitesse du vent en km/h (float)
        :return: True si l'avion peut voler, sinon False
        """

        return vent_km_h <= self.vitesse_vent_max


    def __str__(self):
        return f"Avion {self.nom} (vent max: {self.vitesse_vent_max} km/h, croisière: {self.vitesse_croisiere} km/h)"

    # === Création des avions ===


avions = [
    # Hélice
    Avion("Cessna 172", 20, "hélice", 190),
    Avion("Piper PA-28 Cherokee", 60, "hélice", 210),
    Avion("Diamond DA40", 65, "hélice", 285),

    # Turbopropulseur
    Avion("DHC-6 Twin Otter", 70, "turbopropulseur", 320),
    Avion("Beechcraft King Air 350", 80, "turbopropulseur", 540),
    Avion("ATR 72", 90, "turbopropulseur", 510),

    #Jet
    Avion("Airbus A320neo", 100, "jet", 830),
    Avion("Airbus A350-900", 120, "jet", 900),
    Avion("Boeing 737 MAX 8", 100, "jet", 840),
    Avion("Boeing 787-9 Dreamliner", 120, "jet", 913),
]


villes_coordonnees = {
    "New York": (40.7128, -74.0060),
    "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298),
    "Houston": (29.7604, -95.3698),
    "Phoenix": (33.4484, -112.0740),
    "Philadelphia": (39.9526, -75.1652),
    "San Antonio": (29.4241, -98.4936),
    "San Diego": (32.7157, -117.1611),
    "Dallas": (32.7767, -96.7970),
    "San Jose": (37.3382, -121.8863),
    "Austin": (30.2672, -97.7431),
    "Jacksonville": (30.3322, -81.6557),
    "Fort Worth": (32.7555, -97.3308),
    "Columbus": (39.9612, -82.9988),
    "Charlotte": (35.2271, -80.8431),
    "San Francisco": (37.7749, -122.4194),
    "Indianapolis": (39.7684, -86.1581),
    "Seattle": (47.6062, -122.3321),
    "Denver": (39.7392, -104.9903),
    "Washington": (38.9072, -77.0369),
    "Boston": (42.3601, -71.0589),
    "Nashville": (36.1627, -86.7816),
    "El Paso": (31.7619, -106.4850),
    "Detroit": (42.3314, -83.0458),
    "Memphis": (35.1495, -90.0490),
    "Portland": (45.5152, -122.6784),
    "Las Vegas": (36.1699, -115.1398),
    "Louisville": (38.2527, -85.7585),
    "Baltimore": (39.2904, -76.6122),
    "Milwaukee": (43.0389, -87.9065),
    "Albuquerque": (35.0844, -106.6504),
    "Tucson": (32.2226, -110.9747),
    "Fresno": (36.7378, -119.7871),
    "Mesa": (33.4152, -111.8315),
    "Sacramento": (38.5816, -121.4944),
    "Atlanta": (33.7490, -84.3880),
    "Kansas City": (39.0997, -94.5786),
    "Colorado Springs": (38.8339, -104.8214),
    "Miami": (25.7617, -80.1918),
    "Raleigh": (35.7796, -78.6382),
    "Omaha": (41.2565, -95.9345),
    "Long Beach": (33.7701, -118.1937),
    "Virginia Beach": (36.8529, -75.9780),
    "Oakland": (37.8044, -122.2712),
    "Minneapolis": (44.9778, -93.2650),
    "Tulsa": (36.1539, -95.9928),
    "Tampa": (27.9506, -82.4572),
    "Arlington": (32.7357, -97.1081),
    "New Orleans": (29.9511, -90.0715),
    "Wichita": (37.6872, -97.3301)
}

depart = input("Quel est votre ville de départ : ")
arrivee = input("Quel est votre ville d'arrivée : ")

categorie = ""
while categorie.lower() not in ["hélice", "turbopropulseur", "jet"]:
    categorie = input("Quel type d’avion veux-tu utiliser ? (hélice / turbopropulseur/ jet) : ").strip().lower()

# Filtrage
avions_filtres = [avion for avion in avions if avion.categorie == categorie]

#  Affichage des avions disponibles
print("\nAvions disponibles :")
for i, avion in enumerate(avions_filtres, 1):
    print(f"{i}. {avion}")

# Choix de l'avion
choix = -1
while choix < 1 or choix > len(avions_filtres):
    try:
        choix = int(input(f"\nChoisissez un avion (1 à {len(avions_filtres)}) : "))
    except ValueError:
        continue

avion_selectionne = avions_filtres[choix - 1]
print(f"\n Vous avez selectionné : {avion_selectionne.nom} (vent max : {avion_selectionne.vitesse_vent_max} km/h)")


def trouver_waypoint_alternatif(wp_id, lat, lon, avion, cle_api, waypoints_dict, partition, geometry,
                                rayon_initial=50000, rayon_max=300000, increment=25000):
    """
    Cherche un waypoint alternatif proche avec météo acceptable.
    Étend progressivement le rayon de recherche si aucun n'est trouvé.
    """
    from geopy.distance import distance

    rayon = rayon_initial
    while rayon <= rayon_max:
        voisins = []
        for id_voisin, (lat_v, lon_v) in waypoints_dict.items():
            if id_voisin == wp_id:
                continue
            dist = distance((lat, lon), (lat_v, lon_v)).meters
            if dist <= rayon:
                voisins.append((id_voisin, lat_v, lon_v, dist))

        # Trier les voisins par distance
        voisins.sort(key=lambda x: x[3])

        # Tester la météo sur chaque voisin
        for id_v, lat_v, lon_v, _ in voisins:
            meteo = DonneesMeteo(cle_api, (lat_v, lon_v))
            meteo.fetch()
            infos = meteo.get_donnees()
            if avion.en_capaciter_de_voler(infos.get('vent_kph', 0)):
                return (id_v, lat_v, lon_v)

        rayon += increment

    # Aucun voisin acceptable trouvé

    return (wp_id, lat, lon)


waypoints_liste = charger_waypoints("Data/Waypoints.csv")

waypoints_dict = {wp_id: (lat, lon) for wp_id, lat, lon in waypoints_liste}

partition, geometry = grille_partition(waypoints_dict, res=(10, 10))

chemin = selectionner_waypoints_plus_proches_par_segments(waypoints_dict, villes_coordonnees[depart],villes_coordonnees[arrivee] , partition, geometry)

chemin_robuste = []
for wp_id, lat, lon in chemin:
    meteo = DonneesMeteo(cle_api, (lat, lon))
    meteo.fetch()
    infos = meteo.get_donnees()
    vent = infos.get('vent_kph', 0)
    if avion_selectionne.en_capaciter_de_voler(vent):
        chemin_robuste.append((wp_id, lat, lon))
    else:
        alt = trouver_waypoint_alternatif(wp_id, lat, lon, avion_selectionne, cle_api, waypoints_dict, partition, geometry)
        chemin_robuste.append(alt)
#

def calculer_distance(trajet):
    #Calcule la distance totale en kilomètres d'un trajet donné sous forme de liste de (id, lat, lon)
    distance_totale = 0.0
    for i in range(len(trajet) - 1):
        coord1 = (trajet[i][1], trajet[i][2])  # (lat, lon)
        coord2 = (trajet[i + 1][1], trajet[i + 1][2])
        distance_totale += geodesic(coord1, coord2).kilometers
    return distance_totale


def calcul_temps_vol(trajet, vitesse_km_h):
    distance = calculer_distance(trajet)
    temps_heures = distance / vitesse_km_h
    heures = int(temps_heures)
    minutes = int((temps_heures - heures) * 60)

    #Retourne le temps de vol estimé en heures, minutes
    return heures, minutes, distance


h, m, d = calcul_temps_vol(chemin_robuste, avion_selectionne.vitesse_croisiere)
print(f"Distance totale estimée : {d:.1f} km")
print(f"Temps de vol estimé : {h} h {m} min")

# Remplacer chemin par chemin_robuste pour la carte
carte = tracer_trajet_meteo_dynamique(chemin_robuste, cle_api, avion_selectionne)
carte.save("trajet_robuste.html")

