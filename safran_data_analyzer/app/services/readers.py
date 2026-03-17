"""Définition des classes de lecture de données (BaseReader, ExcelReader, Factory)."""
import pandas as pd
from abc import ABC, abstractmethod

class BaseReader(ABC):
    """Classe abstraite parent : définit le moule (interface) pour tous les futurs lecteurs."""
    
    @abstractmethod
    def read(self, filepath: str) -> pd.DataFrame:
        """Lit un fichier et le convertit en DataFrame pandas."""
        pass

class ExcelReader(BaseReader):
    """Classe enfant : Spécialiste de la lecture des fichiers Excel (.xlsx)."""

    def _verify_magic_bytes(self, filepath: str) -> bool:
        """Vérifie que les 4 premiers octets correspondent bien à un zip (PK\x03\x04)."""
        with open(filepath, 'rb') as f:
            magic_bytes = f.read(4)
        return magic_bytes == b'PK\x03\x04'
    
    def read(self, filepath: str) -> pd.DataFrame:
        """Lit un fichier Excel et le convertit en DataFrame pandas après sécurité."""
        if not self._verify_magic_bytes(filepath):
            raise ValueError("Le fichier ne semble pas être un véritable document Excel (Magic Bytes invalides).")
        return pd.read_excel(filepath)

class ReaderFactory:
    """Factory de création de lecteurs selon l'extension."""
    
    @staticmethod
    def get_reader(filename: str) -> BaseReader:
        """Renvoie l'instance de lecteur de données (ExcelReader)."""
        if filename.endswith('.xlsx'):
            return ExcelReader()
        raise ValueError(f"Format de fichier non pris en charge pour : {filename}")