import pandas as pd
import csv
from geopy.distance import geodesic
import folium
from math import floor
import numpy as np
import requests
import os
import streamlit as st
import math
import time

class AvionManager:
    def __init__(self, fichier_csv="Data/avions.csv"):
        self.fichier_csv = fichier_csv
        self.df = pd.read_csv(fichier_csv)

    def choix_avion_mode_1(self):
        types_disponibles = self.df['type'].unique()
        print("Types d’avions disponibles :")
        liste_type = []
        for t in types_disponibles:
            liste_type.append(t)
            print(f" - {t}")

        type_choisi = ""
        while type_choisi not in liste_type:
            type_choisi = input("Entrez un type d’avion : ").strip().lower()

        da_type = self.df[self.df['type'] == type_choisi]

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

    def choix_avion_mode_2(self, borne_min=0, borne_max=100):
        types_disponibles = self.df['type'].unique()
        print("Types d’avions disponibles :")
        for t in types_disponibles:
            print(f" - {t}")

        while True:
            type_choisi = input("Entrez un type d’avion : ").strip().lower()

            if type_choisi not in types_disponibles:
                print("Type invalide. Veuillez réessayer.")
                continue

            da_type = self.df[
                (self.df['type'] == type_choisi) &
                (self.df['vitesse_vent_admissible'] >= borne_min) &
                (self.df['vitesse_vent_admissible'] <= borne_max)
                ]

            if da_type.empty:
                print(
                    f"Aucun avion trouvé pour le type '{type_choisi}' avec vent admissible entre {borne_min} et {borne_max} km/h.")
                print("Veuillez choisir un autre type d’avion.\n")
            else:
                break

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

    def choix_du_mode(self, borne_min, borne_max):
        reponse_possible = ["1", "2"]
        reponse_mode = ""
        while reponse_mode not in reponse_possible:
            reponse_mode = input(
                "A présent veuillez choisir votre mode\n 1 - Proposer n'importe quel avion\n 2 - Proposer uniquement les avions susceptibles à une déviation\n Réponse :  ")

        if reponse_mode == "1":
            return self.choix_avion_mode_1()
        else:
            return self.choix_avion_mode_2(borne_min=borne_min, borne_max=borne_max)


class NavigationManager:
    def __init__(self, waypoint_csv='Data/Waypoints.csv', rayon_max_km=200):
        self.waypoint_csv = waypoint_csv
        self.rayon_max_km = rayon_max_km

    def distance(self, p1, p2):
        R = 6371
        lat1, lon1 = map(math.radians, p1)
        lat2, lon2 = map(math.radians, p2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def calcul_angle(self, depart, waypoint, arrivee):
        v1 = (waypoint[0] - depart[0], waypoint[1] - depart[1])
        v2 = (arrivee[0] - depart[0], arrivee[1] - depart[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        norm1 = math.hypot(*v1)
        norm2 = math.hypot(*v2)
        if norm1 == 0 or norm2 == 0:
            return float('inf')
        cos_theta = dot / (norm1 * norm2)
        return math.acos(max(min(cos_theta, 1), -1))

    def intercaler_points(self, lat1, lon1, lat2, lon2, n):
        points_intercale = []
        for i in range(1, n + 1):
            x = lat1 + i * (lat2 - lat1) / (n + 1)
            y = lon1 + i * (lon2 - lon1) / (n + 1)
            points_intercale.append((x, y))
        return points_intercale

    def charger_waypoints(self):
        df = pd.read_csv(self.waypoint_csv)
        return df[['ident', 'latitude_deg', 'longitude_deg']].dropna()

    def trouver_point_suivant(self, depart, arrivee, points_utilises):
        df = pd.read_csv(self.waypoint_csv)[['latitude_deg', 'longitude_deg']].dropna()
        df = df[~df.apply(lambda row: (row['latitude_deg'], row['longitude_deg']) in points_utilises, axis=1)]
        df = df[~df.apply(lambda row: (round(row['latitude_deg'], 5), round(row['longitude_deg'], 5)) == (round(arrivee[0], 5), round(arrivee[1], 5)), axis=1)]

        if df.empty:
            return None

        df['angle'] = df.apply(lambda row: self.calcul_angle(depart, (row['latitude_deg'], row['longitude_deg']), arrivee), axis=1)
        df['distance'] = df.apply(lambda row: self.distance(depart, (row['latitude_deg'], row['longitude_deg'])), axis=1)

        df_filtre = df[(df['angle'] <= math.radians(179)) & (df['distance'] <= self.rayon_max_km)]

        if df_filtre.empty:
            return None

        point_choisi = df_filtre.loc[df_filtre['angle'].idxmin()]
        return (point_choisi['latitude_deg'], point_choisi['longitude_deg'])

    def tracer_chemin(self, depart, arrivee, seuil, verifier_meteo_callback):
        point = depart
        liste_point_utilisees = []
        liste_finale = []
        liste_points_meteo = []
        vent_max_tot = 0

        while self.distance(point, arrivee) > 75:
            prochain_point = self.trouver_point_suivant(point, arrivee, liste_point_utilisees)
            if prochain_point is None:
                print("❌ Aucun point trouvé, barrière météo ou géographique.")
                break

            coord_seg = self.intercaler_points(point[0], point[1], prochain_point[0], prochain_point[1], 6)
            Etat, liste_coordonnees, donnees_meteo, vent_max = verifier_meteo_callback(coord_seg, seuil)

            if vent_max_tot < vent_max:
                vent_max_tot = vent_max

            if Etat:
                liste_finale.append(liste_coordonnees)
                liste_finale.append([prochain_point])
                liste_points_meteo.extend(donnees_meteo)
                liste_point_utilisees.append(prochain_point)
                point = prochain_point
            else:
                liste_point_utilisees.append(prochain_point)

        liste_finale.append([arrivee])
        return liste_finale, liste_points_meteo, vent_max_tot

class DonneesMeteo:
    def __init__(self, cle_api, coordonnees=None):
        self.coordonnees = coordonnees
        self.cle_api = cle_api
        self.donnees = None

    def fetch(self):
        if not self.coordonnees:
            raise ValueError("Coordonnées requises")
        lat, lon = self.coordonnees
        url = f"http://api.weatherapi.com/v1/current.json?key={self.cle_api}&q={lat},{lon}"
        response = requests.get(url)
        if response.status_code == 200:
            self.donnees = response.json()
        else:
            raise RuntimeError("Erreur météo")

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

class MeteoManager:
    def __init__(self, cle_api):
        self.cle_api = cle_api

    def verifier_conditions_meteo(self, coordonnees, seuil_vent_kph, max_depassements=2, pause=1):
        depassements = 0
        liste_coords = []
        donnees_meteo_segment = []
        vent_max = 0

        for lat, lon in coordonnees:
            meteo = DonneesMeteo(self.cle_api, (lat, lon))
            try:
                meteo.fetch()
                donnees = meteo.get_donnees()
                vent = donnees.get("vent_kph", None)
                liste_coords.append((lat, lon))
                donnees_meteo_segment.append((lat, lon, vent))
                if vent and vent > vent_max:
                    vent_max = vent
                if vent and vent > seuil_vent_kph:
                    depassements += 1
                    if depassements > max_depassements:
                        return False, liste_coords, donnees_meteo_segment, vent_max
            except Exception as e:
                liste_coords.append((lat, lon))
                donnees_meteo_segment.append((lat, lon, None))

            time.sleep(pause)

        return True, liste_coords, donnees_meteo_segment, vent_max

class TrajectoireManager:
    def __init__(self, n_points_bezier=40, auto_ctrl_ratio=0.1):
        self.n = n_points_bezier
        self.ratio = auto_ctrl_ratio

    def bezier_curve(self, p0, p1, p2):
        t = np.linspace(0, 1, self.n)
        return [
            (
                (1 - tt) ** 2 * p0[0] + 2 * (1 - tt) * tt * p1[0] + tt ** 2 * p2[0],
                (1 - tt) ** 2 * p0[1] + 2 * (1 - tt) * tt * p1[1] + tt ** 2 * p2[1]
            )
            for tt in t
        ]

    def auto_ctrl(self, p1, p2):
        p1 = np.array(p1, dtype=float)
        p2 = np.array(p2, dtype=float)
        return tuple(p1 + self.ratio * (p2 - p1))

    def trajectoire_lisse_avec_controles(self, data):
        if len(data) < 2:
            raise ValueError("Il faut au moins deux segments.")
        trajectoire = list(data[0])
        for i in range(len(data) - 1):
            p0 = data[i][-1]
            p2 = data[i + 1][0]
            ctrl = self.auto_ctrl(p0, p2)
            courbe = self.bezier_curve(p0, ctrl, p2)
            trajectoire.extend(courbe[1:])
            trajectoire.extend(data[i + 1][1:])
        return trajectoire


class VisualisationManager:
    def afficher_meteo_sur_carte(self, points_meteo, seuil, itineraire):
        lat_centre = sum(lat for lat, lon, vent in points_meteo) / len(points_meteo)
        lon_centre = sum(lon for lat, lon, vent in points_meteo) / len(points_meteo)
        carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=6)

        if itineraire:
            folium.PolyLine(itineraire, color="blue", weight=2).add_to(carte)

        for lat, lon, vent in points_meteo:
            couleur = "gray" if vent is None else ("green" if vent <= seuil else "red")
            popup = "Vent : inconnu" if vent is None else f"Vent : {vent:.1f} km/h"
            folium.CircleMarker(location=(lat, lon), radius=5, color=couleur,
                                fill=True, fill_color=couleur, popup=popup).add_to(carte)

        return carte

    def afficher_double_itineraire(self, itin1, itin2, points_meteo, seuil):
        lat_centre, lon_centre = itin1[0] if itin1 else itin2[0]
        carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=6)

        if itin1:
            folium.PolyLine(itin1, color="blue", weight=3, tooltip="Itinéraire référence").add_to(carte)
        if itin2:
            folium.PolyLine(itin2, color="purple", weight=3, tooltip="Itinéraire dévié").add_to(carte)

        for lat, lon, vent in points_meteo:
            couleur = "gray" if vent is None else ("green" if vent <= seuil else "red")
            popup = "Vent : inconnu" if vent is None else f"Vent : {vent:.1f} km/h"
            folium.CircleMarker(location=(lat, lon), radius=5, color=couleur,
                                fill=True, fill_color=couleur, popup=popup).add_to(carte)
        return carte



# Constantes
CLE_API = "d9ac5ac56f3d4768abd232315250506"
WAYPOINT_CSV = "Data/Waypoints.csv"
VILLES_CSV = "Data/Villes.csv"

def transformer_nom_en_coordonnees(ville, df_villes):
    match = df_villes[df_villes['city'].str.lower() == ville.lower()]
    if match.empty:
        raise ValueError(f"Ville '{ville}' non trouvée dans le fichier Villes.csv.")
    return match.iloc[0]['lat'], match.iloc[0]['lng']



# Constantes
CLE_API = "d9ac5ac56f3d4768abd232315250506"
WAYPOINT_CSV = "Data/Waypoints.csv"
VILLES_CSV = "Data/Villes.csv"
AVIONS_CSV = "Data/avions.csv"

# Initialisation
df_villes = pd.read_csv(VILLES_CSV)
avion_manager = AvionManager(AVIONS_CSV)
navigation_manager = NavigationManager(WAYPOINT_CSV)
meteo_manager = MeteoManager(CLE_API)
trajectoire_manager = TrajectoireManager()
visualisation_manager = VisualisationManager()


def transformer_nom_en_coordonnees(ville):
    match = df_villes[df_villes['city'].str.lower() == ville.lower()]
    if match.empty:
        return None
    return match.iloc[0]['lat'], match.iloc[0]['lng']


# --- Interface Streamlit ---
st.set_page_config(page_title="Simulation de Trajectoire Aérienne", layout="wide")
st.title("✈️ Simulation de Trajectoire Aérienne avec Météo")

st.sidebar.header("📍 Paramètres de vol")

ville_depart = st.sidebar.selectbox("Ville de départ", df_villes['city'].sort_values().unique())
ville_arrivee = st.sidebar.selectbox("Ville d’arrivée", df_villes['city'].sort_values().unique())

if ville_depart == ville_arrivee:
    st.warning("Les villes doivent être différentes.")
    st.stop()

depart = transformer_nom_en_coordonnees(ville_depart)
arrivee = transformer_nom_en_coordonnees(ville_arrivee)

if not depart or not arrivee:
    st.error("Ville introuvable dans la base de données.")
    st.stop()

# Itinéraire de référence
st.subheader("🧭 Calcul de l’itinéraire de référence (sans contraintes)")
with st.spinner("Calcul en cours..."):
    itin_droit, meteo_droit, vent_max_ref = navigation_manager.tracer_chemin(
        depart, arrivee, seuil=10000,
        verifier_meteo_callback=lambda coords, seuil: meteo_manager.verifier_conditions_meteo(coords, seuil)
    )
    itin_droit_lisse = trajectoire_manager.trajectoire_lisse_avec_controles(itin_droit)

st.success(f"Itinéraire de référence calculé ✅ | Vent max détecté : {vent_max_ref:.1f} km/h")

# Choix de l'avion
st.subheader("🛩️ Choix de l’avion selon le vent détecté")
type_avions = avion_manager.df['type'].unique()
type_choisi = st.selectbox("Type d’avion :", type_avions)

# Avions valides selon borne (comme dans ton code mode 2)
borne_min = vent_max_ref - 5
borne_max = vent_max_ref
avions_filtres = avion_manager.df[
    (avion_manager.df['type'] == type_choisi) &
    (avion_manager.df['vitesse_vent_admissible'] >= borne_min) &
    (avion_manager.df['vitesse_vent_admissible'] <= borne_max)
]

if avions_filtres.empty:
    st.warning("Aucun avion de ce type ne supporte le vent détecté.")
    st.stop()

nom_avion = st.selectbox("Modèle d’avion :", avions_filtres['nom'].values)
avion = avions_filtres[avions_filtres['nom'] == nom_avion].iloc[0]
vitesse_admi = avion['vitesse_vent_admissible']
vitesse_avion = avion['vitesse_de_avion']

st.success(f"Avion sélectionné : {nom_avion} (Vent max admissible : {vitesse_admi} km/h)")

# Calcul de l’itinéraire avec météo réelle
st.subheader("🌪️ Calcul de l’itinéraire en prenant en compte la météo")
with st.spinner("Déviation en cours..."):
    itin_devie, meteo_devie, vent_max_devie = navigation_manager.tracer_chemin(
        depart, arrivee, seuil=vitesse_admi,
        verifier_meteo_callback=lambda coords, seuil: meteo_manager.verifier_conditions_meteo(coords, seuil)
    )
    itin_devie_lisse = trajectoire_manager.trajectoire_lisse_avec_controles(itin_devie)

st.success(f"Itinéraire dévié terminé ✅ | Vent max détecté : {vent_max_devie:.1f} km/h")

# Affichage de la carte finale
st.subheader("🗺️ Visualisation")
carte_html = visualisation_manager.afficher_double_itineraire(
    itin_droit_lisse, itin_devie_lisse, meteo_devie, seuil=vitesse_admi
)
carte_html.save("carte_resultat.html")

from streamlit.components.v1 import html
with open("carte_resultat.html", "r", encoding="utf-8") as f:
    html_map = f.read()
html(html_map, height=600)