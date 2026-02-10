"""
CLI principal para GitLab CI/CD Creator
"""

import click
import gitlab
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from .config import Config
from .gitlab_client import GitLabClient
from .k8s_generator import K8sGenerator
from .template_manager import TemplateManager

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """
    GitLab CI/CD Creator - Genera automáticamente pipelines CI/CD para Kubernetes
    
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
        "[bold blue]Inicialización de GitLab CI/CD Creator[/bold blue]",
        border_style="blue"
    ))
    
    config = Config()
    
    # Solicitar configuración si no se proporcionó
    if not gitlab_url:
        gitlab_url = Prompt.ask(
            "URL de GitLab",
            default=config.get('gitlab_url', 'https://gitlab.com')
        )
    
    if not token:
        token = Prompt.ask("Token de acceso personal de GitLab", password=True)
    
    if not template_repo:
        template_repo = Prompt.ask(
            "Ruta del repositorio de plantillas (ej: grupo/plantillas-cicd)",
            default=config.get('template_repo', '')
        )
        
    # Validar que el repositorio de plantillas no esté vacío
    if not template_repo or template_repo.strip() == '':
        console.print("[red]✗[/red] El repositorio de plantillas es obligatorio")
        return
    
    # Verificar conexión y repositorio de plantillas
    try:
        console.print("\n[dim]Conectando con GitLab...[/dim]")
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
    console.print("\nYa puedes usar el CLI con: gitlab-cicd create <proyecto>")


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
    console.print(Panel.fit(
        f"[bold blue]Creando CI/CD para {project_path}[/bold blue]",
        border_style="blue"
    ))
    
    # Cargar configuración
    config = Config()
    if not config.is_configured():
        console.print("[red]✗[/red] No se ha inicializado la configuración. Ejecuta 'gitlab-cicd init' primero.")
        return
    
    try:
        # Conectar a GitLab
        client = GitLabClient(config.get('gitlab_url'), config.get('gitlab_token'))
        console.print("[green]✓[/green] Conectado a GitLab")
        
        # Obtener o crear proyecto
        if create_project:
            try:
                project = client.create_project_if_not_exists(project_path)
                console.print(f"[green]✓[/green] Proyecto listo: {project['web_url']}")
            except ValueError as e:
                console.print(f"[red]✗[/red] {str(e)}")
                console.print("[yellow]💡[/yellow] El grupo/namespace debe existir antes de crear el proyecto")
                console.print(f"[dim]  1. Crea el grupo en GitLab: {config.get('gitlab_url')}/admin/groups/new[/dim]")
                console.print(f"[dim]  2. O usa un grupo existente que tengas disponible[/dim]")
                return
        else:
            try:
                project = client.get_project(project_path)
                console.print(f"[green]✓[/green] Proyecto encontrado: {project['name']}")
            except Exception as e:
                if "404" in str(e):
                    console.print(f"[red]✗[/red] El proyecto '{project_path}' no existe")
                    console.print("[yellow]💡[/yellow] Usa --create-project para crearlo automáticamente:")
                    console.print(f"[dim]  gitlab-cicd create {project_path} --namespace {namespace} --create-project[/dim]")
                else:
                    console.print(f"[red]✗[/red] Error al acceder al proyecto: {str(e)}")
                return
        
        # Obtener clusters disponibles del proyecto de plantillas
        console.print("\n[bold]Obteniendo clusters disponibles...[/bold]")
        available_clusters = []
        try:
            # Los GitLab Agents están asociados a proyectos
            # Obtenemos los agents del proyecto de plantillas (clients/infrastructure)
            try:
                # Intentar obtener el proyecto de plantillas con manejo de errores de permisos
                try:
                    template_project = client._get_project_safe(config.get('template_repo'))
                except gitlab.exceptions.GitlabGetError:
                    # Si falla el acceso directo, intentar buscar por nombre
                    projects = client.gl.projects.list(search=config.get('template_repo').split('/')[-1], get_all=True)
                    template_project = None
                    for p in projects:
                        if p.path_with_namespace == config.get('template_repo'):
                            template_project = p
                            break
                    
                    if not template_project:
                        raise Exception(f"Proyecto de plantillas '{config.get('template_repo')}' no encontrado.")
                
                # Obtener GitLab Agents del proyecto
                agents = template_project.cluster_agents.list(get_all=True)
                
                for agent in agents:
                    agent_name = agent.name
                    cluster_context = f"{config.get('template_repo')}:{agent_name}"
                    available_clusters.append(cluster_context)
                    console.print(f"  [green]✓[/green] {cluster_context}")
                    
            except Exception as cluster_err:
                console.print(f"[yellow]⚠[/yellow] No se pudieron obtener clusters: {str(cluster_err)}")
                    
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Error al buscar clusters: {str(e)}")
        
        if not available_clusters:
            console.print("[yellow]⚠[/yellow] No se encontraron clusters configurados")
            console.print("[dim]Ingresa el KUBE_CONTEXT manualmente para cada entorno[/dim]")
        
        # Cargar plantillas desde el repositorio central
        console.print(f"\nCargando plantillas desde: {config.get('template_repo')}")
        template_manager = TemplateManager(config.get('template_repo'))
        templates = template_manager.load_from_gitlab(
            config.get('gitlab_url'),
            config.get('gitlab_token'),
            config.get('template_repo')
        )
        
        if not templates:
            console.print("[red]✗[/red] No se pudieron cargar las plantillas del repositorio")
            return
            
        console.print(f"[green]✓[/green] Plantillas cargadas: {len(templates)} archivos")
        
        # Extraer y clasificar variables
        console.print("\n[bold]Analizando variables de las plantillas...[/bold]")
        template_vars, cicd_vars = template_manager.extract_variables(templates)
        
        if template_vars:
            console.print(f"  • Variables de plantilla: {', '.join(template_vars)}")
        if cicd_vars:
            console.print(f"  • Variables CI/CD (se guardarán en GitLab): {', '.join(cicd_vars)}")
        
        # Configurar KUBE_CONTEXT por entorno
        env_list = [e.strip() for e in environments.split(',')]
        kube_contexts = {}
        
        console.print("\n[bold]Configuración de KUBE_CONTEXT por entorno:[/bold]")
        for env in env_list:
            console.print(f"\n[cyan]Entorno: {env}[/cyan]")
            
            if available_clusters:
                console.print("Clusters disponibles:")
                for idx, cluster in enumerate(available_clusters, 1):
                    console.print(f"  {idx}. {cluster}")
                
                cluster_choice = Prompt.ask(
                    f"Selecciona el cluster para {env} (número o ingresa manualmente)",
                    default="1"
                )
                
                try:
                    cluster_idx = int(cluster_choice) - 1
                    if 0 <= cluster_idx < len(available_clusters):
                        kube_contexts[env] = available_clusters[cluster_idx]
                    else:
                        kube_contexts[env] = Prompt.ask(f"KUBE_CONTEXT para {env}")
                except ValueError:
                    kube_contexts[env] = cluster_choice
            else:
                kube_contexts[env] = Prompt.ask(
                    f"KUBE_CONTEXT para {env}",
                    default=f"{config.get('template_repo')}:cluster-{env}"
                )
        
        # Recopilar información adicional para variables de plantilla
        console.print("\n[bold]Información requerida para las plantillas:[/bold]")
        
        variables = {
            'project_name': project['name'],
            'project_path': project_path,
            'namespace': namespace,
            'environments': env_list,
            'template_repo': config.get('template_repo'),
        }
        
        # Solicitar valores para variables de plantilla adicionales
        for var in template_vars:
            if var not in variables:
                default_value = ""
                if var == 'docker_registry':
                    default_value = "registry.gitlab.com"
                elif var == 'docker_image':
                    default_value = project_path
                    
                value = Prompt.ask(
                    f"{var}",
                    default=default_value if default_value else None
                )
                variables[var] = value
        
        # Solicitar valores para variables CI/CD
        cicd_variables = {}
        if cicd_vars:
            console.print("\n[bold]Valores para variables CI/CD:[/bold]")
            console.print("[dim]Estas variables se guardarán en la configuración de GitLab[/dim]")
            
            for var in cicd_vars:
                # Preguntar si la variable debe ser protegida/enmascarada
                value = Prompt.ask(f"{var}")
                
                is_protected = Confirm.ask(f"  ¿Marcar {var} como protegida?", default=False)
                is_masked = Confirm.ask(f"  ¿Marcar {var} como enmascarada?", default=True)
                
                cicd_variables[var] = {
                    'value': value,
                    'protected': is_protected,
                    'masked': is_masked
                }
        
        # Generar configuración K8s
        generator = K8sGenerator()
        generator.set_cicd_vars(cicd_vars)
        
        # Procesar plantillas (sin sustituir variables CI/CD)
        console.print("\n[bold]Generando archivos CI/CD...[/bold]")
        processed_files = generator.process_templates(templates, variables, preserve_cicd_vars=True)
        console.print(f"[green]✓[/green] {len(processed_files)} archivos procesados")
        
        # Crear archivos en el repositorio
        for file_path, content in processed_files.items():
            client.create_or_update_file(
                project['id'],
                file_path,
                content,
                f"Add CI/CD configuration: {file_path}"
            )
            console.print(f"  [green]✓[/green] {file_path}")
        
        # Crear variables KUBE_CONTEXT por entorno
        console.print("\n[bold]Configurando variables KUBE_CONTEXT en GitLab...[/bold]")
        for env, kube_context in kube_contexts.items():
            client.create_or_update_variable(
                project['id'],
                'KUBE_CONTEXT',
                kube_context,
                protected=False,
                masked=False,
                environment_scope=env
            )
            console.print(f"  [green]✓[/green] KUBE_CONTEXT={kube_context} (scope: {env})")
        
        # Crear variables CI/CD extraídas de las plantillas
        if cicd_variables:
            console.print("\n[bold]Configurando variables CI/CD adicionales en GitLab...[/bold]")
            
            for key, var_config in cicd_variables.items():
                client.create_or_update_variable(
                    project['id'],
                    key,
                    var_config['value'],
                    protected=var_config['protected'],
                    masked=var_config['masked']
                )
                flags = []
                if var_config['protected']:
                    flags.append('protegida')
                if var_config['masked']:
                    flags.append('enmascarada')
                flag_str = f" ({', '.join(flags)})" if flags else ""
                console.print(f"  [green]✓[/green] {key}{flag_str}")
        else:
            console.print("\n[dim]No se definieron variables CI/CD adicionales[/dim]")
        
        console.print(f"\n[bold green]✓ CI/CD configurado exitosamente![/bold green]")
        console.print(f"\nPuedes ver el pipeline en: {project['web_url']}/-/pipelines")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")
        raise


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
        
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")


@main.command()
def list_templates():
    """
    Lista las plantillas disponibles en el repositorio central
    """
    config = Config()
    if not config.is_configured():
        console.print("[red]✗[/red] No se ha inicializado la configuración. Ejecuta 'gitlab-cicd init' primero.")
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
            
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")


if __name__ == '__main__':
    main()
