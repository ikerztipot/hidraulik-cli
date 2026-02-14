"""
CLI principal para Hidraulik
"""

import click
import gitlab
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from urllib.parse import quote

from .config import Config
from .gitlab_client import GitLabClient
from .k8s_generator import K8sGenerator
from .template_manager import TemplateManager
from .services import VariableService, RunnerService, K8sConfigService
from .validators import (
    validate_k8s_namespace,
    validate_project_path,
    validate_component_name,
    sanitize_file_path
)
from .exceptions import (
    GitLabCICDError,
    AuthenticationError,
    ProjectNotFoundError,
    ValidationError,
    ConfigurationError
)
from .logging_config import setup_logging, get_logger

console = Console()
logger = get_logger('cli')

# Inicializar logging
setup_logging()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    Hidraulik - Genera automáticamente pipelines CI/CD para Kubernetes
    
    Este CLI ayuda a configurar pipelines CI/CD en repositorios de GitLab,
    utilizando plantillas personalizables para despliegues en Kubernetes.
    """
    pass


@main.command()
@click.option('--gitlab-url', help='URL de GitLab (ej: https://gitlab.com)')
@click.option('--token', help='Token de acceso personal de GitLab')
@click.option('--template-repo', help='URL del repositorio con las plantillas')
def init(gitlab_url, token, template_repo):
    """
    Inicializa la configuración del CLI
    """
    console.print(Panel.fit(
        "[bold blue]Inicialización de Hidraulik[/bold blue]",
        border_style="blue"
    ))
    
    config = Config()
    
    # Solicitar configuración si no se proporcionó
    if not gitlab_url:
        gitlab_url = Prompt.ask(
            "URL de GitLab",
            default=config.get('gitlab_url', 'https://gitlab.com')
        )
    
    # Limpiar y validar URL
    gitlab_url = gitlab_url.strip().rstrip('/')
    if not gitlab_url.startswith('http'):
        gitlab_url = f"https://{gitlab_url}"
    
    if not token:
        token = Prompt.ask("Token de acceso personal de GitLab", password=True)
    
    # Limpiar token
    token = token.strip()
    
    if not template_repo:
        template_repo = Prompt.ask(
            "Ruta del repositorio de plantillas (ej: grupo/plantillas-cicd)",
            default=config.get('template_repo', '')
        )
    
    # Limpiar ruta del repositorio
    template_repo = template_repo.strip()
        
    # Validar que el repositorio de plantillas no esté vacío
    if not template_repo or template_repo.strip() == '':
        console.print("[red]✗[/red] El repositorio de plantillas es obligatorio")
        return
    
    # Verificar conexión y repositorio de plantillas
    try:
        console.print(f"\n[dim]Conectando con {gitlab_url}...[/dim]")
        client = GitLabClient(gitlab_url, token)
        user = client.get_current_user()
        console.print(f"[green]✓[/green] Conectado como: {user['username']}")
        
        # Verificar el tipo y alcance del token
        console.print("\n[dim]Verificando permisos del token...[/dim]")
        try:
            # Intentar listar proyectos del usuario para verificar alcance del token
            test_projects = client.gl.projects.list(membership=True, per_page=1, get_all=False)
            if test_projects:
                console.print(f"[green]✓[/green] Token con acceso a proyectos del usuario/grupo")
            else:
                console.print("[yellow]⚠[/yellow] Advertencia: El token parece tener alcance limitado")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Advertencia: Token con permisos limitados")
            console.print("[dim]Si es un Project Access Token, solo funcionará con el repo de plantillas[/dim]")
        
        # Verificar que el repositorio de plantillas existe
        console.print(f"\n[dim]Verificando repositorio de plantillas: {template_repo}...[/dim]")
        try:
            templates_project = client.get_project(template_repo)
            console.print(f"[green]✓[/green] Repositorio encontrado: {templates_project['name']}")
            
            # Verificar que hay archivos en el repositorio
            console.print("[dim]Escaneando plantillas disponibles...[/dim]")
            tree = client.list_repository_tree(templates_project['id'], recursive=True)
            template_files = [item for item in tree if item['type'] == 'blob' and item['name'].endswith('.j2')]
            
            if template_files:
                console.print(f"[green]✓[/green] Se encontraron {len(template_files)} plantillas")
            else:
                console.print("[yellow]⚠[/yellow] Advertencia: No se encontraron archivos de plantilla (.j2) en el repositorio")
                
        except Exception as e:
            console.print(f"[red]✗[/red] Error al acceder al repositorio de plantillas: {str(e)}")
            console.print("[yellow]⚠[/yellow] Verifica que:")
            console.print("  • La ruta del repositorio es correcta (formato: grupo/proyecto)")
            console.print("  • Tienes permisos de lectura en el repositorio")
            console.print("  • El repositorio existe y contiene plantillas .j2")
            
            # Intentar buscar proyectos similares (limitado)
            if Confirm.ask("\n¿Buscar proyectos similares que contengan 'infrastructure'?", default=False):
                console.print("[dim]Buscando proyectos (esto puede tardar)...[/dim]")
                try:
                    all_projects = client.gl.projects.list(search='infrastructure', per_page=20, get_all=False)
                    matching = [p for p in all_projects if 'infrastructure' in p.path_with_namespace.lower()]
                    
                    if matching:
                        console.print(f"Se encontraron {len(matching)} proyectos similares:")
                        for p in matching[:10]:
                            console.print(f"  • {p.path_with_namespace}")
                        if len(matching) > 10:
                            console.print(f"  ... y {len(matching) - 10} más")
                    else:
                        console.print("No se encontraron proyectos similares")
                except Exception as search_err:
                    console.print(f"[dim]No se pudo buscar proyectos: {str(search_err)}[/dim]")
            
            return
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error al conectar con GitLab: {str(e)}")
        return
    
    # Guardar configuración solo si todo está correcto
    config.set('gitlab_url', gitlab_url)
    config.set('gitlab_token', token)
    config.set('template_repo', template_repo)
    config.save()
    
    console.print("\n[green]✓[/green] Configuración guardada exitosamente")
    console.print("\nYa puedes usar el CLI con: hidraulik create <proyecto>")


@main.command()
@click.argument('project_path')
@click.option('--namespace', help='Namespace de Kubernetes', required=True)
@click.option('--environments', help='Entornos a configurar (separados por coma)', default='dev,pre,pro')
@click.option('--create-project', is_flag=True, help='Crear nuevo proyecto si no existe')
def create(project_path, namespace, environments, create_project):
    """
    Crea el CI/CD para un repositorio de GitLab
    
    PROJECT_PATH: Ruta del proyecto en GitLab (ej: grupo/proyecto)
    """
    try:
        logger.info(f"Iniciando creación de CI/CD para {project_path}")
        console.print(f"\n[bold blue]→[/bold blue] Configurando CI/CD: [bold]{project_path}[/bold]\n")
        
        # Validar inputs
        validate_project_path(project_path)
        validate_k8s_namespace(namespace)
        
        # Cargar configuración
        config = Config()
        if not config.is_configured():
            raise ConfigurationError(
                "No hay configuración. Ejecuta: hidraulik init"
            )
        
        # Conectar a GitLab
        client = _connect_to_gitlab(config)
        
        # Obtener o crear proyecto
        project = _get_or_create_project(client, project_path, create_project)
        
        # Configurar servicios
        variable_service = VariableService(console)
        runner_service = RunnerService(client, console)
        k8s_service = K8sConfigService(console)
        
        # Descubrir runners
        console.print("[dim]Descubriendo runners...[/dim]")
        available_runners = runner_service.discover_available_runners(
            project_path,
            config.get('template_repo')
        )
        if available_runners:
            console.print(f"[green]✓[/green] {len(available_runners)} runner(s) disponible(s)")
        
        # Recopilar configuración
        project_config = _collect_project_configuration(
            project_path,
            namespace,
            environments
        )
        
        # Configurar componentes
        components_config = _configure_components(
            project_config['components'],
            variable_service,
            k8s_service
        )
        
        # Seleccionar runner
        console.print("\n[bold]Selecciona el runner:[/bold]")
        default_runner_tags = ['buildkit', 'scaleway', 'worko-internal']
        runner_tags = runner_service.select_runner_interactive(
            available_runners,
            default_runner_tags
        )
        
        # Configurar clusters por entorno
        kube_contexts = _configure_kube_contexts(
            client,
            project_config['environments'],
            config.get('template_repo'),
            project_path
        )
        components_config['kube_contexts'] = kube_contexts
        
        # Cargar plantillas
        templates = _load_templates(config, components_config['k8s_manifests'])
        if not templates:
            logger.error("No se pudieron cargar las plantillas")
            raise ConfigurationError("No se encontraron plantillas")
        
        # Generar y crear archivos
        files_created = _generate_and_create_files(
            client,
            project,
            templates,
            {**project_config, **components_config, 'runner_tags': runner_tags}
        )
        
        console.print(f"[green]✓[/green] {files_created} archivo(s) creado(s)")
        
        # Configurar variables CI/CD
        console.print("[dim]Configurando variables...[/dim]")
        variables_count = variable_service.create_gitlab_variables(
            client,
            project['id'],
            components_config['config_vars'],
            components_config['secret_vars'],
            components_config['kube_contexts']
        )
        console.print(f"[green]✓[/green] Variables configuradas")
        
        # Mostrar variables pendientes
        variable_service.display_pending_configuration(
            components_config['config_vars'],
            components_config['secret_vars'],
            project['web_url']
        )
        
        # Resumen final
        console.print(f"\n[bold green]✓ CI/CD configurado![/bold green]")
        console.print(f"[dim]Ver pipeline:[/dim] {project['web_url']}/-/pipelines")
        
        logger.info(f"CI/CD creado exitosamente para {project_path}")
        
    except ValidationError as e:
        console.print(f"[red]✗[/red] {e.message}")
        console.print(f"[dim]{e.reason}[/dim]")
        logger.error(f"Error de validación: {e.message}")
    except AuthenticationError as e:
        console.print(f"[red]✗[/red] {e.message}")
        console.print("\n[yellow]💡 Solución:[/yellow]")
        console.print("  1. Genera un nuevo token en GitLab")
        console.print(f"     [cyan]{config.get('gitlab_url')}/-/user_settings/personal_access_tokens[/cyan]")
        console.print("  2. Permisos requeridos: [bold]api[/bold], [bold]read_repository[/bold], [bold]write_repository[/bold]")
        console.print("  3. Reinicializa: [cyan]hidraulik init[/cyan]")
        logger.error(f"Error de autenticación: {e.message}")
    except ProjectNotFoundError as e:
        console.print(f"[red]✗[/red] {e.message}")
        console.print(f"[yellow]💡[/yellow] Usa: [cyan]--create-project[/cyan] para crearlo")
        logger.error(f"Proyecto no encontrado: {e.project_path}")
    except GitLabCICDError as e:
        console.print(f"[red]✗[/red] {e.message}")
        if e.details:
            console.print(f"[dim]Detalles: {e.details}[/dim]")
        logger.error(f"Error: {e.message}", extra=e.details)
    except Exception as e:
        console.print(f"[red]✗[/red] Error inesperado: {str(e)}")
        logger.exception("Error inesperado")
        raise


def _connect_to_gitlab(config: Config) -> GitLabClient:
    """Conecta a GitLab y maneja errores de autenticación"""
    try:
        client = GitLabClient(config.get('gitlab_url'), config.get('gitlab_token'))
        console.print("[dim]Conectado a GitLab[/dim]")
        logger.info("Conexión a GitLab establecida")
        return client
    except Exception as e:
        error_msg = str(e).lower()
        if '401' in error_msg or 'invalid_token' in error_msg or 'unauthorized' in error_msg:
            raise AuthenticationError("Token inválido o expirado")
        raise


def _get_or_create_project(client: GitLabClient, project_path: str, create_project: bool):
    """Obtiene o crea un proyecto"""
    try:
        if create_project:
            project = client.create_project_if_not_exists(project_path)
            console.print(f"[green]✓[/green] Proyecto: {project['name']}")
        else:
            project = client.get_project(project_path)
            console.print(f"[green]✓[/green] Proyecto: {project['name']}")
        
        logger.info(f"Proyecto obtenido/creado: {project['name']}")
        return project
    except ValueError as e:
        raise ConfigurationError(str(e))
    except Exception as e:
        if "404" in str(e):
            raise ProjectNotFoundError(project_path)
        raise


def _collect_project_configuration(project_path: str, namespace: str, environments: str) -> dict:
    """Recopila configuración básica del proyecto"""
    console.print("\n[bold]Configuración:[/bold]")
    
    # Componentes
    project_name = project_path.split('/')[-1]
    components_input = Prompt.ask(
        "Componentes (separados por coma)",
        default="web"
    )
    components = [c.strip() for c in components_input.split(',') if c.strip()]
    
    # Validar nombres de componentes
    for component in components:
        validate_component_name(component)
    
    # Docker
    use_docker = Confirm.ask("¿Usa Docker?", default=True)
    
    dockerfile_paths = {}
    container_ports = {}
    
    if use_docker:
        # Crear servicio K8s temporalmente para validar puertos
        k8s_temp_service = K8sConfigService(console)
        
        for component in components:
            default_path = (
                "Dockerfile" if len(components) == 1
                else f"{component}/Dockerfile"
            )
            dockerfile_path = Prompt.ask(
                f"Dockerfile de '{component}'",
                default=default_path
            )
            dockerfile_paths[component] = dockerfile_path
            
            port = k8s_temp_service.configure_container_port(component)
            container_ports[component] = port
            console.print(
                f"  [green]✓[/green] {component}: {dockerfile_path} (puerto {port})"
            )
    
    # Prefijo de tags
    suggested_prefix = (
        project_name.split('-')[0] if '-' in project_name
        else project_name[:4]
    )
    tag_prefix = Prompt.ask(
        "Prefijo para tags de release",
        default=suggested_prefix
    )
    
    # Parsear entornos
    env_list = [e.strip() for e in environments.split(',')]
    
    logger.info(f"Configuración recopilada: {len(components)} componentes, {len(env_list)} entornos")
    
    return {
        'project_name': project_name[:63],  # Limitar longitud
        'project_path': project_path,
        'namespace': namespace,
        'environments': env_list,
        'components': components,
        'use_docker': use_docker,
        'dockerfile_paths': dockerfile_paths,
        'container_ports': container_ports,
        'tag_prefix': tag_prefix,
        'template_repo': None,  # Se añadirá después
    }


def _configure_components(components: list, variable_service: VariableService, k8s_service: K8sConfigService) -> dict:
    """Configura variables, K8s y recursos para cada componente"""
    # Variables de entorno
    console.print("\n[bold]Variables de entorno:[/bold]")
    config_vars = {}
    secret_vars = {}
    
    for component in components:
        comp_config, comp_secret = variable_service.collect_component_variables(component)
        if comp_config:
            config_vars[component] = comp_config
        if comp_secret:
            secret_vars[component] = comp_secret
    
    # Deployment K8s
    console.print("\n[bold]Despliegue en Kubernetes:[/bold]")
    k8s_deployment = {}
    k8s_manifests = {}
    resource_profiles = {}
    pvc_volumes = {}
    
    for component in components:
        has_configs = component in config_vars
        has_secrets = component in secret_vars
        
        deploy, manifests = k8s_service.configure_component_deployment(
            component,
            has_configs,
            has_secrets
        )
        
        k8s_deployment[component] = deploy
        k8s_manifests[component] = manifests
        
        if deploy:
            # Perfil de recursos
            profile = k8s_service.select_resource_profile(component)
            resource_profiles[component] = profile
            
            # PVC si está habilitado
            if 'pvc' in manifests:
                volumes = k8s_service.configure_pvc_volumes(component)
                if volumes:
                    pvc_volumes[component] = volumes
    
    logger.info(f"Componentes configurados: {len(k8s_deployment)} deployments")
    
    return {
        'config_vars': config_vars,
        'secret_vars': secret_vars,
        'k8s_deployment': k8s_deployment,
        'k8s_manifests': k8s_manifests,
        'resource_profiles': resource_profiles,
        'pvc_volumes': pvc_volumes,
    }


def _configure_kube_contexts(client: GitLabClient, env_list: list, template_repo: str, project_path: str) -> dict:
    """Configura contextos de Kubernetes por entorno"""
    kube_contexts = {}
    
    console.print("\n[bold]Clusters por entorno:[/bold]")
    
    # Descubrir clusters/agents disponibles
    console.print("\n[dim]Descubriendo clusters disponibles...[/dim]")
    clusters = []
    
    # Función para buscar agentes en un grupo
    def get_agents_from_group(group_path: str):
        try:
            from urllib.parse import quote
            encoded_path = quote(group_path, safe='')
            group = client.gl.groups.get(encoded_path)
            projects = group.projects.list(get_all=True)
            
            for proj in projects:
                try:
                    full_proj = client.gl.projects.get(proj.id)
                    agents = full_proj.cluster_agents.list(get_all=True)
                    
                    for agent in agents:
                        cluster_context = f"{proj.path_with_namespace}:{agent.name}"
                        # Evitar duplicados
                        if not any(c['context'] == cluster_context for c in clusters):
                            clusters.append({
                                'name': agent.name,
                                'context': cluster_context,
                                'config_project': proj.path_with_namespace,
                                'type': 'group'
                            })
                except Exception:
                    pass
        except Exception:
            pass
    
    # Buscar en grupos padre del template_repo
    if template_repo:
        template_parts = template_repo.split('/')
        # Buscar desde el grupo raíz hasta el template repo
        for i in range(1, len(template_parts)):
            group_path = '/'.join(template_parts[:i])
            get_agents_from_group(group_path)
    
    # Buscar en grupos padre del proyecto actual
    if project_path:
        project_parts = project_path.split('/')
        for i in range(1, len(project_parts)):
            group_path = '/'.join(project_parts[:i])
            get_agents_from_group(group_path)
    
    # Mostrar clusters encontrados
    if clusters:
        console.print(f"\n[green]✓[/green] {len(clusters)} cluster(s) encontrado(s):")
        for i, cluster in enumerate(clusters, 1):
            type_label = f"[dim]({cluster['config_project']})[/dim]"
            console.print(f"  {i}. [cyan]{cluster['context']}[/cyan] {type_label}")
    else:
        console.print("[yellow]⚠[/yellow] No se encontraron Kubernetes Agents configurados")
        console.print("[dim]   Los agentes deben estar registrados en GitLab → Operate → Kubernetes clusters[/dim]")
        console.print("[dim]   Se usarán valores predeterminados basados en el template_repo[/dim]")
    
    # Configurar contexto por entorno
    console.print()
    for env in env_list:
        # Sugerencia basada en el env
        default_context = f"{template_repo}:cluster-{env}" if template_repo else f"cluster-{env}"
        
        # Si hay clusters disponibles, permitir selección directa
        if clusters:
            cluster_choice = Prompt.ask(
                f"Selecciona cluster para [cyan]{env}[/cyan] (1-{len(clusters)}) o Enter para escribir manualmente",
                choices=[str(i) for i in range(1, len(clusters) + 1)] + [""],
                default=""
            )
            
            if cluster_choice:
                kube_contexts[env] = clusters[int(cluster_choice) - 1]['context']
            else:
                kube_contexts[env] = Prompt.ask(
                    f"  KUBE_CONTEXT para {env}",
                    default=default_context
                )
        else:
            # No hay clusters, pedir directamente
            kube_contexts[env] = Prompt.ask(
                f"KUBE_CONTEXT [cyan]{env}[/cyan]",
                default=default_context
            )
    
    return kube_contexts


def _load_templates(config: Config, k8s_manifests_filter: dict) -> dict:
    """Carga plantillas desde GitLab"""
    console.print(f"\n[dim]Cargando plantillas filtradas...[/dim]")
    
    template_manager = TemplateManager(config.get('template_repo'))
    templates = template_manager.load_from_gitlab(
        config.get('gitlab_url'),
        config.get('gitlab_token'),
        config.get('template_repo'),
        k8s_manifests_filter=k8s_manifests_filter
    )
    
    if templates:
        console.print(f"[green]✓[/green] {len(templates)} plantilla(s) cargada(s)")
        logger.info(f"Plantillas cargadas: {len(templates)}")
    
    return templates


def _generate_and_create_files(client: GitLabClient, project: dict, templates: dict, variables: dict) -> int:
    """Genera y crea archivos en el repositorio"""
    console.print("\n[dim]Generando archivos...[/dim]")
    
    generator = K8sGenerator()
    
    # Separar templates de K8s y pipeline
    k8s_templates = {k: v for k, v in templates.items() if k.startswith('k8s/')}
    pipeline_templates = {k: v for k, v in templates.items() if not k.startswith('k8s/')}
    
    # Procesar pipeline templates (solo una vez)
    processed_files = generator.process_templates(pipeline_templates, variables, preserve_cicd_vars=True)
    
    # Procesar K8s templates por componente
    for component in variables['components']:
        # Variables específicas del componente
        component_vars = {
            **variables,
            'component': component
        }
        
        # Procesar templates K8s para este componente
        component_k8s = generator.process_templates(k8s_templates, component_vars, preserve_cicd_vars=True)
        
        # Reescribir rutas: k8s/01-namespace.yaml -> k8s/web/01-namespace.yaml
        for file_path, content in component_k8s.items():
            base_name = file_path.split('/')[-1]
            manifest_type = _extract_manifest_type(base_name)
            
            # Solo incluir si el manifest está seleccionado para este componente
            if manifest_type and manifest_type in variables['k8s_manifests'].get(component, []):
                new_path = f"k8s/{component}/{base_name}"
                processed_files[new_path] = content
    
    # Crear archivos en el repositorio
    for file_path, content in processed_files.items():
        # Sanitizar path por seguridad
        safe_path = sanitize_file_path(file_path)
        client.create_or_update_file(
            project['id'],
            safe_path,
            content,
            f"Add CI/CD: {safe_path}"
        )
    
    logger.info(f"Archivos generados: {len(processed_files)}")
    return len(processed_files)


def _extract_manifest_type(base_name: str) -> str:
    """Extrae el tipo de manifest del nombre de archivo"""
    manifest_mapping = {
        '01-namespace': 'namespace',
        '02-secrets': 'secrets',
        '03-configs': 'configs',
        '04-deployment': 'deployment',
        '05-ingress': 'ingress',
        '06-service': 'service',
        '07-pvc': 'pvc',
    }
    
    for pattern, manifest_type in manifest_mapping.items():
        if pattern in base_name:
            return manifest_type
    
    return None


@main.command()
@click.argument('project_path')
def status(project_path):
    """
    Muestra el estado del CI/CD de un proyecto
    
    PROJECT_PATH: Ruta del proyecto en GitLab (ej: grupo/proyecto)
    """
    config = Config()
    if not config.is_configured():
        console.print("[red]✗[/red] No se ha inicializado la configuración.")
        return
    
    try:
        client = GitLabClient(config.get('gitlab_url'), config.get('gitlab_token'))
        project = client.get_project(project_path)
        
        console.print(Panel.fit(
            f"[bold]Estado de CI/CD: {project['name']}[/bold]",
            border_style="blue"
        ))
        
        # Obtener último pipeline
        try:
            pipelines = client.get_pipelines(project['id'], per_page=1)
            if pipelines:
                pipeline = pipelines[0]
                status_color = {
                    'success': 'green',
                    'failed': 'red',
                    'running': 'yellow',
                    'pending': 'yellow'
                }.get(pipeline['status'], 'white')
                
                console.print(f"Último pipeline: [{status_color}]{pipeline['status']}[/{status_color}]")
                console.print(f"Rama: {pipeline['ref']}")
                console.print(f"URL: {pipeline['web_url']}")
            else:
                console.print("[yellow]No se encontraron pipelines[/yellow]")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] No se pudo acceder a los pipelines: {str(e)}")
        
        # Listar variables
        console.print("\n[bold]Variables CI/CD:[/bold]")
        try:
            variables = client.get_variables(project['id'])
            if variables:
                for var in variables:
                    console.print(f"  • {var['key']}")
            else:
                console.print("[dim]No hay variables configuradas[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] No se pudo acceder a las variables: {str(e)}")
            console.print("[dim]El token actual no tiene permisos para leer variables CI/CD[/dim]")
            
    except gitlab.exceptions.GitlabAuthenticationError:
        console.print("[red]✗[/red] Error de autenticación: Token de GitLab inválido o expirado")
        console.print("[yellow]💡[/yellow] Ejecuta [cyan]hidraulik init[/cyan] para reconfigurar")
    except gitlab.exceptions.GitlabGetError as e:
        if "404" in str(e):
            console.print(f"[red]✗[/red] Proyecto '{project_path}' no encontrado")
        else:
            console.print(f"[red]✗[/red] Error al acceder a GitLab: {str(e)}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")


@main.command()
@click.argument('project_path')
@click.argument('key')
@click.argument('value')
@click.option('--protected', is_flag=True, help='Marcar como variable protegida')
@click.option('--masked', is_flag=True, help='Marcar como variable enmascarada')
def set_variable(project_path, key, value, protected, masked):
    """
    Establece una variable CI/CD en un proyecto
    
    PROJECT_PATH: Ruta del proyecto en GitLab
    KEY: Nombre de la variable
    VALUE: Valor de la variable
    """
    config = Config()
    if not config.is_configured():
        console.print("[red]✗[/red] No se ha inicializado la configuración.")
        return
    
    try:
        client = GitLabClient(config.get('gitlab_url'), config.get('gitlab_token'))
        project = client.get_project(project_path)
        
        client.create_or_update_variable(
            project['id'],
            key,
            value,
            protected=protected,
            masked=masked
        )
        
        console.print(f"[green]✓[/green] Variable {key} configurada exitosamente")
        
    except gitlab.exceptions.GitlabAuthenticationError:
        console.print("[red]✗[/red] Error de autenticación: Token de GitLab inválido o expirado")
        console.print("[yellow]💡[/yellow] Ejecuta [cyan]hidraulik init[/cyan] para reconfigurar")
    except gitlab.exceptions.GitlabGetError as e:
        if "404" in str(e):
            console.print(f"[red]✗[/red] Proyecto '{project_path}' no encontrado")
        else:
            console.print(f"[red]✗[/red] Error al acceder a GitLab: {str(e)}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")


@main.command()
def list_templates():
    """
    Lista las plantillas disponibles en el repositorio central
    """
    config = Config()
    if not config.is_configured():
        console.print("[red]✗[/red] No se ha inicializado la configuración. Ejecuta 'hidraulik init' primero.")
        return
    
    try:
        console.print(Panel.fit(
            f"[bold]Plantillas en: {config.get('template_repo')}[/bold]",
            border_style="blue"
        ))
        
        template_manager = TemplateManager(config.get('template_repo'))
        templates = template_manager.load_from_gitlab(
            config.get('gitlab_url'),
            config.get('gitlab_token'),
            config.get('template_repo')
        )
        
        if not templates:
            console.print("[yellow]⚠[/yellow] No se encontraron plantillas en el repositorio")
            return
        
        console.print(f"\n[green]✓[/green] Se encontraron {len(templates)} plantillas:\n")
        
        for template_path in sorted(templates.keys()):
            console.print(f"  • {template_path}")
            
    except gitlab.exceptions.GitlabAuthenticationError:
        console.print("[red]✗[/red] Error de autenticación: Token de GitLab inválido o expirado")
        console.print("[yellow]💡[/yellow] Ejecuta [cyan]hidraulik init[/cyan] para reconfigurar")
    except gitlab.exceptions.GitlabGetError as e:
        if "404" in str(e):
            console.print(f"[red]✗[/red] Repositorio de plantillas '{config.get('template_repo')}' no encontrado")
            console.print("[yellow]💡[/yellow] Verifica la configuración con [cyan]hidraulik init[/cyan]")
        else:
            console.print(f"[red]✗[/red] Error al acceder a GitLab: {str(e)}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")


if __name__ == '__main__':
    main()
