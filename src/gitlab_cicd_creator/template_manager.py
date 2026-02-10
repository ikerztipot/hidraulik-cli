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
    
    # Mapeo de carpetas de plantillas a rutas de destino en el proyecto
    TEMPLATE_PATHS = {
        'pipeline': '',           # Raíz del proyecto (.gitlab-ci.yml)
        'k8s': 'k8s',            # Carpeta k8s/ para manifiestos
        'helm': 'helm',          # Carpeta helm/ para charts
        'config': 'config',      # Carpeta config/ para configuraciones
        'includes': None,        # Archivos remotos (no se copian)
    }
    
    def __init__(self, template_repo_path: str):
        """
        Inicializa el gestor de plantillas
        
        Args:
            template_repo_path: Ruta del repositorio de plantillas en GitLab (ej: grupo/proyecto)
        """
        self.template_repo_path = template_repo_path
        self.templates_cache = {}
        self.template_types = {}  # Mapeo de archivo -> tipo de plantilla
    
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
            # Excluir archivos en includes/ ya que son referencias remotas
            template_files = [
                item for item in tree 
                if item['type'] == 'blob' 
                and item['name'].endswith('.j2')
                and not item['path'].startswith('includes/')
            ]
            
            console.print(f"  • Encontrados {len(template_files)} archivos de plantilla")
            
            # Descargar contenido de cada plantilla
            for item in template_files:
                file_path = item['path']
                
                # Detectar tipo de plantilla
                template_type = self._detect_template_type(file_path)
                
                try:
                    # Obtener contenido del archivo
                    file_content = project.files.get(file_path=file_path, ref=ref)
                    content = file_content.decode().decode('utf-8')
                    
                    # Calcular ruta de destino (sin .j2)
                    dest_path = self._calculate_dest_path(file_path, template_type)
                    
                    # Usar la ruta de destino como clave
                    templates[dest_path] = content
                    self.template_types[dest_path] = template_type
                    
                    # Mostrar con información de tipo
                    type_color = "cyan" if template_type != 'unknown' else "yellow"
                    console.print(f"  • Cargada: {file_path} → {dest_path} ([{type_color}]{template_type}[/{type_color}])")
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
    
    def _detect_template_type(self, file_path: str) -> str:
        """
        Detecta el tipo de plantilla según la carpeta
        
        Args:
            file_path: Ruta del archivo en el repositorio (ej: pipeline/.gitlab-ci.yml.j2)
            
        Returns:
            Tipo de plantilla: 'pipeline', 'k8s', 'helm', 'config', o 'unknown'
        """
        parts = file_path.split('/')
        if len(parts) > 1:
            first_dir = parts[0]
            if first_dir in self.TEMPLATE_PATHS:
                return first_dir
        return 'unknown'
    
    def _calculate_dest_path(self, file_path: str, template_type: str) -> str:
        """
        Calcula la ruta de destino del archivo en el proyecto
        
        Args:
            file_path: Ruta original en el repo de plantillas (ej: pipeline/.gitlab-ci.yml.j2)
            template_type: Tipo de plantilla detectado
            
        Returns:
            Ruta de destino (ej: .gitlab-ci.yml o k8s/deployment.yaml)
        """
        # Remover la extensión .j2
        file_path = file_path[:-3] if file_path.endswith('.j2') else file_path
        
        # Remover la carpeta de tipo de plantilla del path
        parts = file_path.split('/')
        if len(parts) > 1 and parts[0] == template_type:
            # Remover el primer directorio (pipeline/, k8s/, etc.)
            file_name = '/'.join(parts[1:])
        else:
            file_name = file_path
        
        # Agregar el prefijo de carpeta de destino según el tipo
        dest_prefix = self.TEMPLATE_PATHS.get(template_type, '')
        
        if dest_prefix:
            return f"{dest_prefix}/{file_name}"
        else:
            return file_name
    
    def get_templates_by_type(self, template_type: str) -> Dict[str, str]:
        """
        Obtiene las plantillas de un tipo específico
        
        Args:
            template_type: Tipo de plantilla ('pipeline', 'k8s', 'helm', etc.)
            
        Returns:
            Diccionario con plantillas del tipo especificado
        """
        return {
            path: content 
            for path, content in self.templates_cache.items()
            if self.template_types.get(path) == template_type
        }
    
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
        
        # Variables de loop internas de Jinja2 que no deben pedirse al usuario
        jinja_loop_vars = {'env', 'component', 'tag', 'idx', 'item', 'key', 'value', 'index', 'loop'}
        
        # Clasificar variables
        template_vars = []
        cicd_vars = []
        
        for var in sorted(all_vars):
            # Ignorar variables de loop de Jinja2
            if var in jinja_loop_vars:
                continue
            
            if var.startswith('CICD_'):
                cicd_vars.append(var)
            else:
                template_vars.append(var)
        
        return template_vars, cicd_vars
    
    def get_remote_includes(self, gitlab_url: str, token: str, ref: str = 'main') -> List[str]:
        """Obtiene la lista de archivos remotos disponibles en includes/.
        
        Estos archivos se incluyen directamente desde el repositorio remoto
        sin copiarlos al proyecto destino.
        
        Args:
            gitlab_url: URL de GitLab
            token: Token de acceso
            ref: Rama o tag del repositorio (por defecto: main)
            
        Returns:
            Lista de rutas de archivos en includes/
        """
        try:
            gl = gitlab.Gitlab(gitlab_url, private_token=token)
            gl.auth()
            
            project = gl.projects.get(self.template_repo_path)
            tree = project.repository_tree(recursive=True, get_all=True, ref=ref)
            
            includes = []
            for item in tree:
                if item['type'] == 'blob' and item['path'].startswith('includes/'):
                    includes.append(item['path'])
            
            return sorted(includes)
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] No se pudo cargar archivos remotos: {e}")
            return []
    
    def extract_variables_from_includes(self, templates: Dict[str, str], gitlab_url: str, token: str, ref: str = 'main') -> List[str]:
        """Extrae variables requeridas por archivos remotos incluidos en las plantillas.
        
        Las variables deben estar marcadas con comentarios especiales en los includes:
        # @requires: VAR1, VAR2, VAR3
        
        Args:
            templates: Diccionario con plantillas cargadas
            gitlab_url: URL de GitLab
            token: Token de acceso
            ref: Rama o tag del repositorio
            
        Returns:
            Lista de variables únicas encontradas en archivos incluidos
        """
        include_vars = set()
        
        try:
            gl = gitlab.Gitlab(gitlab_url, private_token=token)
            gl.auth()
            project = gl.projects.get(self.template_repo_path)
            
            # Debug: listar todos los archivos del repositorio
            console.print(f"[dim]    → Listando archivos del repositorio...[/dim]")
            try:
                tree = project.repository_tree(recursive=True, ref=ref, get_all=True)
                include_files = [item['path'] for item in tree if item['path'].startswith('include')]
                if include_files:
                    console.print(f"[dim]    → Archivos encontrados en includes: {', '.join(include_files)}[/dim]")
                else:
                    console.print(f"[yellow]    ⚠ No hay archivos en carpetas include*[/yellow]")
            except Exception as e:
                console.print(f"[dim]    → No se pudo listar: {str(e)[:50]}[/dim]")
            
            # Buscar includes en las plantillas
            for template_content in templates.values():
                # Detectar includes remotos: file: '/includes/...'
                include_pattern = r"file:\s*['\"](/includes/[^'\"]+)['\"]"
                includes = re.findall(include_pattern, template_content)
                
                for include_path in includes:
                    try:
                        # Limpiar el path (remover / inicial)
                        clean_path = include_path.lstrip('/')
                        console.print(f"[dim]    → Buscando: {clean_path} (rama: {ref})[/dim]")
                        
                        # Descargar el archivo incluido
                        file_content = project.files.get(file_path=clean_path, ref=ref)
                        content = file_content.decode().decode('utf-8')
                        
                        # Buscar comentarios @requires
                        # Formato: # @requires: VAR1, VAR2, VAR3
                        requires_pattern = r'#\s*@requires?:\s*([A-Z_][A-Z0-9_,\s]*)'
                        matches = re.findall(requires_pattern, content, re.IGNORECASE)
                        
                        for match in matches:
                            # Separar variables por comas y limpiar espacios
                            vars_list = [v.strip() for v in match.split(',') if v.strip()]
                            include_vars.update(vars_list)
                            
                        console.print(f"[dim]    ✓ Analizado: {clean_path}[/dim]")
                            
                    except Exception as e:
                        console.print(f"[dim]    → No se pudo analizar {include_path}: {str(e)[:50]}[/dim]")
                        
        except Exception as e:
            console.print(f"[dim]    → Error analizando includes remotos: {str(e)[:50]}[/dim]")
        
        return sorted(list(include_vars))
