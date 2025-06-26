from modules.manager.donnees_meteo import DonneesMeteo  # Classe pour interagir avec l'API météo
import time  # Permet de temporiser les requêtes (éviter surcharge de l'API)

class MeteoManager:
    """
    Classe de gestion des conditions météorologiques sur des segments de trajectoire.

    Cette classe utilise l'API WeatherAPI via la classe `DonneesMeteo` pour interroger
    les conditions météo sur une série de coordonnées GPS et déterminer si elles
    respectent un seuil de vent défini.

    :param cle_api: Clé API pour accéder au service météo (ex: weatherapi.com)
    :type cle_api: str
    """

    def __init__(self, cle_api):
        """
        Initialise un objet MeteoManager avec une clé API.

        :param cle_api: Clé d'accès à l'API WeatherAPI.
        :type cle_api: str
        """
        self.cle_api = cle_api

    def verifier_conditions_meteo(self, coordonnees, seuil_vent_kph, max_depassements=2, pause=1):
        """
        Vérifie les conditions météorologiques sur une série de coordonnées GPS.

        Pour chaque point, récupère les données météo et vérifie si la vitesse du vent
        dépasse un seuil défini. Si trop de points dépassent ce seuil, le segment est rejeté.

        :param coordonnees: Liste de tuples représentant les coordonnées GPS (latitude, longitude).
        :type coordonnees: list[tuple[float, float]]
        :param seuil_vent_kph: Seuil maximal de vent admissible (en km/h).
        :type seuil_vent_kph: float
        :param max_depassements: Nombre maximal de points autorisés à dépasser le seuil de vent.
        :type max_depassements: int, optional
        :param pause: Temps d'attente entre deux requêtes API, en secondes.
        :type pause: float, optional

        :return:
            - `bool` : True si le segment est accepté, False sinon.
            - `list[tuple[float, float]]` : Coordonnées vérifiées.
            - `list[tuple[float, float, float|None]]` : Données météo par point.
            - `float` : Vent maximal rencontré sur le segment.

        :rtype: tuple[bool, list, list, float]
        """
        depassements = 0                    # Nombre de points dépassant le seuil
        liste_coords = []                  # Coordonnées réellement analysées
        donnees_meteo_segment = []         # Résultats météo pour chaque point
        vent_max = 0                       # Vent max rencontré sur le segment

        for lat, lon in coordonnees:
            meteo = DonneesMeteo(self.cle_api, (lat, lon))  # Crée une instance pour récupérer la météo de ce point
            try:
                meteo.fetch()                              # Requête vers l'API
                donnees = meteo.get_donnees()              # Données météo sous forme de dictionnaire
                vent = donnees.get("vent_kph", None)       # Vitesse du vent (peut être None)

                # Sauvegarde des résultats
                liste_coords.append((lat, lon))
                donnees_meteo_segment.append((lat, lon, vent))

                # Met à jour le vent max rencontré
                if vent and vent > vent_max:
                    vent_max = vent

                # Si le vent dépasse le seuil, on incrémente les dépassements
                if vent and vent > seuil_vent_kph:
                    depassements += 1
                    if depassements > max_depassements:
                        # Trop de dépassements → segment rejeté
                        return False, liste_coords, donnees_meteo_segment, vent_max

            except Exception as e:
                # En cas d’erreur (API, réseau, JSON), on note le point mais sans info sur le vent
                liste_coords.append((lat, lon))
                donnees_meteo_segment.append((lat, lon, None))

            # Pause entre les requêtes pour éviter blocage par le serveur
            time.sleep(pause)

        # Aucun dépassement critique → segment accepté
        return True, liste_coords, donnees_meteo_segment, vent_max
