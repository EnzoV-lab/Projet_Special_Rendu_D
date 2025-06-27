# Projet_Special_Rendu_D
# ITINÉRAIRE AÉRIEN SÉCURISÉ PAR METEO
 Membres: Romuald TIAKO - Elsa KUPFER - Enzo VILLAMANDOS - Lucas BONNEAUD

## Introduction

Ce projet permet de simuler une trajectoire aérienne entre deux villes en prenant en compte les conditions météorologiques, notamment la vitesse du vent. Grâce à des données météo en temps réel, le système peut proposer un itinéraire de déviation si les conditions ne permettent pas un vol direct.

Le projet est principalement destiné à des simulations d’itinéraires aériens, mais peut servir de base pour des applications plus complexes en logistique ou aviation.

## Fonctionnalités

* Sélection d’un itinéraire entre deux villes.
* Choix d’un avion parmi une base de données, avec ou sans contrainte météo.
* Intégration d’une API météo pour vérifier les conditions (vitesse du vent).
* Génération d’un itinéraire de déviation si nécessaire.
* Visualisation des trajets sur une carte interactive avec les conditions météo.
* Interface utilisateur complète via **Streamlit**.

## Structure Générale

* `AvionManager` : gestion des types d’avions et de leurs caractéristiques.
* `NavigationManager` : logique de navigation et calcul de trajectoires.
* `MeteoManager` et `DonneesMeteo` : intégration de l’API météo.
* `TrajectoireManager` : lissage des trajectoires via courbes de Bézier.
* `VisualisationManager` : affichage interactif sur carte (Folium).
* Interface Streamlit pour l’utilisation interactive de l’application.

##  Installation

### 1. Cloner le dépôt

``` bash
  git clone https://github.com/EnzoV-lab/Projet_Special_Rendu_D
  cd Projet_Special_Rendu_D
```

### 2. Installer les dépendances

``` bash
  pip install -r requirements.txt
```

### 3. Créer les dossiers nécessaires

``` bash
  mkdir Data Cartes
```

### 4. Fournir les fichiers de données :

Placez les fichiers suivants dans le dossier `Data/` :

* `avions.csv` : base de données des avions avec type, vitesse admissible, etc.
* `Waypoints.csv` : base de données géographiques des points de navigation.
* `Villes.csv` : coordonnées des villes utilisées.

## Lancer l’application

``` bash
  streamlit run main.py
```

L'application s’ouvre dans le navigateur. Utilisez la barre latérale pour définir les paramètres de simulation.

##  Exemple d’utilisation

1. Choisissez une ville de départ et d’arrivée.
2. Lancez le calcul de l’itinéraire de référence.
3. Sélectionnez un type d’avion (libre ou filtré).
4. Lancez le calcul d’itinéraire dévié.
5. Visualisez les deux itinéraires superposés avec les informations météo.

## Exemple de données attendues (`avions.csv`)

```csv
nom,type,vitesse_de_avion,vitesse_vent_admissible
A320,jet,900,120
Cessna208,light,350,60
...
```

## Dépendances principales

* `pandas`
* `numpy`
* `folium`
* `streamlit`
* `geopy`
* `requests`

## API utilisée

* **[WeatherAPI](https://www.weatherapi.com/)** : pour récupérer les données météorologiques.


## À savoir

* Il est possible que certaines coordonnées de villes ou waypoints soient absentes ou incorrectes — vous pouvez compléter les fichiers CSV à votre convenance.
* Le système vérifie le vent tous les \~100 km sur le trajet.
* Le seuil météo est défini par les capacités de l’avion choisi.

##  Public cible

* Étudiants en informatique ou data science.
* Développeurs souhaitant intégrer des contraintes réelles (météo) à des modèles de simulation.
* Curieux des applications géospatiales.

## Documentation
Une documentation complète du code (générée avec Sphinx) est disponible.
### 1. Consulter la documentation
1- Consultation directement via-streamlit
ou

2- Lien actuel vers le blog: ` <http://localhost:63342/Projet_Special_Rendu_D/docs/build/html/index.html?_ijt=6emfc9ru0ec4e650633gegt3ij&_ij_reload=RELOAD_ON_SAVE>`

ou

3- Ouvrez le fichier suivant dans votre navigateur :
``` bash
  docs/build/html/index.html
```
### 2. Naviguez dans les modules, classes et fonctions documentées.

--> Régénérer la documentation

Si vous modifiez le code et souhaitez mettre à jour la documentation :
Dans le terminal ecrivez:
``` bash
cd docs
sphinx-apidoc -o source ../modules
./make.bat html   # Windows
# ou
make html         # Mac/Linux
``` 
➡️ La documentation mise à jour sera disponible dans docs/build/html.
Dans ce cas vous ne pourrez consulter la documentation que via l'option 3 ou vous devrez modifier le lien vous même sur streamlit et sur ce même document

📝 Licence
    Projet académique MGA802 – ETS Montréal. Usage interne uniquement
