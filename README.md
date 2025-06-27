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
```

### 2. Installer le package

``` bash
  pip install -e .
```
### 2.1. En cas de problème utiliser la commande suivante

``` bash
  pip install -r requirements.txt
```
## Lancer l’application

``` bash
  streamlit run Itineraire-aérien-package/main.py
```

L'application s’ouvre dans le navigateur. Utilisez la barre latérale pour définir les paramètres de simulation.

##  Exemple d’utilisation

1. Choisissez une ville de départ et d’arrivée (New York - Charlotte pour un temps de chargement relativement court).
2. Lancez le calcul de l’itinéraire de référence.
3. Choisissez le mode : le mode libre permet de sélectionner n’importe quel avion, sans garantir son arrivée à destination ou sa déviation, tandis que le mode choix par condition météo propose uniquement les avions les plus susceptibles d’être déviés.
4. Lancez le calcul d’itinéraire dévié.
5. Visualisez les deux itinéraires superposés avec les informations météo.
6. Lancez une nouvelle simulation en cliquant sur le bouton prévu à cet effet si cella est souhaiter.

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
* Le choix des villes se situe uniquements aux Etats-Unis
* Les Waypoints et donc les trajet sont uniquement réaliser aux dessus de la terre.
* Les vitesses de vents admissible des avions ne sont pas réelles, elles sont plus basses que la réaliter pour avoir des déviation (les valeurs peuvent etre modifier dans le fichier "avions.csv").
* Les données météo prises sur l'API sont des données météo au sol et non en altitude 
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

2- Lien actuel vers le blog: ` <http://localhost:63342/Projet_Special_Rendu_D/docs/build/html/index.html>`

ou

3- Ouvrez le fichier suivant dans votre navigateur :
``` bash
  docs/build/html/index.html
```
### 2. Naviguez dans les modules, classes et fonctions documentées.

--> Régénérer la documentation

Si vous modifiez le code et souhaitez mettre à jour la documentation :
Dans un premier temps le terminal il faut installer le module sphinx et le module qui permet de gérer les thèmes.
``` bash
pip install sphinx
pip install sphinx-rtd-theme
``` 
Dans le terminal ecrivez ce qu'il y'a ci-dessous afin de générer un nouveau fichier html si on modifie les fichiers
``` bash
cd docs
sys.path.insert(0, os.path.abspath('../../Itineraire-aérien-package'))
sys.path.insert(0, os.path.abspath('../../ItineraireAerien'))
sys.path.insert(0, os.path.abspath('../../Avion'))
sys.path.insert(0, os.path.abspath('../../coordonnees'))
sys.path.insert(0, os.path.abspath('../../Meteo'))
sys.path.insert(0, os.path.abspath('../../Visualisation'))
sys.path.insert(0, os.path.abspath('../..'))
./make.bat html   # Windows
# ou
make html         # Mac/Linux
``` 
➡️ La documentation mise à jour sera disponible dans docs/build/html.
Dans ce cas vous ne pourrez consulter la documentation que via l'option 3 ou vous devrez modifier le lien vous même sur streamlit et sur ce même document

📝 Licence
    Projet académique MGA802 – ETS Montréal. Usage interne uniquement
