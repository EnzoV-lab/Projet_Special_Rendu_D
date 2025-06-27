"""
Module pour convertir un nom de ville en coordonnées géographiques à partir d'un fichier CSV.

Ce module charge une base de données de villes (`Data/Villes.csv`) et expose une fonction
pour rechercher les coordonnées GPS d’une ville donnée.

Attributes
----------
VILLES_CSV : str
    Chemin vers le fichier CSV contenant les villes et leurs coordonnées.
df_villes : pandas.DataFrame
    Données chargées à partir du fichier CSV.
"""
import pandas as pd  # Pour lire et manipuler des fichiers CSV

# Chargement du fichier contenant les villes et leurs coordonnées géographiques
import os
# Le chemin vers le fichier CSV
VILLES_CSV = os.path.join(os.path.dirname(__file__), "../../Data/Villes.csv")
VILLES_CSV = os.path.abspath(VILLES_CSV)
df_villes = pd.read_csv(VILLES_CSV)  # Chargement des données dans un DataFrame

def transformer_nom_en_coordonnees(ville):
    """
    Recherche les coordonnées géographiques (latitude, longitude) d'une ville donnée.

    Parameters
    ----------
    ville : str
        Nom de la ville à rechercher (insensible à la casse).

    Returns
    -------
    tuple or None
        Tuple (latitude, longitude) si la ville est trouvée,
        None sinon.
    """
    # On cherche une ligne dont le nom de ville correspond (casse ignorée)
    match = df_villes[df_villes['city'].str.lower() == ville.lower()]

    # Si aucune correspondance n’est trouvée, on retourne None
    if match.empty:
        return None

    # Si trouvé, on retourne la première correspondance (lat, lon)
    return match.iloc[0]['lat'], match.iloc[0]['lng']
