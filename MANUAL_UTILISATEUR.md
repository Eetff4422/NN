# Manuel Utilisateur - Outil d'Analyse de Production Safran

Ce manuel décrit la configuration, le lancement et l'utilisation de l'Outil d'Analyse de Production dédié à la Direction Technique (Division Matériaux et Procédés).

## 1. Prérequis et Installation
L'application requiert **Python 3.10** ou supérieur.

### Installation des dépendances :
1. Ouvrez un terminal dans le répertoire racine du projet `safran_data_analyzer`.
2. Installez les packages nécessaires via `pip` :
   ```bash
   pip install -r requirements.txt
   ```
*(Note : Si le fichier `requirements.txt` n'est pas fourni, installez : `pandas`, `flask`, `flask-login`, `plotly`, `openpyxl`, `werkzeug`, `itsdangerous`, et `flask-sqlalchemy`)*.

### Lancement de l'application :
1. Exécutez le fichier principal :
   ```bash
   python run.py
   ```
2. Ouvrez votre navigateur web et accédez à l'URL fournie par la console (généralement `http://127.0.0.1:5000/`).

---

## 2. Accès et Authentification
Pour des raisons de sécurité, l'accès à l'application est restreint.

### Créer un compte
1. Sur la page de connexion, cliquez sur "Créer un compte".
2. Remplissez le formulaire. Votre adresse e-mail **doit** se terminer par `@safrangroup.com` ou `@safran.fr`.
3. Configurez une question et une réponse secrète (utile en cas d'oubli de mot de passe).
4. Cliquez sur "Créer mon compte". Vous serez redirigé vers la page de connexion.

### Mot de passe oublié
1. Si vous avez oublié votre mot de passe, cliquez sur "Mot de passe oublié ?" sur la page de connexion.
2. Entrez votre adresse e-mail. Un lien de réinitialisation vous sera envoyé (simulé dans la console).
3. Cliquez sur le lien pour répondre à votre question secrète. En cas de bonne réponse, vous pourrez définir un nouveau mot de passe.

*Remarque : Par sécurité, votre session se déconnectera automatiquement après 15 minutes d'inactivité.*

---

## 3. Utilisation de l'Application

### Page d'Accueil & Importation
Une fois connecté, vous arrivez sur votre tableau de bord personnel.
- **Historique :** Vos analyses précédentes sont listées. Cliquez sur "Ouvrir" pour recharger les résultats d'une analyse passée.
- **Importation :** Pour démarrer une nouvelle analyse, utilisez le formulaire "Nouvelle Analyse" :
  1. Cliquez sur "Parcourir" ou "Choisir un fichier".
  2. Sélectionnez un fichier Excel (`.xlsx` ou `.xls`) contenant les données de production.
  3. Cliquez sur "Lancer l'Analyse".

### Génération de Données (Test)
Si vous ne possédez pas de fichier de test, vous pouvez en générer un automatiquement.
- Exécutez la commande suivante depuis le répertoire racine :
  ```bash
  python generate_mock_data.py
  ```
- Un fichier `suivi_production_mock.xlsx` sera créé. Il peut être importé directement dans l'application.

---

## 4. Le Tableau de Bord d'Analyse (Dashboard)
Une fois le fichier importé, le tableau de bord affiche vos résultats.

### Filtres
- **Filtrer par type de pièce :** Utilisez le menu déroulant en haut de la page pour ne cibler qu'une pièce spécifique (ex: "Disque de turbine"). Les graphiques et KPIs se mettront automatiquement à jour.

### Indicateurs Clés (KPIs)
- **Pièces Analysées :** Le nombre total de pièces dans le jeu de données actuel.
- **Taux de Non-Conformité :** Le pourcentage de pièces déclarées "NOK". S'il dépasse 10%, la valeur s'affiche en rouge.

### Graphiques Interactifs
- **Taux de Conformité (Camembert) :** Permet d'un coup d'œil d'observer la répartition entre les pièces "OK" et "NOK".
- **Dispersion des Températures (Boîte à moustaches) :** Permet d'observer la variabilité des températures de forgeage selon le type de pièce et d'identifier rapidement des valeurs aberrantes (outliers).
- **Analyse des types de défauts (Barres) :** *S'affiche uniquement s'il y a des défauts (NOK).* Répertorie les défauts rencontrés et leur fréquence pour isoler les problèmes récurrents.

### Exportation
Vous pouvez sauvegarder la vue actuelle du tableau de bord au format PDF.
- Cliquez sur le bouton "📥 Exporter le Rapport (PDF)" en haut à droite.
- La fenêtre d'impression de votre navigateur s'ouvre, vous permettant d'enregistrer la page en PDF.