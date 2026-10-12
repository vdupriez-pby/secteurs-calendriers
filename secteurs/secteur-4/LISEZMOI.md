# Calendriers Secteur 4 : mise en ligne avec Google Sheets

Il faut environ 10 minutes, avec un seul compte Google : celui de la personne qui gardera les données. Les vendeurs n'ont besoin d'aucun compte.

## 1. Créer la feuille et coller le code
1. Ouvrez https://sheets.new et nommez la feuille, par exemple « Calendriers Secteur 4 ».
2. Dans le menu, cliquez sur **Extensions > Apps Script**.
3. Dans le fichier `Code.gs` déjà ouvert, effacez tout et collez le contenu de [Code.gs](Code.gs).
4. Cliquez sur **+** à côté de « Fichiers », puis **HTML**. Nommez le fichier exactement `Index`, sans extension. Effacez son contenu et collez celui de [Index.html](Index.html) (voir l'avertissement ci-dessous). Le fichier est long, c'est normal : il contient les 543 adresses et la carte.
5. Enregistrez avec l'icône disquette.

> **Attention : un collage trop long peut être coupé sans prévenir.**
> `Index.html` fait 2509 lignes. Le presse-papiers ou l'éditeur Apps Script peut en garder seulement une partie, sans afficher d'erreur. La page reste alors bloquée sur « Chargement… ».
>
> **Vérifiez toujours après le collage** : appuyez sur Ctrl+Fin dans l'éditeur Apps Script. La dernière ligne doit être `</html>`, vers la ligne 2509.
>
> **Si c'est coupé, collez en deux fois** :
> 1. Dans Apps Script, effacez le contenu de `Index.html`.
> 2. Dans votre éditeur (VS Code par exemple), cliquez au tout début de la ligne 1, puis faites Maj+clic au tout début de la ligne 1254. Copiez, puis collez dans Apps Script.
> 3. Dans votre éditeur, cliquez au début de la ligne 1254, puis faites Ctrl+Maj+Fin pour sélectionner jusqu'à la fin du fichier. Copiez.
> 4. Dans Apps Script, appuyez sur Ctrl+Fin pour aller tout en bas, puis collez.
> 5. Vérifiez à nouveau que la dernière ligne est `</html>`, vers la ligne 2509.

Code d'accès facultatif : en haut de `Code.gs`, remplacez `const CODE_ACCES = '';` par exemple par `const CODE_ACCES = '1832';`. Chaque vendeur le saisira une fois sur son téléphone.

## 2. Publier
1. Cliquez sur **Déployer > Nouveau déploiement**, puis sur la roue dentée, et choisissez **Application Web**.
2. Réglez :
   - **Exécuter en tant que** : Moi ;
   - **Qui a accès** : Tout le monde.
3. Cliquez sur **Déployer**, puis autorisez l'accès.
   - Google affiche « Google n'a pas validé cette application ». C'est normal pour un script personnel.
   - Cliquez sur **Paramètres avancés**, puis sur **Accéder à … (non sécurisé)**, puis **Autoriser**.
4. Copiez l'**URL de l'application Web** (elle se termine par `/exec`) et envoyez-la aux vendeurs.

Sur le téléphone, ouvrez le lien puis choisissez « Ajouter à l'écran d'accueil ». Chaque vendeur indique son prénom à la première ouverture. Les prénoms doivent être différents, car c'est le prénom qui signe chaque passage.

## Où sont les données
Les onglets **Suivi**, **Notes**, **Historique** et **Ajouts** se créent dans la feuille au premier passage saisi. Vous pouvez les trier, les filtrer ou les exporter. Ne modifiez pas les en-têtes ni l'ordre des colonnes.

## Mettre à jour le code sans changer le lien
Cliquez sur **Déployer > Gérer les déploiements**, puis sur le crayon. Dans **Version**, choisissez « Nouvelle version », puis cliquez sur **Déployer**.
