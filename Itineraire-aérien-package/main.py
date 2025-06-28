"""
main.py
=======

Ce script constitue le cœur de l'application Streamlit pour la simulation de trajectoires aériennes
en fonction des conditions météorologiques et des avions disponibles.

Fonctionnalités principales :
-----------------------------
- Sélection interactive des villes de départ et d’arrivée.
- Calcul d’un itinéraire direct (sans contrainte météo).
- Choix de l’avion (libre ou filtré par vent admissible).
- Calcul d’un itinéraire dévié basé sur les contraintes météo réelles.
- Affichage d’une carte interactive avec les trajets (via Folium).
- Résumé synthétique de la simulation.

Modules utilisés :
------------------
- :mod:`pandas` pour la lecture des CSV.
- :mod:`streamlit` pour l’interface web.
- :mod:`folium` pour la cartographie interactive.
- :mod:`Itineraire-aérien-package.manager.*` pour la logique de calcul métier.
- :mod:`outils.coordonees.coordonees_villes` pour la géolocalisation.

Variables globales :
--------------------
CLE_API : str
    Clé API pour accéder au service météo.
WAYPOINT_CSV : str
    Fichier contenant les waypoints (points intermédiaires de navigation).
VILLES_CSV : str
    Fichier contenant les villes et leurs coordonnées.
AVIONS_CSV : str
    Fichier contenant les données sur les avions disponibles.

Notes :
-------
- Le fichier doit être exécuté avec `streamlit run main.py`.
- Nécessite une connexion Internet pour interroger l’API météo.
- L’utilisateur doit sélectionner deux villes différentes.

"""

# === Import des bibliothèques nécessaires ===
import pandas as pd  # Pour manipuler les fichiers CSV
import streamlit as st  # Pour l'application web interactive
from streamlit.components.v1 import html  # Pour afficher du HTML brut
from pathlib import Path
# === Importation des Itineraire-aérien-package personnalisés ===
import ItineraireAerien
from ItineraireAerien.Avion import AvionManager
from ItineraireAerien.coordonees import transformer_nom_en_coordonnees
from ItineraireAerien.Meteo import DonneesMeteo
from ItineraireAerien.Meteo import MeteoManager
from ItineraireAerien.Visualisation import NavigationManager
from ItineraireAerien.Visualisation import TrajectoireManager
from ItineraireAerien.Visualisation import VisualisationManager
import os

# Constantes globales du projet
CLE_API = "d9ac5ac56f3d4768abd232315250506"

BASE_DIR = Path(__file__).resolve().parent
WAYPOINT_CSV = BASE_DIR / "Data" / "Waypoints.csv"
VILLES_CSV = BASE_DIR / "Data" / "Villes.csv"
AVIONS_CSV = BASE_DIR / "Data" / "avions.csv"
cartes_dir = BASE_DIR / "Itineraire-aérien-package" / "Cartes"


# Chargement des villes disponibles depuis le CSV
# (doit contenir les colonnes : city, lat, lng)
df_villes = pd.read_csv(VILLES_CSV)

# Initialisation des gestionnaires (managers)
avion_manager = AvionManager(AVIONS_CSV)  #: Gestionnaire des avions
navigation_manager = NavigationManager(WAYPOINT_CSV)  #: Gestionnaire de navigation
meteo_manager = MeteoManager(CLE_API)  #: Gestionnaire météo
trajectoire_manager = TrajectoireManager()  #: Lissage des trajectoires
visualisation_manager = VisualisationManager()  #: Génération de cartes

# --- Interface utilisateur Streamlit ---

# Configuration de la page Streamlit
st.set_page_config(page_title="Simulation de Trajectoire Aérienne", layout="wide")
st.title("Simulation de Trajectoire Aérienne avec Météo")
st.sidebar.markdown("[📄 Consulter la documentation Sphinx](http://localhost:63342/Projet_Special_Rendu_D/docs/build/html/index.html)")
st.sidebar.header("Paramètres de vol")

# === Sélection des villes de départ et d'arrivée ===
ville_depart = st.sidebar.selectbox("Ville de départ", df_villes['city'].sort_values().unique())
ville_arrivee = st.sidebar.selectbox("Ville d’arrivée", df_villes['city'].sort_values().unique())

# Validation : les deux villes doivent être différentes
if ville_depart == ville_arrivee:
    st.warning("Les villes doivent être différentes.")
    st.stop()

# Transformation des noms de villes en coordonnées GPS
depart = transformer_nom_en_coordonnees(ville_depart)
arrivee = transformer_nom_en_coordonnees(ville_arrivee)

if not depart or not arrivee:
    st.error("Ville introuvable dans la base de données.")
    st.stop()

# Initialisation de l'état de session pour stocker les résultats entre les actions utilisateur
if "itin_droit_lisse" not in st.session_state:
    st.session_state.itin_droit_lisse = None
    st.session_state.meteo_droit = None
    st.session_state.vent_max_ref = None

# --- Bouton : Calcul de l'itinéraire direct sans contrainte météo ---
if st.sidebar.button("Lancer le calcul de l'itinéraire de référence"):
    st.subheader("Calcul de l’itinéraire de référence (sans contraintes)")
    with st.spinner("Calcul en cours (le calcul peut prendre quelques minutes)..."):
        # Trace un itinéraire direct sans filtre météo (seuil très élevé)
        itin_droit, meteo_droit, vent_max_ref = navigation_manager.tracer_chemin(
            depart, arrivee, seuil=10000,  # Seuil très haut pour ignorer les contraintes
            verifier_meteo_callback=lambda coords, seuil: meteo_manager.verifier_conditions_meteo(coords, seuil)
        )
        # Lissage de la trajectoire pour un affichage plus esthétique
        itin_droit_lisse = trajectoire_manager.trajectoire_lisse_avec_controles(itin_droit)

        # Sauvegarde dans la session
        st.session_state.itin_droit_lisse = itin_droit_lisse
        st.session_state.meteo_droit = meteo_droit
        st.session_state.vent_max_ref = vent_max_ref

    st.success(f"Itinéraire de référence calculé | Vent max détecté : {vent_max_ref:.1f} km/h")

# --- Si itinéraire de référence disponible, proposer un avion ---
if st.session_state.itin_droit_lisse:
    vent_max_ref = st.session_state.vent_max_ref
    itin_droit_lisse = st.session_state.itin_droit_lisse

    st.subheader("Choix de l'avion")
    mode = st.radio("Mode de sélection de l'avion :", ["Choix libre (mode 1)", "Filtré par conditions météo (mode 2)"])

    type_avions = ["-- Sélectionner un type --"] + list(avion_manager.df['type'].unique())
    type_choisi = st.selectbox("Type d’avion :", type_avions)

    if type_choisi == "-- Sélectionner un type --":
        st.warning("Veuillez sélectionner un type d’avion.")
        st.stop()

    if mode == "Choix libre (mode 1)":
        avions_type = avion_manager.df[avion_manager.df['type'] == type_choisi]
        if avions_type.empty:
            st.warning("Aucun avion de ce type n’est disponible.")
            st.stop()
        nom_avion = st.selectbox("Modèle d’avion :", avions_type['nom'].values)
        avion = avions_type[avions_type['nom'] == nom_avion].iloc[0]
    else:
        # Mode 2 : filtrer selon le vent détecté sur l’itinéraire de référence
        borne_min = int(max(0, vent_max_ref - 4))
        borne_max = int(vent_max_ref - 2)
        st.info(f"Recherche des avions supportant entre {borne_min} et {borne_max} km/h de vent.")

        avions_filtres = avion_manager.df[
            (avion_manager.df['type'] == type_choisi) &
            (avion_manager.df['vitesse_vent_admissible'] >= borne_min) &
            (avion_manager.df['vitesse_vent_admissible'] <= borne_max)
        ]
        if avions_filtres.empty:
            st.warning("Aucun avion de ce type ne supporte le vent détecté.")
            st.stop()

        avions_filtres['affichage'] = avions_filtres.apply(
            lambda row: f"{row['nom']} (vent max: {row['vitesse_vent_admissible']} km/h)", axis=1
        )
        nom_affichage = st.selectbox("Modèle d’avion :", avions_filtres['affichage'].values)
        nom_avion = nom_affichage.split(" (")[0]
        avion = avions_filtres[avions_filtres['nom'] == nom_avion].iloc[0]

    # Récupération des caractéristiques de l'avion
    vitesse_admi = avion['vitesse_vent_admissible']
    vitesse_avion = avion['vitesse_de_avion']
    st.success(f"Avion sélectionné : {nom_avion} (Vent max admissible : {vitesse_admi} km/h)")

    # --- Bouton : Calcul d’itinéraire dévié avec météo réelle ---
    if st.button("Lancer le calcul de l’itinéraire avec déviation"):
        st.subheader("Calcul de l’itinéraire déviée")
        with st.spinner("Déviation en cours (le calcul peut prendre quelques minutes)..."):
            itin_devie, meteo_devie, vent_max_devie = navigation_manager.tracer_chemin(
                depart, arrivee, seuil=vitesse_admi,
                verifier_meteo_callback=lambda coords, seuil: meteo_manager.verifier_conditions_meteo(coords, seuil)
            )
            itin_devie_lisse = trajectoire_manager.trajectoire_lisse_avec_controles(itin_devie)

        st.success(f"Itinéraire dévié terminé | Vent max détecté : {vent_max_devie:.1f} km/h")

        # Visualisation de la carte contenant les deux itinéraires
        st.info("Le trajet **bleu** correspond à l’itinéraire **de référence**, \n"
                 "et le trajet **violet** correspond à l’itinéraire **dévié**.")

        st.subheader("Visualisation")
        carte_html = visualisation_manager.afficher_double_itineraire(
            itin_droit_lisse, itin_devie_lisse, meteo_devie, seuil=vitesse_admi
        )
        carte_path = cartes_dir / "carte_resultat.html"
        os.makedirs(os.path.dirname(carte_path), exist_ok=True)
        carte_html.save(str(carte_path))

        with open(carte_path, "r", encoding="utf-8") as f:
            html_map = f.read()
        html(html_map, height=600)

        # Résumé synthétique de la simulation
        st.subheader("Résumé de la simulation")
        st.markdown(f"""
        - Ville de départ : `{ville_depart}`
        - Ville d’arrivée : `{ville_arrivee}`
        - Avion sélectionné : `{nom_avion}`
        - Vent max admissible avion : `{vitesse_admi} km/h`
        - Vent max sur itinéraire direct : `{vent_max_ref:.1f} km/h`
        - Vent max sur itinéraire dévié : `{vent_max_devie:.1f} km/h`
        """)

        # Bouton pour relancer une simulation depuis le début
        if st.button("🔁 Nouvelle simulation"):
            st.session_state.clear()
            st.experimental_rerun()
