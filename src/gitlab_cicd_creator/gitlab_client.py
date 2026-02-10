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
                            # Asegurar que obtenemos el ID correctamente
                            parent_id = group.id if hasattr(group, 'id') else group.__dict__.get('_attrs', {}).get('id')
                            if not parent_id:
                                # Recargar el grupo para obtener el ID
                                import time
                                time.sleep(0.5)  # Esperar brevemente para que GitLab procese
                                encoded_path = quote(current_path, safe='')
                                group = self.gl.groups.get(encoded_path)
                                parent_id = group.id
                            console.print(f"  [green]✓[/green] Grupo creado: {current_path} (ID: {parent_id})")
                        except gitlab.exceptions.GitlabCreateError as create_err:
                            # Si el error es "already taken", intentar obtener el grupo existente
                            if "already been taken" in str(create_err):
                                console.print(f"  [yellow]⚠[/yellow] El grupo ya existe, buscando: {current_path}")
                                try:
                                    import time
                                    time.sleep(0.5)
                                    
                                    # Si es un subgrupo (tiene parent), buscar en los subgrupos del padre
                                    if parent_id:
                                        parent_group = self.gl.groups.get(parent_id)
                                        subgroups = parent_group.subgroups.list(search=group_name, get_all=True)
                                        
                                        # Buscar el subgrupo que coincida exactamente
                                        for sg in subgroups:
                                            if sg.path == group_name:
                                                # Obtener el grupo completo
                                                group = self.gl.groups.get(sg.id)
                                                parent_id = group.id
                                                console.print(f"  [green]✓[/green] Subgrupo encontrado: {current_path} (ID: {parent_id})")
                                                break
                                        else:
                                            raise Exception(f"Subgrupo '{group_name}' no encontrado en el padre")
                                    else:
                                        # Es un grupo raíz, buscar directamente
                                        encoded_path = quote(group_name, safe='')
                                        group = self.gl.groups.get(encoded_path)
                                        parent_id = group.id
                                        console.print(f"  [green]✓[/green] Grupo encontrado: {current_path} (ID: {parent_id})")
                                        
                                except Exception as get_err:
                                    console.print(f"  [red]✗[/red] No se pudo obtener el grupo existente: {str(get_err)}")
                                    raise ValueError(f"El grupo '{current_path}' existe pero no se puede acceder: {str(get_err)}")
                            else:
                                console.print(f"  [red]✗[/red] Error creando grupo {current_path}: {str(create_err)}")
                                raise ValueError(f"No se pudo crear el grupo '{current_path}': {str(create_err)}")
                        except Exception as e:
                            console.print(f"  [red]✗[/red] Error creando grupo {current_path}: {str(e)}")
                            raise ValueError(f"No se pudo crear el grupo '{current_path}': {str(e)}")
                
                # Ahora crear el proyecto en el último grupo
                console.print(f"  [yellow]→[/yellow] Creando proyecto: {name}")
                
                if not parent_id:
                    raise ValueError(f"No se pudo obtener el ID del grupo para '{namespace_parts}'")
                
                console.print(f"  [dim]Usando namespace_id: {parent_id}[/dim]")
                
                try:
                    project = self.gl.projects.create({
                        'name': name,
                        'path': name,
                        'namespace_id': parent_id,
                    })
                    console.print(f"  [green]✓[/green] Proyecto creado: {project_path}")
                except gitlab.exceptions.GitlabCreateError as e:
                    console.print(f"  [red]✗[/red] Error al crear proyecto: {str(e)}")
                    console.print(f"  [dim]Debug - namespace_id: {parent_id}, name: {name}, path: {name}[/dim]")
                    raise ValueError(f"No se pudo crear el proyecto '{name}': {str(e)}")
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
        
        # Buscar si existe la variable con el mismo key Y scope
        # GitLab permite múltiples variables con el mismo key pero diferentes scopes
        existing_var = None
        
        try:
            # Listar todas las variables y filtrar manualmente
            # Esto es necesario porque cuando hay múltiples variables con el mismo key
            # pero diferentes scopes, project.variables.get() lanza error 409
            all_vars = project.variables.list(get_all=True)
            for var in all_vars:
                if var.key == key and var.environment_scope == environment_scope:
                    existing_var = var
                    break
        except Exception as e:
            # Si falla al listar, continuar para intentar crear
            pass
        
        try:
            if existing_var:
                # Actualizar variable existente
                existing_var.value = value
                existing_var.protected = protected
                existing_var.masked = masked
                existing_var.save()
            else:
                # Crear nueva variable
                project.variables.create({
                    'key': key,
                    'value': value,
                    'protected': protected,
                    'masked': masked,
                    'environment_scope': environment_scope,
                })
        except gitlab.exceptions.GitlabCreateError as e:
            # Si hay error al crear (ej: ya existe), intentar actualizarla
            if '409' in str(e) or 'already exists' in str(e).lower():
                # Buscar la variable específica y actualizarla
                try:
                    all_vars = project.variables.list(get_all=True)
                    for var in all_vars:
                        if var.key == key and var.environment_scope == environment_scope:
                            var.value = value
                            var.protected = protected
                            var.masked = masked
                            var.save()
                            return
                except Exception:
                    pass
            raise
    
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
    
    def get_available_runners(self, scope: str = 'all') -> List[Dict[str, Any]]:
        """
        Obtiene los runners disponibles en la instancia
        
        Args:
            scope: Alcance de runners ('active', 'paused', 'online', 'all')
            
        Returns:
            Lista de runners con sus tags y estado
        """
        try:
            # Intentar obtener runners de la instancia (requiere permisos de admin)
            runners = self.gl.runners.list(scope=scope, get_all=True)
            result = []
            
            for runner in runners:
                # El list() puede no devolver tags, hacer GET individual
                try:
                    runner_detail = self.gl.runners.get(runner.id)
                    tags = runner_detail._attrs.get('tag_list', [])
                    result.append({
                        'id': runner.id,
                        'description': getattr(runner, 'description', ''),
                        'active': getattr(runner, 'active', False),
                        'is_shared': getattr(runner, 'is_shared', False),
                        'online': getattr(runner, 'online', False),
                        'status': getattr(runner, 'status', 'unknown'),
                        'tags': tags,
                    })
                except gitlab.exceptions.GitlabGetError:
                    # Si no se puede obtener el detalle, agregar sin tags
                    result.append({
                        'id': runner.id,
                        'description': getattr(runner, 'description', ''),
                        'active': getattr(runner, 'active', False),
                        'is_shared': getattr(runner, 'is_shared', False),
                        'online': getattr(runner, 'online', False),
                        'status': getattr(runner, 'status', 'unknown'),
                        'tags': [],
                    })
            return result
        except (gitlab.exceptions.GitlabGetError, gitlab.exceptions.GitlabListError):
            # Si falla (sin permisos admin), retornar lista vacía
            return []
    
    def get_group_runners(self, group_id) -> List[Dict[str, Any]]:
        """
        Obtiene los runners disponibles en un grupo
        
        Args:
            group_id: ID del grupo (numérico o ruta)
            
        Returns:
            Lista de runners del grupo
        """
        try:
            group = self.gl.groups.get(group_id)
            runners = group.runners.list(get_all=True)
            result = []
            
            for runner in runners:
                # El list() no devuelve tags, necesitamos hacer GET individual
                try:
                    runner_detail = self.gl.runners.get(runner.id)
                    tags = runner_detail._attrs.get('tag_list', [])
                    result.append({
                        'id': runner.id,
                        'description': getattr(runner, 'description', ''),
                        'active': getattr(runner, 'active', False),
                        'is_shared': getattr(runner, 'is_shared', False),
                        'online': getattr(runner, 'online', False),
                        'status': getattr(runner, 'status', 'unknown'),
                        'tags': tags,
                    })
                except gitlab.exceptions.GitlabGetError:
                    # Si no se puede obtener el detalle, agregar sin tags
                    result.append({
                        'id': runner.id,
                        'description': getattr(runner, 'description', ''),
                        'active': getattr(runner, 'active', False),
                        'is_shared': getattr(runner, 'is_shared', False),
                        'online': getattr(runner, 'online', False),
                        'status': getattr(runner, 'status', 'unknown'),
                        'tags': [],
                    })
            return result
        except (gitlab.exceptions.GitlabGetError, gitlab.exceptions.GitlabListError):
            return []
    
    def get_project_runners(self, project_id) -> List[Dict[str, Any]]:
        """
        Obtiene los runners disponibles para un proyecto
        
        Args:
            project_id: ID del proyecto (numérico o ruta)
            
        Returns:
            Lista de runners disponibles para el proyecto
        """
        try:
            project = self._get_project_safe(project_id)
            runners = project.runners.list(get_all=True)
            result = []
            
            for runner in runners:
                # El list() no devuelve tags, hacer GET individual
                try:
                    runner_detail = self.gl.runners.get(runner.id)
                    tags = runner_detail._attrs.get('tag_list', [])
                    result.append({
                        'id': runner.id,
                        'description': getattr(runner, 'description', ''),
                        'active': getattr(runner, 'active', False),
                        'is_shared': getattr(runner, 'is_shared', False),
                        'online': getattr(runner, 'online', False),
                        'status': getattr(runner, 'status', 'unknown'),
                        'tags': tags,
                    })
                except gitlab.exceptions.GitlabGetError:
                    # Si no se puede obtener el detalle, agregar sin tags
                    result.append({
                        'id': runner.id,
                        'description': getattr(runner, 'description', ''),
                        'active': getattr(runner, 'active', False),
                        'is_shared': getattr(runner, 'is_shared', False),
                        'online': getattr(runner, 'online', False),
                        'status': getattr(runner, 'status', 'unknown'),
                        'tags': [],
                    })
            return result
        except (gitlab.exceptions.GitlabGetError, gitlab.exceptions.GitlabListError):
            return []
