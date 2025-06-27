import numpy as np  # Pour les calculs numériques et manipulation de vecteurs

class TrajectoireManager:
    """
    Classe permettant de lisser une trajectoire composée de segments en utilisant des courbes de Bézier quadratiques.

    :param n_points_bezier: Nombre de points générés pour chaque courbe de Bézier.
    :type n_points_bezier: int
    :param auto_ctrl_ratio: Position relative du point de contrôle sur le segment p1 → p2.
    :type auto_ctrl_ratio: float
    """
    def __init__(self, n_points_bezier=40, auto_ctrl_ratio=0.1):
        """
        Initialise les paramètres de génération des courbes.

        :param n_points_bezier: Nombre de points générés par courbe.
        :type n_points_bezier: int
        :param auto_ctrl_ratio: Ratio définissant l'emplacement du point de contrôle.
        :type auto_ctrl_ratio: float
        """
        self.n = n_points_bezier        # Plus ce nombre est grand, plus la courbe sera lisse
        self.ratio = auto_ctrl_ratio    # Définit la position du point de contrôle (ex : 0.1 = proche de p1)

    def bezier_curve(self, p0, p1, p2):
        """
        Génère une courbe de Bézier quadratique à partir de trois points.

        :param p0: Point de départ de la courbe (latitude, longitude).
        :type p0: tuple[float, float]
        :param p1: Point de contrôle (influence la courbure).
        :type p1: tuple[float, float]
        :param p2: Point d’arrivée de la courbe (latitude, longitude).
        :type p2: tuple[float, float]
        :return: Liste de points interpolés (latitude, longitude).
        :rtype: list[tuple[float, float]]
        """
        t = np.linspace(0, 1, self.n)  # Génère 'n' valeurs de t entre 0 et 1
        return [
            (
                (1 - tt) ** 2 * p0[0] + 2 * (1 - tt) * tt * p1[0] + tt ** 2 * p2[0],  # Latitude
                (1 - tt) ** 2 * p0[1] + 2 * (1 - tt) * tt * p1[1] + tt ** 2 * p2[1]   # Longitude
            )
            for tt in t
        ]

    def auto_ctrl(self, p1, p2):
        """
        Calcule automatiquement un point de contrôle intermédiaire entre deux points.

        :param p1: Point de départ (latitude, longitude).
        :type p1: tuple[float, float]
        :param p2: Point d’arrivée (latitude, longitude).
        :type p2: tuple[float, float]
        :return: Point de contrôle calculé selon le ratio défini.
        :rtype: tuple[float, float]
        """
        p1 = np.array(p1, dtype=float)
        p2 = np.array(p2, dtype=float)
        return tuple(p1 + self.ratio * (p2 - p1))  # Point à 10% (par défaut) de la distance entre p1 et p2

    def trajectoire_lisse_avec_controles(self, data):
        """
        Lisse une trajectoire en remplaçant les jonctions entre segments par des courbes de Bézier.

        :param data: Liste de segments, chaque segment étant une liste de points [(lat, lon), ...].
        :type data: list[list[tuple[float, float]]]
        :return: Trajectoire complète lissée sous forme de liste de points (latitude, longitude).
        :rtype: list[tuple[float, float]]
        :raises ValueError: Si moins de deux segments sont fournis.
        """
        if len(data) < 2:
            raise ValueError("Il faut au moins deux segments pour lisser une trajectoire.")

        trajectoire = list(data[0])  # Démarre avec le premier segment

        for i in range(len(data) - 1):
            p0 = data[i][-1]          # Dernier point du segment actuel
            p2 = data[i + 1][0]       # Premier point du segment suivant
            ctrl = self.auto_ctrl(p0, p2)              # Calcul du point de contrôle entre p0 et p2
            courbe = self.bezier_curve(p0, ctrl, p2)   # Génère la courbe entre ces deux points

            trajectoire.extend(courbe[1:])             # Ajoute la courbe (sauf le 1er point déjà présent)
            trajectoire.extend(data[i + 1][1:])        # Ajoute les points restants du segment suivant

        return trajectoire  # Liste finale de points (lissée et continue)
