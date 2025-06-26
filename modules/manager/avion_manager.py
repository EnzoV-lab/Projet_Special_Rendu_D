import pandas as pd  # Bibliothèque pour la manipulation de données sous forme de tableaux (DataFrames)
import csv           # Module standard pour la manipulation de fichiers CSV

class AvionManager:
    """
    Classe de gestion des avions à partir d'un fichier CSV contenant leurs caractéristiques.
    Permet de sélectionner un avion selon différents modes.
    """
    def __init__(self, fichier_csv="Data/avions.csv"):
        """
        Initialise le gestionnaire d'avions à partir d'un fichier CSV.
        :param fichier_csv: chemin vers le fichier contenant les données des avions
        """
        self.fichier_csv = fichier_csv
        self.df = pd.read_csv(fichier_csv)  # Chargement du fichier CSV dans un DataFrame

    def choix_avion_mode_1(self):
        """
        Mode 1 : permet à l'utilisateur de choisir librement un avion, sans contrainte météo.
        """
        types_disponibles = self.df['type'].unique()  # Liste des types d’avions uniques dans le fichier
        print("Types d’avions disponibles :")
        liste_type = []
        for t in types_disponibles:
            liste_type.append(t)
            print(f" - {t}")

        # Demande à l’utilisateur de choisir un type d’avion (en forçant à écrire un type valide)
        type_choisi = ""
        while type_choisi not in liste_type:
            type_choisi = input("Entrez un type d’avion : ").strip().lower()

        # Filtrage des avions de ce type
        da_type = self.df[self.df['type'] == type_choisi]

        print("\nAvions disponibles :")
        liste_avion = []
        for _, row in da_type.iterrows():
            nom = row['nom']
            vent = row['vitesse_vent_admissible']
            liste_avion.append(nom)
            print(f" - {nom} (vent max admissible : {vent} km/h)")

        # Demande du nom exact de l’avion choisi
        nom_choisi = ""
        while nom_choisi not in liste_avion:
            nom_choisi = input("Entrez le nom de l’avion : ").strip()

        # Récupération des caractéristiques de l’avion choisi
        avion = da_type[da_type['nom'] == nom_choisi].iloc[0]
        vitesse_admi = avion['vitesse_vent_admissible']
        vitesse_avion = avion['vitesse_de_avion']
        return vitesse_admi, vitesse_avion

    def choix_avion_mode_2(self, borne_min=0, borne_max=100):
        """
        Mode 2 : propose uniquement les avions dont la vitesse de vent admissible est dans une certaine plage.
        Utile pour filtrer les avions selon les conditions météo prévues.
        :param borne_min: vitesse de vent minimale admissible
        :param borne_max: vitesse de vent maximale admissible
        """
        types_disponibles = self.df['type'].unique()
        print("Types d’avions disponibles :")
        for t in types_disponibles:
            print(f" - {t}")

        # Boucle jusqu’à obtenir un type d’avion valide avec des résultats dans la plage spécifiée
        while True:
            type_choisi = input("Entrez un type d’avion : ").strip().lower()

            if type_choisi not in types_disponibles:
                print("Type invalide. Veuillez réessayer.")
                continue

            # Filtrage selon le type et la plage de vitesse admissible
            da_type = self.df[
                (self.df['type'] == type_choisi) &
                (self.df['vitesse_vent_admissible'] >= borne_min) &
                (self.df['vitesse_vent_admissible'] <= borne_max)
            ]

            if da_type.empty:
                print(f"Aucun avion trouvé pour le type '{type_choisi}' avec vent admissible entre {borne_min} et {borne_max} km/h.")
                print("Veuillez choisir un autre type d’avion.\n")
            else:
                break

        print("\nAvions disponibles :")
        liste_avion = []
        for _, row in da_type.iterrows():
            nom = row['nom']
            vent = row['vitesse_vent_admissible']
            liste_avion.append(nom)
            print(f" - {nom} (vent max admissible : {vent} km/h)")

        # Choix final de l’avion
        nom_choisi = ""
        while nom_choisi not in liste_avion:
            nom_choisi = input("Entrez le nom de l’avion : ").strip()

        avion = da_type[da_type['nom'] == nom_choisi].iloc[0]
        vitesse_admi = avion['vitesse_vent_admissible']
        vitesse_avion = avion['vitesse_de_avion']
        return vitesse_admi, vitesse_avion

    def choix_du_mode(self, borne_min, borne_max):
        """
        Permet à l’utilisateur de choisir entre les deux modes :
        - Mode 1 : sans contrainte météo
        - Mode 2 : filtrage selon la plage de vent admissible
        :return: les caractéristiques de l’avion choisi
        """
        reponse_possible = ["1", "2"]
        reponse_mode = ""

        # L’utilisateur doit répondre "1" ou "2"
        while reponse_mode not in reponse_possible:
            reponse_mode = input(
                "A présent veuillez choisir votre mode\n"
                " 1 - Proposer n'importe quel avion\n"
                " 2 - Proposer uniquement les avions susceptibles à une déviation\n Réponse :  ")

        # Appel au bon mode selon la réponse
        if reponse_mode == "1":
            return self.choix_avion_mode_1()
        else:
            return self.choix_avion_mode_2(borne_min=borne_min, borne_max=borne_max)
