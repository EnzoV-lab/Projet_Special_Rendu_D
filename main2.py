import csv
from geopy.distance import geodesic
import folium
from math import floor
import numpy as np
import pandas as pd
import requests
import os

cle_api ="d9ac5ac56f3d4768abd232315250506"


filepath = os.path.join("Data", "Waypoints.csv")
df = pd.read_csv(filepath)
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


import pandas as pd
import math


import pandas as pd
import math

def calcul_angle(depart, waypoint, arrivee):
    """Calcule l'angle (en radians) entre les vecteurs départ→waypoint et départ→arrivée."""
    v1 = (waypoint[0] - depart[0], waypoint[1] - depart[1])
    v2 = (arrivee[0] - depart[0], arrivee[1] - depart[1])
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    norm1 = math.hypot(*v1)
    norm2 = math.hypot(*v2)
    if norm1 == 0 or norm2 == 0:
        return float('inf')
    cos_theta = dot / (norm1 * norm2)
    return math.acos(max(min(cos_theta, 1), -1))  # Clamp to avoid domain errors

def distance(p1, p2):
    """Renvoie la distance entre deux points (approximation en km)."""
    R = 6371  # rayon de la Terre
    lat1, lon1 = map(math.radians, p1)
    lat2, lon2 = map(math.radians, p2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def trouver_point_suivant(depart, arrivee, points_utilises, fichier_csv='Data/Waypoints.csv', rayon_max_km=100):
    """
    Trouve un point proche de `depart` (mais pas utilisé), dans la direction générale de `arrivee`.
    """
    # Charger les waypoints
    df = pd.read_csv(fichier_csv)
    df = df[['latitude_deg', 'longitude_deg']].dropna()

    # Supprimer les points déjà utilisés
    df = df[~df.apply(lambda row: (row['latitude_deg'], row['longitude_deg']) in points_utilises, axis=1)]

    # Supprimer le point d’arrivée si jamais il est dans le fichier
    df = df[~df.apply(lambda row: (round(row['latitude_deg'], 5), round(row['longitude_deg'], 5)) == (round(arrivee[0], 5), round(arrivee[1], 5)), axis=1)]

    if df.empty:
        return None

    # Ajouter colonnes "angle" et "distance"
    df['angle'] = df.apply(lambda row: calcul_angle(depart, (row['latitude_deg'], row['longitude_deg']), arrivee), axis=1)
    df['distance'] = df.apply(lambda row: distance(depart, (row['latitude_deg'], row['longitude_deg'])), axis=1)

    # Garder les points dans la direction (angle ≤ 90°) et proches (distance ≤ rayon_max_km)
    df_filtre = df[(df['angle'] <= math.pi / 2) & (df['distance'] <= rayon_max_km)]

    if df_filtre.empty:
        return None

    # Choisir le point le plus aligné (angle minimal)
    point_choisi = df_filtre.loc[df_filtre['angle'].idxmin()]
    return (point_choisi['latitude_deg'], point_choisi['longitude_deg'])


import time  # pour respecter les limites d'appels à l'API


def verifier_conditions_meteo(coordonnees, cle_api, seuil_vent_kph=13, max_depassements=4, pause=1):
    depassements = 0
    donnees_meteo_segment = []

    for lat, lon in coordonnees:
        meteo = DonneesMeteo(cle_api, (lat, lon))
        try:
            meteo.fetch()
            donnees = meteo.get_donnees()
            vent = donnees.get("vent_kph", 0)
            donnees_meteo_segment.append((lat, lon, vent))  # ← stocker vent

            if vent is not None and vent > seuil_vent_kph:
                depassements += 1

            if depassements > max_depassements:
                return False, donnees_meteo_segment

        except Exception as e:
            print(f"Erreur pour le point ({lat}, {lon}) : {e}")
            donnees_meteo_segment.append((lat, lon, None))  # ← None si erreur

        time.sleep(pause)

    return True, donnees_meteo_segment



def tracer_chemin(depart, arrivee, seuil):
    point = depart
    liste_point_utilisees = []
    liste_finale = []
    liste_points_meteo = []  # ← ajouter

    while distance(point, arrivee) > 20:
        prochain_point = trouver_point_suivant(point, arrivee, liste_point_utilisees)

        if prochain_point is None:
            print("🔴 Aucun prochain point valide trouvé — arrêt.")
            break

        print("➡️ Test du segment vers", prochain_point)

        coord_seg = intercaler_points(point[0], point[1],
                                      prochain_point[0], prochain_point[1],
                                      10)

        Etat, donnees_meteo = verifier_conditions_meteo(coord_seg, cle_api, seuil)
        print(f"   → État météo valide ?", Etat)



        if Etat:
            liste_finale.append([point] + [(lat, lon) for lat, lon, _ in donnees_meteo] + [prochain_point])
            liste_points_meteo.extend(donnees_meteo)
            liste_point_utilisees.append(prochain_point)
            point = prochain_point
        else:
            print("   ⚠️ Segment NON valide, on cherche un autre point...")
            liste_point_utilisees.append(prochain_point)
            continue

    liste_finale.append([arrivee])
    return liste_finale, liste_points_meteo




class Avion:
    def __init__(self, nom, vitesse_vent_max, categorie):
        """
        Initialise un objet Avion.

        :param nom: Nom ou modèle de l'avion (str)
        :param vitesse_vent_max: Vitesse maximale de vent tolérée (en km/h)
        """
        self.nom = nom
        self.vitesse_vent_max = vitesse_vent_max
        self.categorie = categorie

    def en_capaciter_de_voler(self, vent_kph):
        """
        Vérifie si l'avion peut voler avec la vitesse de vent donnée.

        :param vent_kph: vitesse du vent en km/h (float)
        :return: True si l'avion peut voler, sinon False
        """
        return vent_kph <= self.vitesse_vent_max

    def __str__(self):
        return f"Avion {self.nom} (vent max: {self.vitesse_vent_max} km/h)"

    # === Création des avions ===


avions = [
    # Hélice
    Avion("Cessna 172", 18, "hélice"),
    Avion("Piper PA-28 Cherokee", 60, "hélice"),
    Avion("Diamond DA40", 65, "hélice"),

    # Turbopropulseur
    Avion("DHC-6 Twin Otter", 70, "turbopropulseur"),
    Avion("Beechcraft King Air 350", 80, "turbopropulseur"),
    Avion("ATR 72", 90, "turbopropulseur")
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

"""depart = input("Quel est votre ville de départ : ")
arrivee = input("Quel est votre ville d'arrivée : ")

categorie = ""
while categorie.lower() not in ["hélice", "turbopropulseur"]:
    categorie = input("Quel type d’avion veux-tu utiliser ? (hélice / turbopropulseur) : ").strip().lower()

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
print(f"\n Vous avez selectionné : {avion_selectionne.nom} (vent max : {avion_selectionne.vitesse_vent_max} km/h)")"""













import folium

def afficher_meteo_sur_carte(points_meteo,seuille, itineraire=None):
    if not points_meteo:
        raise ValueError("Aucune donnée météo à afficher.")

    lat_centre = sum(lat for lat, lon, vent in points_meteo) / len(points_meteo)
    lon_centre = sum(lon for lat, lon, vent in points_meteo) / len(points_meteo)
    carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=6)

    # Tracer itinéraire s'il est fourni
    if itineraire:
        for segment in itineraire:
            folium.PolyLine(segment, color="blue", weight=2).add_to(carte)

    # Tracer points météo
    for lat, lon, vent in points_meteo:
        couleur = "gray" if vent is None else (
            "green" if vent <= seuille else
            "red"
        )
        popup_text = "Vent : inconnu" if vent is None else f"Vent : {vent:.1f} km/h"
        folium.CircleMarker(
            location=(lat, lon),
            radius=5,
            color=couleur,
            fill=True,
            fill_color=couleur,
            popup=popup_text
        ).add_to(carte)

    return carte






depart = (47.6062, -122.3321)
arrivee = (45.5152, -122.6784)


"""itineraire, points_meteo = tracer_chemin(depart, arrivee, seuil=18)
carte = afficher_meteo_sur_carte(points_meteo,15, itineraire=itineraire)
carte.save("carte_avec_meteo_autre.html")"""

itineraire1, points_meteo1 = tracer_chemin(depart, arrivee, seuil=40)
carte1 = afficher_meteo_sur_carte(points_meteo1,15, itineraire=itineraire1)
carte1.save("carte_avec_meteo_autre1.html")

itineraire, points_meteo = tracer_chemin(depart, arrivee, seuil=15)
carte = afficher_meteo_sur_carte(points_meteo,15, itineraire=itineraire)
carte.save("carte_avec_meteo_autre.html")








