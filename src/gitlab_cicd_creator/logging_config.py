"""
Configuración de logging estructurado
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(level: str = 'INFO', log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Configura logging estructurado con rotación de archivos
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directorio donde guardar logs (por defecto: ~/.gitlab-cicd-creator/logs)
    
    Returns:
        Logger configurado
    """
    if log_dir is None:
        log_dir = Path.home() / '.gitlab-cicd-creator' / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger('gitlab_cicd_creator')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Evitar duplicación de handlers
    if logger.handlers:
        return logger
    
    # Formato detallado
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo con rotación (10MB, 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'gitlab-cicd.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler para consola (solo errores críticos)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger hijo del logger principal
    
    Args:
        name: Nombre del módulo
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(f'gitlab_cicd_creator.{name}')
