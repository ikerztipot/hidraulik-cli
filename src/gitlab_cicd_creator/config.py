"""
Gestión de configuración del CLI
"""

import os
import json
from pathlib import Path
from typing import Any, Optional


class Config:
    """Gestor de configuración del CLI"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_dir: Directorio de configuración personalizado
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.gitlab-cicd-creator'
        
        self.config_file = self.config_dir / 'config.json'
        self.config_data = {}
        
        # Crear directorio si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar configuración existente
        self._load()
    
    def _load(self) -> None:
        """Carga la configuración desde el archivo"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config_data = json.load(f)
    
    def save(self) -> None:
        """Guarda la configuración en el archivo"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self.config_data[key] = value
    
    def delete(self, key: str) -> None:
        """
        Elimina una clave de configuración
        
        Args:
            key: Clave a eliminar
        """
        if key in self.config_data:
            del self.config_data[key]
    
    def is_configured(self) -> bool:
        """
        Verifica si la configuración básica está completa
        
        Returns:
            True si está configurado
        """
        required_keys = ['gitlab_url', 'gitlab_token', 'template_repo']
        return all(key in self.config_data for key in required_keys)
    
    def clear(self) -> None:
        """Limpia toda la configuración"""
        self.config_data = {}
        if self.config_file.exists():
            self.config_file.unlink()
