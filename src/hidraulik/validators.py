"""
Validadores de inputs para prevenir errores y vulnerabilidades
"""

import re
from pathlib import Path
from typing import List

from .exceptions import ValidationError


def normalize_to_k8s_namespace(name: str) -> str:
    """
    Normaliza un nombre a formato válido para namespace de Kubernetes (RFC 1123)
    
    Args:
        name: Nombre a normalizar
        
    Returns:
        Nombre normalizado (lowercase, solo letras, números y guiones)
    """
    # Convertir a minúsculas
    normalized = name.lower()
    
    # Reemplazar caracteres no permitidos por guiones
    normalized = re.sub(r'[^a-z0-9-]', '-', normalized)
    
    # Eliminar guiones consecutivos
    normalized = re.sub(r'-+', '-', normalized)
    
    # Eliminar guiones al inicio y final
    normalized = normalized.strip('-')
    
    # Limitar a 63 caracteres
    if len(normalized) > 63:
        normalized = normalized[:63].rstrip('-')
    
    # Si queda vacío, usar default
    if not normalized:
        normalized = 'default'
    
    return normalized


def validate_k8s_namespace(namespace: str) -> bool:
    """
    Valida que el namespace cumple con RFC 1123
    
    Args:
        namespace: Nombre del namespace
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si el namespace no es válido
    """
    pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    
    if not namespace:
        raise ValidationError('namespace', namespace, 'No puede estar vacío')
    
    if len(namespace) > 63:
        raise ValidationError(
            'namespace',
            namespace,
            f'Máximo 63 caracteres (tiene {len(namespace)})'
        )
    
    if not re.match(pattern, namespace):
        raise ValidationError(
            'namespace',
            namespace,
            'Debe ser DNS-1123: minúsculas, números, guiones. '
            'No puede empezar/terminar con guión'
        )
    
    return True


def validate_project_path(project_path: str) -> bool:
    """
    Valida formato de proyecto GitLab (namespace/proyecto o grupo/subgrupo/proyecto)
    
    Args:
        project_path: Ruta del proyecto
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si el formato no es válido
    """
    if not project_path:
        raise ValidationError('project_path', project_path, 'No puede estar vacío')
    
    # Debe tener al menos un /
    if '/' not in project_path:
        raise ValidationError(
            'project_path',
            project_path,
            'Debe incluir namespace (ej: grupo/proyecto)'
        )
    
    # No debe empezar ni terminar con /
    if project_path.startswith('/') or project_path.endswith('/'):
        raise ValidationError(
            'project_path',
            project_path,
            'No puede empezar ni terminar con /'
        )
    
    # Validar cada parte (grupo/subgrupo/proyecto)
    parts = project_path.split('/')
    for part in parts:
        if not part:
            raise ValidationError(
                'project_path',
                project_path,
                'No puede contener // (barras consecutivas)'
            )
        
        # GitLab permite letras, números, _, -, .
        if not re.match(r'^[a-zA-Z0-9_.-]+$', part):
            raise ValidationError(
                'project_path',
                project_path,
                f'Parte inválida: "{part}". Solo se permiten letras, números, _, -, .'
            )
    
    return True


def validate_variable_name(var_name: str) -> bool:
    """
    Valida nombre de variable de entorno (estilo shell)
    
    Args:
        var_name: Nombre de la variable
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si el nombre no es válido
    """
    if not var_name:
        raise ValidationError('variable_name', var_name, 'No puede estar vacío')
    
    # Debe empezar con letra mayúscula o _
    # Puede contener letras mayúsculas, números y _
    pattern = r'^[A-Z_][A-Z0-9_]*$'
    
    if not re.match(pattern, var_name):
        raise ValidationError(
            'variable_name',
            var_name,
            'Debe empezar con letra mayúscula o _ y solo contener A-Z, 0-9, _'
        )
    
    # Advertir sobre nombres reservados comunes
    reserved = {'PATH', 'HOME', 'USER', 'SHELL', 'PWD', 'TERM'}
    if var_name in reserved:
        raise ValidationError(
            'variable_name',
            var_name,
            f'Nombre reservado del sistema. Usa otro nombre'
        )
    
    return True


def validate_component_name(component: str) -> bool:
    """
    Valida nombre de componente
    
    Args:
        component: Nombre del componente
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si el nombre no es válido
    """
    if not component:
        raise ValidationError('component', component, 'No puede estar vacío')
    
    # Debe ser alfanumérico con guiones (para paths y DNS)
    pattern = r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'
    
    if not re.match(pattern, component):
        raise ValidationError(
            'component',
            component,
            'Debe ser minúsculas, números, guiones. No puede empezar/terminar con guión'
        )
    
    if len(component) > 63:
        raise ValidationError(
            'component',
            component,
            f'Máximo 63 caracteres (tiene {len(component)})'
        )
    
    return True


def sanitize_file_path(file_path: str) -> str:
    """
    Sanitiza una ruta de archivo para prevenir path traversal
    
    Args:
        file_path: Ruta del archivo
        
    Returns:
        Ruta sanitizada
        
    Raises:
        ValidationError: Si la ruta contiene elementos peligrosos
    """
    if not file_path:
        raise ValidationError('file_path', file_path, 'No puede estar vacío')
    
    # Normalizar la ruta
    normalized = Path(file_path).as_posix()
    
    # Verificar que no contiene .. (path traversal)
    if '..' in normalized:
        raise ValidationError(
            'file_path',
            file_path,
            'No se permite .. (path traversal) en la ruta'
        )
    
    # No debe ser ruta absoluta (para archivos en repo)
    if normalized.startswith('/'):
        raise ValidationError(
            'file_path',
            file_path,
            'Debe ser ruta relativa (no empezar con /)'
        )
    
    return normalized


def validate_port(port: str) -> bool:
    """
    Valida número de puerto
    
    Args:
        port: Puerto como string
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si el puerto no es válido
    """
    try:
        port_num = int(port)
    except ValueError:
        raise ValidationError('port', port, 'Debe ser un número entero')
    
    if not (1 <= port_num <= 65535):
        raise ValidationError(
            'port',
            port,
            f'Debe estar entre 1 y 65535 (es {port_num})'
        )
    
    return True


def validate_storage_size(size: str) -> bool:
    """
    Valida tamaño de storage de Kubernetes (ej: 5Gi, 10Mi)
    
    Args:
        size: Tamaño como string
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si el tamaño no es válido
    """
    pattern = r'^\d+(\.\d+)?(Mi|Gi|Ti|M|G|T)$'
    
    if not re.match(pattern, size):
        raise ValidationError(
            'storage_size',
            size,
            'Formato inválido. Usa: 5Gi, 10Mi, 1Ti, etc.'
        )
    
    return True


def validate_runner_tags(tags: List[str]) -> bool:
    """
    Valida lista de tags de runner
    
    Args:
        tags: Lista de tags
        
    Returns:
        True si es válido
        
    Raises:
        ValidationError: Si los tags no son válidos
    """
    if not tags:
        raise ValidationError('runner_tags', str(tags), 'Debe tener al menos un tag')
    
    for tag in tags:
        if not tag or not tag.strip():
            raise ValidationError('runner_tags', tag, 'Tag vacío no permitido')
        
        # Tags suelen ser alfanuméricos con guiones y underscore
        if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
            raise ValidationError(
                'runner_tags',
                tag,
                f'Tag "{tag}" contiene caracteres inválidos. Solo a-z, A-Z, 0-9, -, _'
            )
    
    return True
