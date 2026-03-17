import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_production_data(num_rows=1000):
    """Génère un faux jeu de données de suivi de production (Nouveau format)."""
    
    np.random.seed(42)
    random.seed(42)
    
    etapes = ["Forge", "Traitement thermique", "Usinage", "Contrôle qualité"]
    defauts_possibles = ["Porosité", "Fissure", "Défaut dimensionnel", "Inclusion", "Mauvais état de surface"]
    operateurs = [f"OP-{str(i).zfill(3)}" for i in range(1, 15)]
    
    data = []
    
    current_date = datetime(2024, 1, 1, 8, 0)
    
    for i in range(num_rows):
        piece_id = f"P-{str(i).zfill(5)}"
        lot = f"LOT-{(i // 50) + 1000}"

        # On simule un parcours partiel ou complet des pièces
        nb_etapes = random.randint(1, len(etapes))
        etapes_piece = random.sample(etapes, nb_etapes)

        # Décalage de la date de départ
        current_date += timedelta(minutes=random.randint(15, 120))

        for etape in etapes_piece:
            temps_prevu = random.choice([30.0, 45.0, 60.0, 120.0])

            # Simulation d'un temps réel avec variation
            variation = random.uniform(0.8, 1.5)
            temps_reel = temps_prevu * variation

            date_debut = current_date
            date_fin = date_debut + timedelta(minutes=temps_reel)
            current_date = date_fin # La prochaine étape commencera après la fin

            # Température uniquement pour forge et thermique
            temp = np.nan
            if etape in ["Forge", "Traitement thermique"]:
                temp = round(random.uniform(850, 1250), 1)

            # Logique métier simulée : Détermination de la conformité
            statut = "Conforme"
            defaut = np.nan

            # 8% de chance d'être non conforme
            if random.random() < 0.08:
                statut = "Non-conforme"
                defaut = random.choice(defauts_possibles)
            elif random.random() < 0.05:
                statut = "En attente"

            data.append({
                "Identifiant pièce": piece_id,
                "Numéro de lot": lot,
                "Étape process": etape,
                "Date/heure début étape": date_debut,
                "Date/heure fin étape": date_fin,
                "Temps prévu (min)": temps_prevu,
                "Statut de conformité": statut,
                "Type de défaut": defaut,
                "Opérateur": random.choice(operateurs),
                "Température process (°C)": temp
            })

    df = pd.DataFrame(data)
    filename = 'suivi_production_mock.xlsx'
    df.to_excel(filename, index=False)
    print(f"✅ Fichier '{filename}' généré avec succès avec {len(df)} lignes !")

if __name__ == "__main__":
    generate_production_data(1000)