import pandas as pd
import plotly.express as px

class ProductionAnalyzer:
    """Le cerveau métier : analyse les données de production et génère les visuels."""
    
    def __init__(self, df: pd.DataFrame):
        # 1. STANDARDISATION DES COLONNES (Le remède anti-crash)
        # On remplace automatiquement les accents et caractères gênants
        df.columns = df.columns.str.replace('é', 'e').str.replace('è', 'e').str.replace(' ', '_')
        
        # On s'assure que les colonnes vitales sont bien présentes après nettoyage
        colonnes_vitales = ['Type_Piece', 'Statut_Conformite', 'Temperature_Forgeage_C']
        for col in colonnes_vitales:
            if col not in df.columns:
                raise ValueError(f"Colonne vitale manquante dans le fichier : '{col}'. Vérifiez le format de votre Excel.")

        self.df = df
        self.pieces_uniques = df['Type_Piece'].dropna().unique().tolist()

    def apply_filter(self, selected_piece: str):
        """Filtre les données si l'utilisateur a sélectionné une pièce spécifique."""
        if selected_piece != 'Toutes':
            self.df = self.df[self.df['Type_Piece'] == selected_piece]

    def get_kpis(self) -> tuple:
        """Calcule et renvoie les indicateurs clés (Total et Taux de rebut)."""
        total_pieces = len(self.df)
        taux_rebut = 0
        if total_pieces > 0:
            taux_rebut = round((len(self.df[self.df['Statut_Conformite'] == 'NOK']) / total_pieces) * 100, 1)
        
        return total_pieces, taux_rebut

    def get_charts(self) -> tuple:
        """Génère les 2 graphiques Plotly et les convertit en JSON pour le web."""

        # 1. Graphique Camembert (Taux de Conformité)
        fig1 = px.pie(self.df, names='Statut_Conformite', title='Taux de Conformité',
                      color='Statut_Conformite', color_discrete_map={'OK':'#28a745', 'NOK':'#dc3545'}, hole=0.4)
        graph1JSON = fig1.to_json()

        # 2. Graphique Boîte à moustaches (Températures)
        fig2 = px.box(self.df, x='Type_Piece', y='Temperature_Forgeage_C', color='Type_Piece',
                      title='Dispersion des Températures', points="all")
        graph2JSON = fig2.to_json()

        return graph1JSON, graph2JSON
