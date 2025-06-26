import folium  # Folium permet de créer des cartes interactives basées sur Leaflet.js


class VisualisationManager:
    """
    Classe responsable de l'affichage de cartes interactives contenant des itinéraires
    et des données météo (notamment le vent) à l'aide de la bibliothèque Folium.
    """
    def afficher_meteo_sur_carte(self, points_meteo, seuil, itineraire):
        """
        Affiche une carte interactive avec un itinéraire et les points météo associés.

        :param points_meteo: Liste de tuples contenant latitude, longitude et vitesse du vent (km/h).
                                Format : [(lat, lon, vent_kph), ...]
        :type points_meteo: list[tuple[float, float, float or None]]
        :param seuil: Seuil de vent maximal admissible (km/h) pour le tracé.
        :type seuil: float
        :param itineraire: Liste de coordonnées GPS représentant l’itinéraire.
        :type itineraire: list[tuple[float, float]]
        :return: Carte Folium avec tracé et points météo.
        :rtype: folium.Map
        """
        # Calcule le centre de la carte à partir des points météo
        lat_centre = sum(lat for lat, lon, vent in points_meteo) / len(points_meteo)
        lon_centre = sum(lon for lat, lon, vent in points_meteo) / len(points_meteo)
        carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=6)

        # Trace l’itinéraire principal (en bleu)
        if itineraire:
            folium.PolyLine(itineraire, color="blue", weight=2).add_to(carte)

        # Ajoute les points météo sur la carte avec un code couleur
        for lat, lon, vent in points_meteo:
            couleur = "gray" if vent is None else ("green" if vent <= seuil else "red")
            popup = "Vent : inconnu" if vent is None else f"Vent : {vent:.1f} km/h"

            folium.CircleMarker(
                location=(lat, lon),
                radius=5,
                color=couleur,
                fill=True,
                fill_color=couleur,
                popup=popup
            ).add_to(carte)

        return carte

    def afficher_double_itineraire(self, itin1, itin2, points_meteo, seuil):
        """
        Affiche une carte avec deux itinéraires superposés (référence et dévié), ainsi que les points météo.

        :param itin1: Liste de points représentant l’itinéraire de référence.
        :type itin1: list[tuple[float, float]]
        :param itin2: Liste de points représentant l’itinéraire dévié.
        :type itin2: list[tuple[float, float]]
        :param points_meteo: Liste des points météo à afficher, avec vitesse du vent.
                                Format : [(lat, lon, vent_kph), ...]
        :type points_meteo: list[tuple[float, float, float or None]]
        :param seuil: Seuil de vent maximal admissible (km/h) à représenter.
        :type seuil: float
        :return: Carte Folium représentant les deux trajets et les conditions météo.
        :rtype: folium.Map
        """
        # Centre la carte sur le premier point disponible
        lat_centre, lon_centre = itin1[0] if itin1 else itin2[0]
        carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=6)

        # Trace l’itinéraire de référence (en bleu)
        if itin1:
            folium.PolyLine(
                itin1,
                color="blue",
                weight=3,
                tooltip="Itinéraire référence"
            ).add_to(carte)

        # Trace l’itinéraire dévié (en violet)
        if itin2:
            folium.PolyLine(
                itin2,
                color="purple",
                weight=3,
                tooltip="Itinéraire dévié"
            ).add_to(carte)

        # Ajoute les points météo, avec un code couleur selon la vitesse du vent
        for lat, lon, vent in points_meteo:
            couleur = "gray" if vent is None else ("green" if vent <= seuil else "red")
            popup = "Vent : inconnu" if vent is None else f"Vent : {vent:.1f} km/h"

            folium.CircleMarker(
                location=(lat, lon),
                radius=5,
                color=couleur,
                fill=True,
                fill_color=couleur,
                popup=popup
            ).add_to(carte)

        return carte
