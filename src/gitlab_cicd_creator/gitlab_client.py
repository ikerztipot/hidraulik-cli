"""
Cliente para interactuar con la API de GitLab
"""

import gitlab
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from rich.console import Console

console = Console()


class GitLabClient:
    """Cliente para interactuar con GitLab API"""
    
    def __init__(self, url: str, token: str):
        """
        Inicializa el cliente de GitLab
        
        Args:
            url: URL de la instancia de GitLab
            token: Token de acceso personal
        """
        self.gl = gitlab.Gitlab(url, private_token=token)
        self.gl.auth()
    
    def _get_project_safe(self, project_id):
        """
        Obtiene un proyecto manejando tanto IDs numéricos como rutas
        
        Args:
            project_id: ID numérico o ruta del proyecto (ej: grupo/subgrupo/proyecto)
            
        Returns:
            Objeto de proyecto de GitLab
        """
        # Si es string (ruta), aplicar URL encoding
        if isinstance(project_id, str):
            project_id = quote(project_id, safe='')
        return self.gl.projects.get(project_id)
    
    def get_current_user(self) -> Dict[str, Any]:
        """Obtiene información del usuario actual"""
        return self.gl.user.__dict__['_attrs']
    
    def get_project(self, project_path: str) -> Dict[str, Any]:
        """
        Obtiene un proyecto por su ruta
        
        Args:
            project_path: Ruta del proyecto (ej: grupo/proyecto o grupo/subgrupo/proyecto)
            
        Returns:
            Información del proyecto
        """
        try:
            # Intentar acceso directo primero
            project = self._get_project_safe(project_path)
            return project.__dict__['_attrs']
        except gitlab.exceptions.GitlabGetError:
            # Si falla, intentar buscar por ruta para obtener el ID
            projects = self.gl.projects.list(search=project_path.split('/')[-1], get_all=True)
            for p in projects:
                if p.path_with_namespace == project_path:
                    # Usar el ID numérico del proyecto encontrado
                    project = self.gl.projects.get(p.id)
                    return project.__dict__['_attrs']
            # Si no se encuentra, lanzar el error original
            raise
    
    def create_project_if_not_exists(self, project_path: str) -> Dict[str, Any]:
        """
        Crea un proyecto si no existe, creando grupos necesarios recursivamente
        
        Args:
            project_path: Ruta del proyecto (ej: grupo/proyecto o grupo/subgrupo/proyecto)
            
        Returns:
            Información del proyecto
        """
        try:
            return self.get_project(project_path)
        except gitlab.exceptions.GitlabGetError:
            # El proyecto no existe, crearlo
            parts = project_path.split('/')
            
            if len(parts) >= 2:
                # Separar el nombre del proyecto del namespace
                name = parts[-1]
                namespace_parts = parts[:-1]
                
                # Crear grupos recursivamente si no existen
                parent_id = None
                current_path = ""
                
                for i, group_name in enumerate(namespace_parts):
                    # Construir la ruta completa hasta este nivel
                    if current_path:
                        current_path += f"/{group_name}"
                    else:
                        current_path = group_name
                    
                    try:
                        # Intentar obtener el grupo
                        encoded_path = quote(current_path, safe='')
                        group = self.gl.groups.get(encoded_path)
                        parent_id = group.id
                        console.print(f"  [green]✓[/green] Grupo encontrado: {current_path}")
                    except gitlab.exceptions.GitlabGetError:
                        # El grupo no existe, crearlo
                        console.print(f"  [yellow]→[/yellow] Creando grupo: {current_path}")
                        
                        group_data = {
                            'name': group_name,
                            'path': group_name,
                        }
                        
                        # Si hay un grupo padre, especificarlo
                        if parent_id:
                            group_data['parent_id'] = parent_id
                        
                        try:
                            group = self.gl.groups.create(group_data)
                            parent_id = group.id
                            console.print(f"  [green]✓[/green] Grupo creado: {current_path}")
                        except Exception as e:
                            console.print(f"  [red]✗[/red] Error creando grupo {current_path}: {str(e)}")
                            raise ValueError(f"No se pudo crear el grupo '{current_path}': {str(e)}")
                
                # Ahora crear el proyecto en el último grupo
                console.print(f"  [yellow]→[/yellow] Creando proyecto: {name}")
                project = self.gl.projects.create({
                    'name': name,
                    'namespace_id': parent_id,
                })
                console.print(f"  [green]✓[/green] Proyecto creado: {project_path}")
            else:
                # Proyecto en namespace personal
                project = self.gl.projects.create({'name': project_path})
            
            return project.__dict__['_attrs']
    
    def create_or_update_file(
        self,
        project_id,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = 'main'
    ) -> None:
        """
        Crea o actualiza un archivo en el repositorio
        
        Args:
            project_id: ID del proyecto (numérico o ruta como grupo/proyecto)
            file_path: Ruta del archivo en el repositorio
            content: Contenido del archivo
            commit_message: Mensaje del commit
            branch: Rama donde crear/actualizar el archivo
        """
        project = self._get_project_safe(project_id)
        
        try:
            # Intentar obtener el archivo
            file = project.files.get(file_path=file_path, ref=branch)
            # Si existe, actualizarlo
            file.content = content
            file.save(branch=branch, commit_message=commit_message)
        except gitlab.exceptions.GitlabGetError:
            # El archivo no existe, crearlo
            project.files.create({
                'file_path': file_path,
                'branch': branch,
                'content': content,
                'commit_message': commit_message,
            })
    
    def create_or_update_variable(
        self,
        project_id,
        key: str,
        value: str,
        protected: bool = False,
        masked: bool = False,
        environment_scope: str = '*'
    ) -> None:
        """
        Crea o actualiza una variable CI/CD
        
        Args:
            project_id: ID del proyecto (numérico o ruta como grupo/proyecto)
            key: Nombre de la variable
            value: Valor de la variable
            protected: Si es una variable protegida
            masked: Si el valor debe enmascararse en los logs
            environment_scope: Alcance del ambiente
        """
        project = self._get_project_safe(project_id)
        
        try:
            # Intentar obtener la variable
            var = project.variables.get(key)
            # Si existe, actualizarla
            var.value = value
            var.protected = protected
            var.masked = masked
            var.save()
        except gitlab.exceptions.GitlabGetError:
            # La variable no existe, crearla
            project.variables.create({
                'key': key,
                'value': value,
                'protected': protected,
                'masked': masked,
                'environment_scope': environment_scope,
            })
    
    def get_variables(self, project_id) -> List[Dict[str, Any]]:
        """
        Obtiene todas las variables CI/CD de un proyecto
        
        Args:
            project_id: ID del proyecto (numérico o ruta como grupo/proyecto)
            
        Returns:
            Lista de variables
        """
        project = self._get_project_safe(project_id)
        variables = project.variables.list(get_all=True)
        return [var.__dict__['_attrs'] for var in variables]
    
    def get_pipelines(
        self,
        project_id,
        per_page: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los pipelines de un proyecto
        
        Args:
            project_id: ID del proyecto (numérico o ruta como grupo/proyecto)
            per_page: Número de resultados por página
            page: Número de página
            
        Returns:
            Lista de pipelines
        """
        project = self._get_project_safe(project_id)
        pipelines = project.pipelines.list(per_page=per_page, page=page)
        return [pipeline.__dict__['_attrs'] for pipeline in pipelines]
    
    def get_file_content(
        self,
        project_id,
        file_path: str,
        ref: str = 'main'
    ) -> str:
        """
        Obtiene el contenido de un archivo del repositorio
        
        Args:
            project_id: ID del proyecto (numérico o ruta como grupo/proyecto)
            file_path: Ruta del archivo
            ref: Rama o tag
            
        Returns:
            Contenido del archivo
        """
        project = self._get_project_safe(project_id)
        file = project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode('utf-8')
    
    def list_repository_tree(
        self,
        project_id,
        path: str = '',
        ref: str = 'main',
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Lista el árbol de archivos del repositorio
        
        Args:
            project_id: ID del proyecto (numérico o ruta como grupo/proyecto)
            path: Ruta dentro del repositorio
            ref: Rama o tag
            recursive: Si debe listar recursivamente
            
        Returns:
            Lista de archivos y directorios
        """
        project = self._get_project_safe(project_id)
        tree = project.repository_tree(path=path, ref=ref, recursive=recursive, get_all=True)
        return [item for item in tree]
