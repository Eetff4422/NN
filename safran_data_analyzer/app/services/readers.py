import pandas as pd
from abc import ABC, abstractmethod

class BaseReader(ABC):
    """
    Classe abstraite parent : définit le moule (interface) pour tous les futurs lecteurs
    de données.
    """
    
    @abstractmethod
    def read(self, filepath: str) -> pd.DataFrame:
        """
        Lit un fichier et le convertit en DataFrame pandas.

        Args:
            filepath (str): Le chemin absolu ou relatif vers le fichier à lire.

        Returns:
            pd.DataFrame: Les données extraites du fichier.
        """
        pass

class ExcelReader(BaseReader):
    """
    Classe enfant : Spécialiste de la lecture des fichiers Excel (.xls, .xlsx).
    """
    
    def read(self, filepath: str) -> pd.DataFrame:
        """
        Lit un fichier Excel et le convertit en DataFrame pandas.

        Args:
            filepath (str): Le chemin absolu ou relatif vers le fichier Excel.

        Returns:
            pd.DataFrame: Les données extraites du fichier Excel.
        """
        return pd.read_excel(filepath)

# Vous pourrez ajouter plus tard :
# class CSVReader(BaseReader): ...
# class SQLReader(BaseReader): ...

class ReaderFactory:
    """
    Factory de création de lecteurs : distribue le bon lecteur selon l'extension
    du fichier fourni.
    """
    
    @staticmethod
    def get_reader(filename: str) -> BaseReader:
        """
        Détermine et renvoie la bonne instance de lecteur de données (BaseReader).

        Args:
            filename (str): Le nom du fichier ou chemin pour vérifier l'extension.

        Returns:
            BaseReader: L'instance de lecteur appropriée (e.g. ExcelReader).

        Raises:
            ValueError: Si le format du fichier n'est pas pris en charge.
        """
        if filename.endswith(('.xlsx', '.xls')):
            return ExcelReader()
        # elif filename.endswith('.csv'): return CSVReader()
        else:
            raise ValueError(f"Format de fichier non pris en charge pour : {filename}")