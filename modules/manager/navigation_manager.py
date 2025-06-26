import math              # Pour les fonctions trigonométriques et calculs géographiques
import pandas as pd      # Pour lire et manipuler les fichiers CSV contenant les waypoints

class NavigationManager:
    def __init__(self, waypoint_csv='Data/Waypoints.csv', rayon_max_km=200):
        """
        Initialise le gestionnaire de navigation.
        :param waypoint_csv: chemin du fichier CSV contenant les waypoints
        :param rayon_max_km: distance maximale autorisée entre deux points consécutifs
        """
        self.waypoint_csv = waypoint_csv
        self.rayon_max_km = rayon_max_km

    def distance(self, p1, p2):
        """
        Calcule la distance en kilomètres entre deux points géographiques (formule de Haversine).
        :param p1: tuple (lat, lon)
        :param p2: tuple (lat, lon)
        :return: distance en kilomètres
        """
        R = 6371  # Rayon moyen de la Terre en km
        lat1, lon1 = map(math.radians, p1)
        lat2, lon2 = map(math.radians, p2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    def calcul_angle(self, depart, waypoint, arrivee):
        """
        Calcule l'angle entre le vecteur (départ -> waypoint) et (départ -> arrivée).
        Utilisé pour sélectionner le waypoint le plus "aligné" vers la destination.
        """
        v1 = (waypoint[0] - depart[0], waypoint[1] - depart[1])
        v2 = (arrivee[0] - depart[0], arrivee[1] - depart[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]  # produit scalaire
        norm1 = math.hypot(*v1)          # norme du vecteur 1
        norm2 = math.hypot(*v2)          # norme du vecteur 2
        if norm1 == 0 or norm2 == 0:
            return float('inf')          # évite division par zéro
        cos_theta = dot / (norm1 * norm2)
        return math.acos(max(min(cos_theta, 1), -1))  # angle en radians (entre 0 et pi)

    def intercaler_points(self, lat1, lon1, lat2, lon2, n):
        """
        Génère n points intermédiaires équidistants entre deux coordonnées.
        :return: liste de tuples (lat, lon)
        """
        points_intercale = []
        for i in range(1, n + 1):
            x = lat1 + i * (lat2 - lat1) / (n + 1)
            y = lon1 + i * (lon2 - lon1) / (n + 1)
            points_intercale.append((x, y))
        return points_intercale

    def charger_waypoints(self):
        """
        Charge les waypoints depuis le fichier CSV.
        :return: DataFrame contenant ident, latitude, longitude
        """
        df = pd.read_csv(self.waypoint_csv)
        return df[['ident', 'latitude_deg', 'longitude_deg']].dropna()

    def trouver_point_suivant(self, depart, arrivee, points_utilises):
        """
        Sélectionne le prochain point de navigation optimal :
        - pas encore utilisé
        - pas trop éloigné
        - bien orienté vers la destination
        """
        df = pd.read_csv(self.waypoint_csv)[['latitude_deg', 'longitude_deg']].dropna()

        # Exclut les points déjà utilisés
        df = df[~df.apply(lambda row: (row['latitude_deg'], row['longitude_deg']) in points_utilises, axis=1)]

        # Évite de sélectionner le point d’arrivée comme waypoint
        df = df[~df.apply(lambda row: (
            round(row['latitude_deg'], 5), round(row['longitude_deg'], 5)) == (
            round(arrivee[0], 5), round(arrivee[1], 5)), axis=1)]

        if df.empty:
            return None  # Aucun point utilisable

        # Calcule l’angle et la distance par rapport à l’objectif
        df['angle'] = df.apply(lambda row: self.calcul_angle(
            depart, (row['latitude_deg'], row['longitude_deg']), arrivee), axis=1)
        df['distance'] = df.apply(lambda row: self.distance(
            depart, (row['latitude_deg'], row['longitude_deg'])), axis=1)

        # Filtre les points proches et orientés dans la bonne direction
        df_filtre = df[(df['angle'] <= math.radians(179)) & (df['distance'] <= self.rayon_max_km)]

        if df_filtre.empty:
            return None

        # Choisit le point avec le plus petit angle (donc le plus droit vers la cible)
        point_choisi = df_filtre.loc[df_filtre['angle'].idxmin()]
        return (point_choisi['latitude_deg'], point_choisi['longitude_deg'])

    def tracer_chemin(self, depart, arrivee, seuil, verifier_meteo_callback):
        """
        Construit un chemin de navigation du point de départ à l’arrivée :
        - en sélectionnant des waypoints
        - en vérifiant les conditions météo sur chaque segment
        - en s'arrêtant en cas d'impossibilité (barrière météo)

        :param depart: coordonnée de départ (lat, lon)
        :param arrivee: coordonnée d’arrivée (lat, lon)
        :param seuil: seuil météo (ex. vent max admissible)
        :param verifier_meteo_callback: fonction externe qui retourne si un segment est praticable
        :return: (liste des segments valides, liste des points météo, vent max détecté)
        """
        point = depart
        liste_point_utilisees = []  # Waypoints déjà utilisés
        liste_finale = []  # Segments finaux de la trajectoire
        liste_points_meteo = []  # Infos météo associées à chaque segment
        vent_max_tot = 0  # Vent max global détecté

        while self.distance(point, arrivee) > 75:  # Tant que l’arrivée n’est pas proche
            prochain_point = self.trouver_point_suivant(point, arrivee, liste_point_utilisees)
            if prochain_point is None:
                print("Aucun point trouvé, barrière météo ou géographique.")
                break

            # Interpolation de points sur le segment (pour vérification météo)
            coord_seg = self.intercaler_points(point[0], point[1], prochain_point[0], prochain_point[1], 6)
            Etat, liste_coordonnees, donnees_meteo, vent_max = verifier_meteo_callback(coord_seg, seuil)

            vent_max_tot = max(vent_max_tot, vent_max)

            if Etat:  # Le segment est praticable
                liste_finale.append(liste_coordonnees)
                liste_finale.append([prochain_point])
                liste_points_meteo.extend(donnees_meteo)
                liste_point_utilisees.append(prochain_point)
                point = prochain_point
            else:  # Le segment est interdit, on ne prend pas ce point
                liste_point_utilisees.append(prochain_point)

        liste_finale.append([arrivee])  # Ajoute l’arrivée à la fin
        return liste_finale, liste_points_meteo, vent_max_tot
