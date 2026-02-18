"""
Gestión de configuración del CLI
"""

import os
import json
from pathlib import Path
from typing import Any, Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class Config:
    """Gestor de configuración del CLI"""
    
    KEYRING_SERVICE = "hidraulik"
    KEYRING_TOKEN_KEY = "gitlab_token"
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_dir: Directorio de configuración personalizado
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.hidraulik'
        
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
        """Guarda la configuración en el archivo (sin el token)"""
        # Crear una copia sin el token para guardar
        data_to_save = {k: v for k, v in self.config_data.items() if k != 'gitlab_token'}
        
        with open(self.config_file, 'w') as f:
            json.dump(data_to_save, f, indent=2)
        
        # Si hay token en config_data, guardarlo en keyring
        if 'gitlab_token' in self.config_data:
            self._save_token_secure(self.config_data['gitlab_token'])
    
    def _save_token_secure(self, token: str) -> None:
        """
        Guarda el token de forma segura usando keyring o fallback
        
        Args:
            token: Token a guardar
        """
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_TOKEN_KEY, token)
                return
            except Exception:
                # Si falla keyring, usar fallback
                pass
        
        # Fallback: guardar en archivo con permisos restrictivos
        token_file = self.config_dir / '.token'
        token_file.write_text(token)
        # Establecer permisos solo lectura/escritura para el propietario
        token_file.chmod(0o600)
    
    def _get_token_secure(self) -> Optional[str]:
        """
        Obtiene el token de forma segura desde keyring o fallback
        
        Returns:
            Token o None si no existe
        """
        if KEYRING_AVAILABLE:
            try:
                token = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_TOKEN_KEY)
                if token:
                    return token
            except Exception:
                pass
        
        # Fallback: leer desde archivo
        token_file = self.config_dir / '.token'
        if token_file.exists():
            return token_file.read_text().strip()
        
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        # Si es el token, obtenerlo de forma segura
        if key == 'gitlab_token':
            token = self._get_token_secure()
            return token if token else default
        
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
        required_keys = ['gitlab_url', 'template_repo']
        # Verificar que exista el token (de forma segura)
        has_token = self._get_token_secure() is not None
        has_config_keys = all(key in self.config_data for key in required_keys)
        return has_config_keys and has_token
    
    def clear(self) -> None:
        """Limpia toda la configuración incluyendo el token seguro"""
        self.config_data = {}
        
        # Eliminar archivo de configuración
        if self.config_file.exists():
            self.config_file.unlink()
        
        # Eliminar token de keyring
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_TOKEN_KEY)
            except Exception:
                pass
        
        # Eliminar archivo de token fallback
        token_file = self.config_dir / '.token'
        if token_file.exists():
            token_file.unlink()
