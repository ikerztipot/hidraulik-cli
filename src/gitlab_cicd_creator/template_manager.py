"""
Gestor de plantillas CI/CD
"""

import os
import re
import tempfile
from typing import Dict, List, Tuple
from pathlib import Path
import gitlab
from rich.console import Console

console = Console()


class TemplateManager:
    """Gestor para cargar y procesar plantillas desde un repositorio GitLab"""
    
    def __init__(self, template_repo_path: str):
        """
        Inicializa el gestor de plantillas
        
        Args:
            template_repo_path: Ruta del repositorio de plantillas en GitLab (ej: grupo/proyecto)
        """
        self.template_repo_path = template_repo_path
        self.templates_cache = {}
    
    def load_templates(self) -> Dict[str, str]:
        """
        DEPRECATED: Las plantillas deben cargarse desde GitLab usando load_from_gitlab()
        
        Returns:
            Diccionario vacío con advertencia
        """
        console.print("[yellow]⚠[/yellow] Advertencia: load_templates() está deprecado. Usa load_from_gitlab()")
        return {}
    
    def load_from_gitlab(self, gitlab_url: str, token: str, project_path: str, ref: str = 'main') -> Dict[str, str]:
        """
        Carga plantillas desde un repositorio de GitLab
        
        Args:
            gitlab_url: URL de GitLab
            token: Token de acceso
            project_path: Ruta del proyecto con plantillas (ej: grupo/plantillas-cicd)
            ref: Rama o tag del repositorio (por defecto: main)
            
        Returns:
            Diccionario con plantillas (ruta_archivo: contenido)
        """
        try:
            gl = gitlab.Gitlab(gitlab_url, private_token=token)
            gl.auth()
            
            # Obtener el proyecto
            project = gl.projects.get(project_path)
            
            templates = {}
            
            # Listar todos los archivos del repositorio de forma recursiva
            console.print(f"  • Explorando repositorio: {project.name}")
            tree = project.repository_tree(recursive=True, get_all=True, ref=ref)
            
            # Filtrar solo archivos .j2 (plantillas Jinja2)
            template_files = [item for item in tree if item['type'] == 'blob' and item['name'].endswith('.j2')]
            
            console.print(f"  • Encontrados {len(template_files)} archivos de plantilla")
            
            # Descargar contenido de cada plantilla
            for item in template_files:
                file_path = item['path']
                try:
                    # Obtener contenido del archivo
                    file_content = project.files.get(file_path=file_path, ref=ref)
                    content = file_content.decode().decode('utf-8')
                    templates[file_path] = content
                    console.print(f"  • Cargada: {file_path}")
                except Exception as e:
                    console.print(f"  [yellow]⚠[/yellow] Error al cargar {file_path}: {str(e)}")
            
            # Cachear las plantillas
            self.templates_cache = templates
            
            return templates
            
        except gitlab.exceptions.GitlabAuthenticationError:
            console.print("[red]✗[/red] Error de autenticación. Verifica tu token de GitLab.")
            return {}
        except gitlab.exceptions.GitlabGetError as e:
            console.print(f"[red]✗[/red] Error al acceder al repositorio: {str(e)}")
            console.print(f"[yellow]⚠[/yellow] Verifica que el repositorio '{project_path}' existe y tienes permisos de lectura")
            return {}
        except Exception as e:
            console.print(f"[red]✗[/red] Error inesperado al cargar plantillas: {str(e)}")
            return {}
    
    def list_available_templates(self) -> List[str]:
        """
        Lista las plantillas disponibles (usa caché si está disponible)
        
        Returns:
            Lista de nombres de plantillas
        """
        if self.templates_cache:
            return list(self.templates_cache.keys())
        return []
    
    def get_template(self, template_name: str) -> str:
        """
        Obtiene una plantilla específica del caché
        
        Args:
            template_name: Nombre de la plantilla
            
        Returns:
            Contenido de la plantilla o cadena vacía si no existe
        """
        return self.templates_cache.get(template_name, '')
    
    def extract_variables(self, templates: Dict[str, str]) -> Tuple[List[str], List[str]]:
        """
        Extrae y clasifica variables de las plantillas Jinja2
        
        Variables que empiezan con 'CICD_' se consideran variables CI/CD que deben
        guardarse en la configuración de GitLab.
        El resto son variables de plantilla que se sustituyen directamente.
        
        Args:
            templates: Diccionario con plantillas (ruta: contenido)
            
        Returns:
            Tupla con (template_vars, cicd_vars)
        """
        all_vars = set()
        
        # Patrón para detectar variables Jinja2: {{ variable }} o {% if variable %}
        # Detecta: {{ var }}, {{ var.attr }}, {% if var %}, {% for item in items %}
        patterns = [
            r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)',  # {{ variable }}
            r'\{%\s+(?:if|elif|for|set)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # {% if variable %}
        ]
        
        for template_content in templates.values():
            for pattern in patterns:
                matches = re.findall(pattern, template_content)
                all_vars.update(matches)
        
        # Clasificar variables
        template_vars = []
        cicd_vars = []
        
        for var in sorted(all_vars):
            if var.startswith('CICD_'):
                cicd_vars.append(var)
            else:
                template_vars.append(var)
        
        return template_vars, cicd_vars
