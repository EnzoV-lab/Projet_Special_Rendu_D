import requests


class DonneesMeteo:
    """
    Classe pour interroger l'API WeatherAPI et récupérer les données météo actuelles
    pour une position géographique donnée.

    :param cle_api: Clé API valide pour accéder à weatherapi.com.
    :type cle_api: str
    :param coordonnees: Coordonnées GPS au format (latitude, longitude).
    :type coordonnees: tuple[float, float] or None
    """
    def __init__(self, cle_api, coordonnees=None):
        """
        Initialise une instance de la classe DonneesMeteo.

        :param cle_api: Clé d’authentification pour WeatherAPI.
        :type cle_api: str
        :param coordonnees: Tuple contenant latitude et longitude (ex. : (45.5, -73.6)).
        :type coordonnees: tuple or None
        """
        self.coordonnees = coordonnees  # Coordonnées géographiques de la zone à analyser
        self.cle_api = cle_api  # Clé API fournie par WeatherAPI
        self.donnees = None  # Stockera les données météo récupérées

    def fetch(self):
        """
        Récupère les données météo actuelles pour les coordonnées fournies,
        en interrogeant l’API WeatherAPI.

        :raises ValueError: Si aucune coordonnée n’est spécifiée.
        :raises RuntimeError: Si la réponse de l’API est invalide ou échoue.
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
        Extrait et retourne les informations météo principales de la réponse de l’API.

        :return: Un dictionnaire contenant :
            - vent_kph (float) : Vitesse du vent en km/h.
            - direction_cardinal (str) : Direction du vent (ex: "NE").
            - direction_deg (int) : Direction du vent en degrés.
            - condition (str) : Description du temps (ex: "Sunny").
            - precip_mm (float) : Précipitations en millimètres.
        :rtype: dict
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
