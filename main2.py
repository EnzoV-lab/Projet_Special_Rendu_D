import csv
from geopy.distance import geodesic
import folium
from math import floor
import numpy as np
import pandas as pd
import requests
import os
import math
import time

cle_api ="d9ac5ac56f3d4768abd232315250506"


filepath = os.path.join("Data", "Waypoints.csv")
df = pd.read_csv(filepath)
north_america_codes = ['US', 'CA', 'MX']
df_na = df[df['iso_country'].isin(north_america_codes)]
waypoints = df_na[['ident', 'latitude_deg', 'longitude_deg', 'iso_country']]
waypoints.to_csv("Data/Waypoints.csv", index=False)

filepath = os.path.join("Data", "Villes.csv")
de = pd.read_csv(filepath)
Villes = de[['city', 'lat', 'lng',]]
Villes.to_csv("Data/Villes.csv", index=False)

filepath = os.path.join("Data", "avions.csv")
da = pd.read_csv("Data/avions.csv")




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

def trouver_point_suivant(depart, arrivee, points_utilises, fichier_csv='Data/Waypoints.csv', rayon_max_km=200):
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

    # Garder les points dans la direction (angle ≤ 179°) et proches (distance ≤ rayon_max_km)
    df_filtre = df[(df['angle'] <= math.radians(179)) & (df['distance'] <= rayon_max_km)]

    if df_filtre.empty:
        return None

    # Choisir le point le plus aligné (angle minimal)
    point_choisi = df_filtre.loc[df_filtre['angle'].idxmin()]
    return (point_choisi['latitude_deg'], point_choisi['longitude_deg'])





def verifier_conditions_meteo(coordonnees, cle_api, seuil_vent_kph, max_depassements=2, pause=1):
    """
    Vérifie les conditions météo pour un segment.

    Args:
        coordonnees: liste de (lat, lon)
        cle_api: str, clé WeatherAPI
        seuil_vent_kph: float, vent max autorisé
        max_depassements: int, nombre max de points dépassant le seuil
        pause: float, pause entre les appels API

    Returns:
        tuple:
            - état (bool): True si segment valide, False sinon
            - liste des coordonnées [(lat, lon), ...]
            - liste des données météo [(lat, lon, vent_kph ou None), ...]
    """
    depassements = 0
    liste_coords = []
    donnees_meteo_segment = []
    vent_max = 0

    for lat, lon in coordonnees:
        meteo = DonneesMeteo(cle_api, (lat, lon))
        try:
            meteo.fetch()
            donnees = meteo.get_donnees()
            vent = donnees.get("vent_kph", None)
            liste_coords.append((lat, lon))
            donnees_meteo_segment.append((lat, lon, vent))
            if vent > vent_max:
                vent_max = vent

            if vent is not None and vent > seuil_vent_kph:

                depassements += 1
                if depassements > max_depassements:
                    return False, liste_coords, donnees_meteo_segment,vent_max

        except Exception as e:
            print(f"Erreur pour le point ({lat}, {lon}) : {e}")
            liste_coords.append((lat, lon))
            donnees_meteo_segment.append((lat, lon, None))

        time.sleep(pause)

    return True, liste_coords, donnees_meteo_segment, vent_max




def tracer_chemin(depart, arrivee, seuil):
    point = depart
    liste_point_utilisees = []
    liste_finale = []
    liste_points_meteo = []
    vent_max_tot = 0
    print(f"🔍 Distance initiale au but : {distance(point, arrivee)} km")
    while distance(point, arrivee) > 75:

        print(f" Distance actuelle entre {point} et {arrivee} : {distance(point, arrivee)} km")

        prochain_point = trouver_point_suivant(point, arrivee, liste_point_utilisees)

        if prochain_point is None:
            print(" Aucun prochain point valide trouvé, une barriere se situe sur le chemin, voyage impossible avec cet avion.")
            break

        print("➡️ Test du segment vers", prochain_point)

        coord_seg = intercaler_points(point[0], point[1],
                                      prochain_point[0], prochain_point[1],
                                      6)

        Etat, liste_coordonnees,donnees_meteo,vent_max = verifier_conditions_meteo(coord_seg, cle_api, seuil)
        if vent_max_tot < vent_max:
            vent_max_tot = vent_max

        print(f"   → État météo valide ?", Etat)



        if Etat:
            liste_finale.append(liste_coordonnees)
            liste_points_meteo.extend(donnees_meteo)
            liste_point_utilisees.append(prochain_point)
            point = prochain_point
        else:
            print("   ⚠️ Segment NON valide, on cherche un autre point...")
            liste_point_utilisees.append(prochain_point)
            continue

    liste_finale.append([arrivee])
    print(liste_finale)
    return liste_finale, liste_points_meteo,vent_max_tot




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

def choix_avion_mode_1(fichier_csv="Data/avions.csv"):

    df = pd.read_csv(fichier_csv)

    types_disponibles = da['type'].unique()
    print("Types d’avions disponibles :")
    liste_type=[]
    for t in types_disponibles:
        liste_type.append(t)
        print(f" - {t}")
    type_choisi = ""
    while type_choisi not in liste_type:
        type_choisi = input("Entrez un type d’avion : ").strip().lower()

    da_type = da[da['type'] == type_choisi]


    print("\nAvions disponibles :")
    liste_avion = []
    for _, row in da_type.iterrows():
        nom = row['nom']
        vent = row['vitesse_vent_admissible']
        liste_avion.append(nom)
        print(f" - {nom} (vent max admissible : {vent} km/h)")

    nom_choisi = ""
    while nom_choisi not in liste_avion:
        nom_choisi = input("Entrez le nom de l’avion : ").strip()

    avion = da_type[da_type['nom'] == nom_choisi].iloc[0]

    vitesse_admi = avion['vitesse_vent_admissible']
    vitesse_avion = avion['vitesse_de_avion']
    return vitesse_admi, vitesse_avion

"""Mistral, prompt " je veux que la proposition d'avion faite soit des avions avec une vitesse de vent admissible entre 2 chiffres défini en parametre de la fonction
 avec la meme structure et la meme sortie que le mode 1"""



def choix_avion_mode_2(fichier_csv="Data/avions.csv", borne_min=0, borne_max=100):
    da = pd.read_csv(fichier_csv)

    types_disponibles = da['type'].unique()
    print("Types d’avions disponibles :")
    for t in types_disponibles:
        print(f" - {t}")

    # Boucle jusqu’à trouver un type avec au moins un avion dans les bornes
    while True:
        type_choisi = input("Entrez un type d’avion : ").strip().lower()

        if type_choisi not in types_disponibles:
            print("Type invalide. Veuillez réessayer.")
            continue

        # Filtrage selon le type choisi et les bornes
        da_type = da[
            (da['type'] == type_choisi) &
            (da['vitesse_vent_admissible'] >= borne_min) &
            (da['vitesse_vent_admissible'] <= borne_max)
        ]

        if da_type.empty:
            print(f"Aucun avion trouvé pour le type '{type_choisi}' avec vent admissible entre {borne_min} et {borne_max} km/h.")
            print("Veuillez choisir un autre type d’avion.\n")
        else:
            break  # On a trouvé un type valide avec au moins un avion

    # Affichage des avions disponibles
    print("\nAvions disponibles :")
    liste_avion = []
    for _, row in da_type.iterrows():
        nom = row['nom']
        vent = row['vitesse_vent_admissible']
        liste_avion.append(nom)
        print(f" - {nom} (vent max admissible : {vent} km/h)")

    # Choix du nom
    nom_choisi = ""
    while nom_choisi not in liste_avion:
        nom_choisi = input("Entrez le nom de l’avion : ").strip()

    avion = da_type[da_type['nom'] == nom_choisi].iloc[0]
    vitesse_admi = avion['vitesse_vent_admissible']
    vitesse_avion = avion['vitesse_de_avion']

    return vitesse_admi, vitesse_avion


def choix_du_mode(borne_min, borne_max):
    reponse_possible = ["1", "2"]
    reponse_mode = ""
    while reponse_mode not in reponse_possible:
        reponse_mode = input(
            "A présent veuillez choisir votre mode\n 1 - Proposer n'importe quel avion\n 2 - Proposer uniquement les avions susceptibles à une déviation\n Reponse :  ")

    if reponse_mode == "1":
        return choix_avion_mode_1()
    else:
        return choix_avion_mode_2(fichier_csv="Data/avions.csv", borne_min=borne_min, borne_max=borne_max)







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

def transformer_nom_en_coordonnees (ville):
    match = de[de['city'].str.lower() == ville]
    return match.iloc[0]['lat'], match.iloc[0]['lng']



def main ():
    select_depart = input("Entrez une ville U.S de départ : ").strip().lower()
    select_arrivee = input("Entrez une ville U.S de d'arrivée' : ").strip().lower()

    depart = transformer_nom_en_coordonnees(select_depart)
    arrivee = transformer_nom_en_coordonnees(select_arrivee)

    print("L'itinéraire de référence est en cours de chargement...  ")
    itineraire_droit, points_meteo_droit,vent_max_total = tracer_chemin(depart, arrivee,10000)
    borne_inferieur = vent_max_total-5
    borne_superieur = vent_max_total
    carte_droit = afficher_meteo_sur_carte(points_meteo_droit,10000, itineraire=itineraire_droit)
    carte_droit.save("carte_itinéraire_droit.html")
    print("L'itinéraire de référence est terminé")

    vitesse_admi, vitesse_avion = choix_du_mode(borne_inferieur, borne_superieur)

    print("L'itinéraire déviée est en cours de chargement...")
    itineraire_deviee, points_meteo_deviee,vent_max_total = tracer_chemin(depart, arrivee,vitesse_admi)
    carte_deviee = afficher_meteo_sur_carte(points_meteo_deviee,vitesse_admi, itineraire=itineraire_deviee)
    carte_deviee.save("carte_itinéraire_deviée.html")
    print("L'itinéraire déviée est terminé")


main()







