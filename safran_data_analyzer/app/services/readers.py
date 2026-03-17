import pandas as pd
from abc import ABC, abstractmethod

class BaseReader(ABC):
    """Classe abstraite parent : définit le moule pour tous les futurs lecteurs."""
    
    @abstractmethod
    def read(self, filepath: str) -> pd.DataFrame:
        """Cette méthode devra être implémentée par toutes les classes enfants."""
        pass

class ExcelReader(BaseReader):
    """Classe enfant : Spécialiste de la lecture des fichiers Excel."""
    
    def read(self, filepath: str) -> pd.DataFrame:
        # On pourrait ajouter ici des paramètres spécifiques à Excel (onglets, etc.)
        return pd.read_excel(filepath)

# Vous pourrez ajouter plus tard :
# class CSVReader(BaseReader): ...
# class SQLReader(BaseReader): ...

class ReaderFactory:
    """L'usine qui distribue le bon lecteur selon l'extension du fichier."""
    
    @staticmethod
    def get_reader(filename: str) -> BaseReader:
        if filename.endswith(('.xlsx', '.xls')):
            return ExcelReader()
        # elif filename.endswith('.csv'): return CSVReader()
        else:
            raise ValueError(f"Format de fichier non pris en charge pour : {filename}")