# Safran Data Analyzer

Outil d'analyse graphique des données de production pour la Direction Technique, Division Matériaux et Procédés (Safran Aircraft Engines).

## Installation rapide

Suivez ces 4 commandes pour lancer le projet en local (Python >= 3.10 requis) :

```bash
cd safran_data_analyzer
python3 -m venv venv
source venv/bin/activate  # (Sous Windows: venv\Scripts\activate)
pip install -r requirements.txt
python run.py
```

## Données de Test

Si vous ne possédez pas de fichier de production Safran, vous pouvez en générer un factice (mock) en exécutant :

```bash
python generate_mock_data.py
```

Un fichier `suivi_production_mock.xlsx` sera créé à la racine du projet et pourra être uploadé dans l'interface.