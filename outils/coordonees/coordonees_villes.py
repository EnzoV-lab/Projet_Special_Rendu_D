import pandas as pd  # Pour lire et manipuler des fichiers CSV

# Chargement du fichier contenant les villes et leurs coordonnées géographiques
VILLES_CSV = "Data/Villes.csv"  # Le chemin vers le fichier CSV
df_villes = pd.read_csv(VILLES_CSV)  # Chargement des données dans un DataFrame

def transformer_nom_en_coordonnees(ville):
    """
    Recherche les coordonnées géographiques (latitude, longitude) d'une ville donnée.

    :param ville: Nom de la ville (insensible à la casse)
    :return: Tuple (lat, lng) si la ville est trouvée, sinon None
    """
    # On cherche une ligne dont le nom de ville correspond (casse ignorée)
    match = df_villes[df_villes['city'].str.lower() == ville.lower()]

    # Si aucune correspondance n’est trouvée, on retourne None
    if match.empty:
        return None

    # Si trouvé, on retourne la première correspondance (lat, lon)
    return match.iloc[0]['lat'], match.iloc[0]['lng']
