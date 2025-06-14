import folium

def tracer_trajet(chemin):
    """
    Affiche un trajet sur une carte Folium et retourne l'objet carte.
    `chemin` est une liste de tuples (id, lat, lon)
    """
    if not chemin:
        raise ValueError("Le chemin est vide.")

    lat_centre = sum(p[1] for p in chemin) / len(chemin)
    lon_centre = sum(p[2] for p in chemin) / len(chemin)
    carte = folium.Map(location=(lat_centre, lon_centre), zoom_start=5)

    for i, (id, lat, lon) in enumerate(chemin):
        couleur = "green" if i == 0 else "red" if i == len(chemin) - 1 else "blue"
        folium.Marker(location=(lat, lon), popup=id, icon=folium.Icon(color=couleur)).add_to(carte)

    folium.PolyLine([(lat, lon) for _, lat, lon in chemin], color="blue", weight=2.5).add_to(carte)
    return carte