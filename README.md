# Calendriers des pompiers de Meylan : suivi des tournées par secteur

Une page web pour téléphone qui permet à l'équipe d'un secteur de se répartir la vente des calendriers. Elle affiche toutes les adresses du secteur, en liste ou sur une carte. Chaque adresse a un statut : **À faire**, **À repasser** ou **Validée**. On peut y ajouter des notes, par exemple un code d'immeuble ou une date de repasse. Chaque saisie est signée par le prénom du vendeur. L'onglet Activité montre qui a fait quoi.

Chaque secteur a sa propre page, hébergée gratuitement par Google Apps Script. Les données sont rangées dans une feuille Google Sheets. Les vendeurs ouvrent simplement un lien, sans compte.

Les secteurs sont ceux de la carte [Calendriers Pompiers Meylan](https://www.google.com/maps/d/viewer?mid=1hj46infUJx8b8XN9YQwTatU6ZZGnixk).

## Mettre en ligne un secteur
Les dossiers `secteurs/secteur-N/` sont prêts à l'emploi. Suivez le `LISEZMOI.md` du secteur, en une dizaine de minutes avec un compte Google.

| Secteur | Dossier | Adresses |
|---|---|---|
| 2 | [secteurs/secteur-2](secteurs/secteur-2/LISEZMOI.md) | 553 |
| 4 | [secteurs/secteur-4](secteurs/secteur-4/LISEZMOI.md) | 543 |

Un secteur absent de ce tableau se construit en une commande, comme expliqué ci-dessous.

## Construire un secteur
Il faut **Python 3.8 ou plus récent**. Node.js est facultatif : s'il est installé, il sert à vérifier la page générée.

```bash
python3 outils/construire.py 7          # un secteur
python3 outils/construire.py 3 5 9      # plusieurs
python3 outils/construire.py tous       # les 15
```

Le script :
1. télécharge la carte des secteurs, la Base Adresse Nationale (Isère, environ 15 Mo) et les rues OpenStreetMap du secteur ;
2. garde les adresses situées dans le contour du secteur ;
3. écrit `secteurs/secteur-N/` à partir des modèles du dossier `outils/`.

Les téléchargements sont gardés dans `outils/cache/`. Supprimez ce dossier pour récupérer des données à jour.

Les serveurs publics OpenStreetMap refusent souvent les requêtes. Le script réessaie pendant quelques minutes, puis s'arrête si rien ne répond : relancez-le plus tard. L'option `--sans-rues` construit quand même la page, avec une carte réduite au contour du secteur et aux adresses.

Une douzaine d'adresses tombent exactement sur la limite entre deux secteurs et figurent dans les deux listes. Mettez-vous d'accord avec l'équipe voisine pour savoir qui y passe.

## Modifier la page
Modifiez les modèles du dossier `outils/` (`modele-index.html`, `modele-code.gs`, `modele-lisezmoi.md`), puis reconstruisez les secteurs. Ne modifiez pas directement les fichiers de `secteurs/` : ils seraient écrasés à la reconstruction.

Deux pièges propres à Google Apps Script :
- **Pas de `//` dans le code JavaScript de la page, sauf pour les commentaires.** Google supprime tout ce qui suit `//` sur une ligne, y compris dans une chaîne comme `"http://…"`. Écrivez les adresses web `"https:\/\/…"`.
- **Pas de lignes très longues.** Un collage dans l'éditeur Apps Script peut couper le fichier sans prévenir. Le script garde les données sur des lignes courtes et refuse toute ligne de plus de 5000 caractères.

Après une modification de la page d'un secteur déjà en ligne, recollez `Index.html`. Faites ensuite **Déployer > Gérer les déploiements > crayon > Nouvelle version** : le lien des vendeurs ne change pas.

## Sources des données
- Adresses : [Base Adresse Nationale](https://adresse.data.gouv.fr), sous Licence Ouverte 2.0.
- Rues de la carte : © les contributeurs d'[OpenStreetMap](https://www.openstreetmap.org/copyright), sous licence ODbL.
- Contours des secteurs : carte Google My Maps « Calendriers Pompiers Meylan ».
