"""
Cliente para interactuar con la API de GitLab
"""

import gitlab
from typing import Dict, List, Any, Optional
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
    
    def get_current_user(self) -> Dict[str, Any]:
        """Obtiene información del usuario actual"""
        return self.gl.user.__dict__['_attrs']
    
    def get_project(self, project_path: str) -> Dict[str, Any]:
        """
        Obtiene un proyecto por su ruta
        
        Args:
            project_path: Ruta del proyecto (ej: grupo/proyecto)
            
        Returns:
            Información del proyecto
        """
        project = self.gl.projects.get(project_path)
        return project.__dict__['_attrs']
    
    def create_project_if_not_exists(self, project_path: str) -> Dict[str, Any]:
        """
        Crea un proyecto si no existe
        
        Args:
            project_path: Ruta del proyecto (ej: grupo/proyecto)
            
        Returns:
            Información del proyecto
        """
        try:
            return self.get_project(project_path)
        except gitlab.exceptions.GitlabGetError:
            # El proyecto no existe, crearlo
            parts = project_path.split('/')
            
            if len(parts) == 2:
                namespace, name = parts
                # Buscar el grupo/namespace
                groups = self.gl.groups.list(search=namespace)
                if groups:
                    namespace_id = groups[0].id
                else:
                    # Crear grupo si no existe
                    group = self.gl.groups.create({'name': namespace, 'path': namespace})
                    namespace_id = group.id
                
                project = self.gl.projects.create({
                    'name': name,
                    'namespace_id': namespace_id,
                })
            else:
                # Proyecto en namespace personal
                project = self.gl.projects.create({'name': project_path})
            
            return project.__dict__['_attrs']
    
    def create_or_update_file(
        self,
        project_id: int,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = 'main'
    ) -> None:
        """
        Crea o actualiza un archivo en el repositorio
        
        Args:
            project_id: ID del proyecto
            file_path: Ruta del archivo en el repositorio
            content: Contenido del archivo
            commit_message: Mensaje del commit
            branch: Rama donde crear/actualizar el archivo
        """
        project = self.gl.projects.get(project_id)
        
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
        project_id: int,
        key: str,
        value: str,
        protected: bool = False,
        masked: bool = False,
        environment_scope: str = '*'
    ) -> None:
        """
        Crea o actualiza una variable CI/CD
        
        Args:
            project_id: ID del proyecto
            key: Nombre de la variable
            value: Valor de la variable
            protected: Si es una variable protegida
            masked: Si el valor debe enmascararse en los logs
            environment_scope: Alcance del ambiente
        """
        project = self.gl.projects.get(project_id)
        
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
    
    def get_variables(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las variables CI/CD de un proyecto
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de variables
        """
        project = self.gl.projects.get(project_id)
        variables = project.variables.list(get_all=True)
        return [var.__dict__['_attrs'] for var in variables]
    
    def get_pipelines(
        self,
        project_id: int,
        per_page: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Obtiene los pipelines de un proyecto
        
        Args:
            project_id: ID del proyecto
            per_page: Número de resultados por página
            page: Número de página
            
        Returns:
            Lista de pipelines
        """
        project = self.gl.projects.get(project_id)
        pipelines = project.pipelines.list(per_page=per_page, page=page)
        return [pipeline.__dict__['_attrs'] for pipeline in pipelines]
    
    def get_file_content(
        self,
        project_id: int,
        file_path: str,
        ref: str = 'main'
    ) -> str:
        """
        Obtiene el contenido de un archivo del repositorio
        
        Args:
            project_id: ID del proyecto
            file_path: Ruta del archivo
            ref: Rama o tag
            
        Returns:
            Contenido del archivo
        """
        project = self.gl.projects.get(project_id)
        file = project.files.get(file_path=file_path, ref=ref)
        return file.decode().decode('utf-8')
    
    def list_repository_tree(
        self,
        project_id: int,
        path: str = '',
        ref: str = 'main',
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Lista el árbol de archivos del repositorio
        
        Args:
            project_id: ID del proyecto
            path: Ruta dentro del repositorio
            ref: Rama o tag
            recursive: Si debe listar recursivamente
            
        Returns:
            Lista de archivos y directorios
        """
        project = self.gl.projects.get(project_id)
        tree = project.repository_tree(path=path, ref=ref, recursive=recursive, get_all=True)
        return [item for item in tree]
