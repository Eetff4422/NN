import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_production_data(num_rows=1000):
    """Génère un faux jeu de données de suivi de production."""
    
    # 1. Initialisation des listes de données
    np.random.seed(42) # Pour avoir des résultats reproductibles
    
    # Types de pièces issus de la fiche de poste
    types_pieces = ['Disque de turbine', 'Anneau mobile', 'Arbre de turbine']
    defauts_possibles = ['Porosité', 'Fissure', 'Défaut dimensionnel', 'Inclusion', 'Aucun']
    
    data = {
        'ID_Lot': [f"LOT-{1000 + i}" for i in range(num_rows)],
        'Date_Production': [datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)],
        'Type_Piece': np.random.choice(types_pieces, num_rows, p=[0.5, 0.3, 0.2]),
        'Operateur_ID': np.random.choice(['OP-01', 'OP-02', 'OP-03', 'OP-04'], num_rows),
        
        # Données techniques simulées (avec une distribution normale)
        'Temperature_Forgeage_C': np.random.normal(loc=1100, scale=25, size=num_rows).round(1),
        'Duree_Refroidissement_min': np.random.normal(loc=120, scale=10, size=num_rows).round(1),
    }

    df = pd.DataFrame(data)

    # 2. Logique métier simulée : Détermination de la conformité
    # Si la température sort de la plage [1050 - 1150], on augmente le risque de non-conformité
    conditions_anomalie = (df['Temperature_Forgeage_C'] < 1050) | (df['Temperature_Forgeage_C'] > 1150)
    
    # Génération du statut (90% OK par défaut, mais les anomalies forcent un NOK)
    statuts = []
    types_defaut = []
    
    for is_anomalie in conditions_anomalie:
        if is_anomalie:
            statuts.append('NOK')
            types_defaut.append(random.choice(defauts_possibles[:-1])) # Exclut 'Aucun'
        else:
            if random.random() > 0.92: # 8% d'erreur naturelle
                statuts.append('NOK')
                types_defaut.append(random.choice(defauts_possibles[:-1]))
            else:
                statuts.append('OK')
                types_defaut.append('Aucun')

    df['Statut_Conformite'] = statuts
    df['Type_Defaut'] = types_defaut

    # 3. Export vers Excel
    filename = 'suivi_production_mock.xlsx'
    df.to_excel(filename, index=False)
    print(f"✅ Fichier '{filename}' généré avec succès avec {num_rows} lignes !")

if __name__ == "__main__":
    generate_production_data(1000)