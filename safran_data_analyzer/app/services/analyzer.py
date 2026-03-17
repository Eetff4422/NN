"""Analyseur de production Safran : Traitement des DataFrames et création des graphiques Plotly."""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import unidecode

EXPECTED_COLUMNS = {
    "piece_id"              : {"label": "Identifiant pièce",         "type": "str",      "required": True},
    "lot"                   : {"label": "Numéro de lot",             "type": "str",      "required": True},
    "etape"                 : {"label": "Étape process",             "type": "str",      "required": True},
    "date_debut"            : {"label": "Date/heure début étape",    "type": "datetime", "required": True},
    "date_fin"              : {"label": "Date/heure fin étape",      "type": "datetime", "required": True},
    "temps_prevu_min"       : {"label": "Temps prévu (min)",         "type": "float",    "required": True},
    "statut_conformite"     : {"label": "Statut de conformité",      "type": "str",      "required": True},
    "type_defaut"           : {"label": "Type de défaut",            "type": "str",      "required": False},
    "operateur"             : {"label": "Opérateur",                 "type": "str",      "required": False},
    "temperature_c"         : {"label": "Température process (°C)",  "type": "float",    "required": False},
}

class ProductionAnalyzer:
    """Le cerveau métier : standardise, analyse et génère les 5 graphiques interactifs."""

    def __init__(self, df: pd.DataFrame):
        """Standardise les colonnes et vérifie leur intégrité selon le dictionnaire de référence."""
        self.df = self._standardize_columns(df)
        self._verify_and_clean_data()

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remplace accents, passe en minuscules, remplace espaces par _ et strip les noms de colonnes, puis mappe vers les IDs internes."""
        def clean_string(s):
            s = str(s).strip().lower()
            s = unidecode.unidecode(s)
            s = s.replace(' ', '_').replace('-', '_')
            return s
        
        # 1. Nettoyage brut des colonnes du fichier
        df.columns = [clean_string(col) for col in df.columns]

        # 2. Mapping: Nom nettoyé du label attendu -> Clé interne (piece_id, lot, etc.)
        mapping = {}
        for key, config in EXPECTED_COLUMNS.items():
            expected_cleaned_label = clean_string(config["label"])
            mapping[expected_cleaned_label] = key

        df = df.rename(columns=mapping)
        return df

    def _verify_and_clean_data(self):
        """Vérifie la présence des colonnes obligatoires et effectue le nettoyage des données/calculs à la volée."""
        missing = [col for col, config in EXPECTED_COLUMNS.items() if config["required"] and col not in self.df.columns]
        if missing:
            raise ValueError(f"Colonnes obligatoires manquantes dans l'Excel : {', '.join(missing)}")

        # Casting types
        for col, config in EXPECTED_COLUMNS.items():
            if col in self.df.columns:
                if config["type"] == "datetime":
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                elif config["type"] == "float":
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                else:
                    self.df[col] = self.df[col].astype(str)

        # Filtre de cohérence des dates
        self.df = self.df.dropna(subset=['date_debut', 'date_fin'])
        self.df = self.df[self.df['date_fin'] > self.df['date_debut']].copy()

        # Filtre sur températures (Si renseignées, alors dans [800, 1300])
        if 'temperature_c' in self.df.columns:
            mask = self.df['temperature_c'].notna()
            self.df.loc[mask, 'temperature_c'] = self.df.loc[mask, 'temperature_c'].apply(
                lambda x: x if 800 <= x <= 1300 else np.nan
            )

        # Colonnes calculées
        self.df['temps_reel_min'] = (self.df['date_fin'] - self.df['date_debut']).dt.total_seconds() / 60
        # Empêcher les divisions par zéro
        self.df = self.df[self.df['temps_reel_min'] > 0].copy()
        self.df['performance_pct'] = (self.df['temps_prevu_min'] / self.df['temps_reel_min']) * 100

    def analyze(self) -> dict:
        """Exécute l'analyse et retourne le JSON contenant les KPIs et les graphiques (format imposé routes)."""
        if self.df.empty:
             raise ValueError("Le fichier de données est vide après le nettoyage des dates invalides.")
        kpis = self._compute_kpis()
        charts = self._generate_charts()
        
        return {
            "kpis": kpis,
            "charts": charts
        }

    def _compute_kpis(self) -> dict:
        """Calcule : nb_pieces_total, taux_rebut_pct, fpy_pct, performance_moy_pct, goulot, top_defaut."""
        total_pieces = self.df['piece_id'].nunique()
        pieces_nc = self.df[self.df['statut_conformite'] == 'Non-conforme']['piece_id'].nunique()
        pieces_conformes = self.df[self.df['statut_conformite'] == 'Conforme']['piece_id'].nunique()

        taux_rebut_pct = (pieces_nc / total_pieces * 100) if total_pieces > 0 else 0
        fpy_pct = (pieces_conformes / total_pieces * 100) if total_pieces > 0 else 0

        performance_moy_pct = self.df['performance_pct'].mean()
        
        # Étape Goulot (la perf la plus basse)
        perf_by_etape = self.df.groupby('etape')['performance_pct'].mean()
        goulot = perf_by_etape.idxmin() if not perf_by_etape.empty else "N/A"

        # Top défaut
        top_defaut = "Aucun"
        if 'type_defaut' in self.df.columns:
            defauts = self.df[(self.df['statut_conformite'] == 'Non-conforme') &
                              (self.df['type_defaut'].notna()) &
                              (self.df['type_defaut'] != 'nan') &
                              (self.df['type_defaut'] != '')]['type_defaut']
            if not defauts.empty:
                top_defaut = defauts.mode().iloc[0]

        return {
            "nb_pieces_total": total_pieces,
            "taux_rebut_pct": round(taux_rebut_pct, 1),
            "fpy_pct": round(fpy_pct, 1),
            "performance_moy_pct": round(performance_moy_pct, 1) if pd.notna(performance_moy_pct) else 0.0,
            "goulot": goulot,
            "top_defaut": top_defaut
        }

    def _generate_charts(self) -> dict:
        """Génère les 5 graphiques (Hist, Box, Pareto, Line Evolution, Heatmap). Retourne un dict de dict (JSON)."""
        charts = {}

        # Graphique 1: Histogramme - Distribution perf par étape
        fig1 = px.histogram(self.df, x="performance_pct", facet_col="etape", color="etape", barmode="overlay",
                            title="Distribution de la Performance (%) par Étape",
                            labels={"performance_pct": "Performance (%)", "count": "Fréquence"})
        charts["graph1"] = json.loads(fig1.to_json())

        # Graphique 2: Boîte à moustaches - Temps réel par étape, color par étape
        fig2 = px.box(self.df, x="etape", y="temps_reel_min", color="etape",
                      title="Temps Réel par Étape (Dispersion)",
                      labels={"temps_reel_min": "Temps Réel (min)", "etape": "Étape de process"})

        # Ajout des lignes de médiane (temps prévu)
        temps_prevu_med = self.df.groupby('etape')['temps_prevu_min'].median().to_dict()
        for etape, val in temps_prevu_med.items():
            fig2.add_hline(y=val, line_dash="dot", annotation_text=f"Prévu ({etape})", annotation_position="bottom right")
        charts["graph2"] = json.loads(fig2.to_json())

        # Graphique 3: Pareto - Fréquence défauts
        if 'type_defaut' in self.df.columns:
            df_defauts = self.df[(self.df['statut_conformite'] == 'Non-conforme') & (self.df['type_defaut'].notna()) & (self.df['type_defaut'] != 'nan')]
            if not df_defauts.empty:
                defaut_counts = df_defauts['type_defaut'].value_counts().reset_index()
                defaut_counts.columns = ['Défaut', 'Nombre']
                defaut_counts['Cumulé (%)'] = defaut_counts['Nombre'].cumsum() / defaut_counts['Nombre'].sum() * 100

                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=defaut_counts['Défaut'], y=defaut_counts['Nombre'], name="Fréquence", marker_color='#003d7a'))
                fig3.add_trace(go.Scatter(x=defaut_counts['Défaut'], y=defaut_counts['Cumulé (%)'], name="Cumul (%)", yaxis='y2', mode='lines+markers', line=dict(color='red')))
                fig3.update_layout(title="Pareto des Types de Défauts", yaxis=dict(title="Fréquence"), yaxis2=dict(title="Cumul (%)", overlaying='y', side='right', range=[0, 105]))
                charts["graph3"] = json.loads(fig3.to_json())
            else:
                charts["graph3"] = None
        else:
            charts["graph3"] = None

        # Graphique 4: Évolution temporelle (Rebut % & Perf)
        df_time = self.df.copy()
        df_time.set_index('date_debut', inplace=True)
        # Resample hebdomadaire : Nombre total de pièces et pièces non conformes
        weekly_total = df_time.resample('W')['piece_id'].nunique()
        weekly_nc = df_time[df_time['statut_conformite'] == 'Non-conforme'].resample('W')['piece_id'].nunique()
        weekly_perf = df_time.resample('W')['performance_pct'].mean()

        df_weekly = pd.DataFrame({
            'Total': weekly_total,
            'NC': weekly_nc,
            'Perf': weekly_perf
        }).fillna(0)

        # Filtrer les semaines avec 0 data
        df_weekly = df_weekly[df_weekly['Total'] > 0].copy()

        df_weekly['Taux_Rebut'] = (df_weekly['NC'] / df_weekly['Total']) * 100
        df_weekly['Taux_Rebut'] = df_weekly['Taux_Rebut'].fillna(0)

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=df_weekly.index, y=df_weekly['Taux_Rebut'], name="Taux de Rebut (%)", mode='lines+markers', line=dict(color='red')))
        fig4.add_trace(go.Scatter(x=df_weekly.index, y=df_weekly['Perf'], name="Performance Moy (%)", mode='lines+markers', yaxis='y2', line=dict(color='green')))
        fig4.update_layout(title="Évolution Hebdomadaire (Rebut & Performance)", xaxis_title="Semaine",
                           yaxis=dict(title="Taux de Rebut (%)", titlefont=dict(color="red"), tickfont=dict(color="red")),
                           yaxis2=dict(title="Performance (%)", titlefont=dict(color="green"), tickfont=dict(color="green"), overlaying="y", side="right"))
        charts["graph4"] = json.loads(fig4.to_json())

        # Graphique 5: Heatmap Perf x Étape x Semaine
        df_heat = self.df.copy()
        df_heat['semaine'] = df_heat['date_debut'].dt.isocalendar().week.astype(str) + "-" + df_heat['date_debut'].dt.isocalendar().year.astype(str)
        cross = pd.crosstab(index=df_heat['etape'], columns=df_heat['semaine'], values=df_heat['performance_pct'], aggfunc='mean')
        
        if not cross.empty:
            fig5 = px.imshow(cross, labels=dict(x="Semaine", y="Étape", color="Perf Moy (%)"), x=cross.columns, y=cross.index, color_continuous_scale="RdYlGn", title="Heatmap de Performance (%) par Étape et Semaine")
            charts["graph5"] = json.loads(fig5.to_json())
        else:
            charts["graph5"] = None

        return charts