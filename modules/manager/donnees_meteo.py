import requests


class DonneesMeteo:
    """
    Classe pour interroger l'API WeatherAPI et récupérer les données météo actuelles pour une coordonnée donnée.
    """
    def __init__(self, cle_api, coordonnees=None):
        """
        Initialise un objet DonneesMeteo.
        :param cle_api: clé API pour accéder à weatherapi.com
        :param coordonnees: tuple (latitude, longitude) des coordonnées à interroger
        """
        self.coordonnees = coordonnees  # Coordonnées géographiques de la zone à analyser
        self.cle_api = cle_api  # Clé API fournie par WeatherAPI
        self.donnees = None  # Stockera les données météo récupérées

    def fetch(self):
        """
        Envoie une requête HTTP à WeatherAPI pour obtenir les données météo actuelles de la coordonnée.
        Résultat stocké dans self.donnees en format JSON.
        """
        if not self.coordonnees:
            raise ValueError("Coordonnées requises")  # Impossible de faire une requête sans position

        lat, lon = self.coordonnees  # On décompose le tuple
        url = f"http://api.weatherapi.com/v1/current.json?key={self.cle_api}&q={lat},{lon}"

        response = requests.get(url)  # Requête GET vers l’API météo

        if response.status_code == 200:
            self.donnees = response.json()  # Réponse correcte : on convertit en dictionnaire Python
        else:
            raise RuntimeError("Erreur météo")  # Erreur HTTP ou problème d’API

    def get_donnees(self):
        """
        Extrait les données utiles de la réponse météo et les retourne sous forme de dictionnaire.
        :return: dictionnaire contenant vitesse du vent, direction, conditions météo, etc.
        """
        if not self.donnees:
            return {}  # Si aucune donnée n’a encore été récupérée

        current = self.donnees.get("current", {})  # On se concentre sur la section "current" du JSON
        condition = current.get("condition", {}).get("text", "")  # Texte descriptif des conditions (ex: "Sunny")

        return {
            "vent_kph": current.get("wind_kph"),                     # Vitesse du vent en km/h
            "direction_cardinal": current.get("wind_dir", "N/A"),   # Direction du vent en points cardinaux (ex: NE)
            "direction_deg": current.get("wind_degree", 0),         # Direction du vent en degrés
            "condition": condition,                                 # État météo général (ex: "Cloudy")
            "precip_mm": current.get("precip_mm", 0)                # Précipitations en mm
        }
