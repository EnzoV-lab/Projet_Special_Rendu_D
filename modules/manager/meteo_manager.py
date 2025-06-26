from modules.manager.donnees_meteo import DonneesMeteo  # Classe pour interagir avec l'API météo
import time  # Permet de temporiser les requêtes (éviter surcharge de l'API)

class MeteoManager:
    """
        Gère la récupération et la vérification des conditions météorologiques.

        Attributes
        ----------
        cle_api : str
            Clé API pour l'accès au service météo.

        Methods
        -------
        verifier_conditions_meteo(coordonnees, seuil_vent_kph)
            Vérifie les conditions météorologiques sur un segment donné.
        """
    def __init__(self, cle_api):
        """
        Initialise le gestionnaire météo avec la clé API.
        :param cle_api: clé fournie par le service météo (ex: weatherapi.com)
        """
        self.cle_api = cle_api

    def verifier_conditions_meteo(self, coordonnees, seuil_vent_kph, max_depassements=2, pause=1):
        """
                Vérifie les conditions météo sur une série de coordonnées.
                Rejette le segment si le vent dépasse le seuil autorisé trop souvent.

                Parameters
                ----------
                coordonnees : list of tuple
                    Liste de coordonnées GPS (latitude, longitude).
                seuil_vent_kph : float (valeur max admissible du vent en km/h)
                    Seuil maximal de vent admis.

                Returns
                -------
                tuple
                    Résultat booléen, liste de coordonnées, données météo, et vent maximal détecté.
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
