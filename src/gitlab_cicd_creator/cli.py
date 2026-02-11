"""
CLI principal para GitLab CI/CD Creator
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

console = Console()


def get_available_runners(client: GitLabClient, project_path: str = None) -> list:
    """
    Obtiene todos los runners disponibles en GitLab con sus tags
    """
    all_runners = []
    seen_ids = set()
    
    # Buscar en instancia, grupo y proyecto sin mensajes verbosos
    try:
        instance_runners = client.get_available_runners(scope='active')
        if instance_runners:
            for runner in instance_runners:
                if runner['id'] not in seen_ids and runner.get('tags'):
                    all_runners.append(runner)
                    seen_ids.add(runner['id'])
    except:
        pass
    
    if project_path:
        parts = project_path.split('/')[:-1]
        if parts:
            try:
                group_runners = client.get_group_runners(parts[0])
                if group_runners:
                    for runner in group_runners:
                        if runner['id'] not in seen_ids and runner.get('tags'):
                            all_runners.append(runner)
                            seen_ids.add(runner['id'])
            except:
                pass
        
        try:
            project_runners = client.get_project_runners(project_path)
            if project_runners:
                for runner in project_runners:
                    if runner['id'] not in seen_ids and runner.get('tags'):
                        all_runners.append(runner)
                        seen_ids.add(runner['id'])
        except:
            pass
    
    return all_runners


def select_runner_interactive(available_runners: list, default_tags: list = None) -> list:
    """
    Permite seleccionar un runner y retorna sus tags
    """
    if not available_runners:
        console.print("\n[yellow]⚠[/yellow] No se encontraron runners, ingresa los tags manualmente")
        tags_input = Prompt.ask(
            "Tags del runner (separados por coma)",
            default=','.join(default_tags) if default_tags else "docker"
        )
        return [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    
    # Mostrar runners de forma compacta
    console.print("")
    for idx, runner in enumerate(available_runners, 1):
        tags_str = ', '.join(runner.get('tags', []))
        status = "●" if runner.get('online') else "○"
        desc = runner.get('description', f"Runner #{runner['id']}")[:40]
        console.print(f"  {idx}. {status} {desc}")
        console.print(f"     [dim]{tags_str}[/dim]")
    
    # Determinar default
    default_idx = "1"
    if default_tags:
        for idx, runner in enumerate(available_runners, 1):
            runner_tags = set(runner.get('tags', []))
            if default_tags and set(default_tags).issubset(runner_tags):
                default_idx = str(idx)
                break
    
    selection = Prompt.ask(
        "\nRunner a usar",
        default=default_idx
    )
    
    try:
        idx = int(selection) - 1
        if 0 <= idx < len(available_runners):
            selected_runner = available_runners[idx]
            tags = selected_runner.get('tags', [])
            return tags
    except ValueError:
        pass
    
    # Fallback manual
    tags_input = Prompt.ask(
        "Tags del runner (separados por coma)",
        default=','.join(default_tags) if default_tags else "docker"
    )
    return [tag.strip() for tag in tags_input.split(',') if tag.strip()]


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
    console.print(f"\n[bold blue]→[/bold blue] Configurando CI/CD: [bold]{project_path}[/bold]\n")
    
    # Cargar configuración
    config = Config()
    if not config.is_configured():
        console.print("[red]✗[/red] Ejecuta primero: [cyan]gitlab-cicd init[/cyan]")
        return
    
    try:
        # Conectar a GitLab
        try:
            client = GitLabClient(config.get('gitlab_url'), config.get('gitlab_token'))
            console.print("[dim]Conectado a GitLab[/dim]")
        except Exception as auth_error:
            error_msg = str(auth_error).lower()
            if '401' in error_msg or 'invalid_token' in error_msg or 'unauthorized' in error_msg:
                console.print("[red]✗[/red] Token inválido o expirado")
                console.print("[dim]Ejecuta:[/dim] [cyan]gitlab-cicd init[/cyan]")
                return
            else:
                raise
        
        # Obtener o crear proyecto
        if create_project:
            try:
                project = client.create_project_if_not_exists(project_path)
                console.print(f"[green]✓[/green] Proyecto: {project['name']}")
            except ValueError as e:
                console.print(f"[red]✗[/red] El grupo debe existir primero")
                return
        else:
            try:
                project = client.get_project(project_path)
                console.print(f"[green]✓[/green] Proyecto: {project['name']}")
            except Exception as e:
                if "404" in str(e):
                    console.print(f"[red]✗[/red] Proyecto no existe. Usa: [cyan]--create-project[/cyan]")
                else:
                    console.print(f"[red]✗[/red] {str(e)}")
                return
        
        # Obtener clusters disponibles (GitLab Agents) - silenciosamente
        available_clusters = []
        groups_checked = set()
        
        def get_agents_from_group(group_path):
            try:
                encoded_path = quote(group_path, safe='')
                group = client.gl.groups.get(encoded_path)
                try:
                    projects = group.projects.list(get_all=True)
                    for proj in projects:
                        try:
                            full_proj = client.gl.projects.get(proj.id)
                            agents = full_proj.cluster_agents.list(get_all=True)
                            if agents:
                                for agent in agents:
                                    cluster_context = f"{proj.path_with_namespace}:{agent.name}"
                                    if cluster_context not in available_clusters:
                                        available_clusters.append(cluster_context)
                        except:
                            pass
                except:
                    pass
            except:
                pass
        
        # Buscar en grupos relevantes
        if config.get('template_repo'):
            template_parts = config.get('template_repo').split('/')
            for i in range(1, len(template_parts)):
                group_path = '/'.join(template_parts[:i])
                if group_path not in groups_checked:
                    groups_checked.add(group_path)
                    get_agents_from_group(group_path)
        
        project_parts = project_path.split('/')[:-1]
        for i in range(1, len(project_parts) + 1):
            group_path = '/'.join(project_parts[:i])
            if group_path not in groups_checked:
                groups_checked.add(group_path)
                get_agents_from_group(group_path)
        
        if available_clusters:
            console.print(f"[green]✓[/green] {len(available_clusters)} cluster(s) disponible(s)")
        
        # Cargar plantillas
        console.print(f"[green]✓[/green] Plantillas: {config.get('template_repo')}")
        template_manager = TemplateManager(config.get('template_repo'))
        templates = template_manager.load_from_gitlab(
            config.get('gitlab_url'),
            config.get('gitlab_token'),
            config.get('template_repo')
        )
        
        if not templates:
            console.print("[red]✗[/red] No se encontraron plantillas")
            return
        
        # Analizar variables silenciosamente
        template_vars, cicd_vars = template_manager.extract_variables(templates)
        include_vars = template_manager.extract_variables_from_includes(
            templates,
            config.get('gitlab_url'),
            config.get('gitlab_token')
        )
        
        # Obtener runners disponibles
        available_runners = get_available_runners(client, project_path)
        if available_runners:
            console.print(f"[green]✓[/green] {len(available_runners)} runner(s) disponible(s)")
        
        # Configuración del pipeline
        console.print("\n[bold]Configuración:[/bold]")
        
        # Componentes
        project_name = project_path.split('/')[-1]
        components_input = Prompt.ask(
            "Componentes (separados por coma)",
            default="web"
        )
        components = [c.strip() for c in components_input.split(',') if c.strip()]
        
        # Docker
        use_docker = Confirm.ask("¿Usa Docker?", default=True)
        
        dockerfile_paths = {}
        if use_docker:
            for component in components:
                default_path = "Dockerfile" if len(components) == 1 else f"{component}/Dockerfile"
                dockerfile_path = Prompt.ask(
                    f"Dockerfile de '{component}'",
                    default=default_path
                )
                dockerfile_paths[component] = dockerfile_path
        
        # Runner
        console.print("\n[bold]Selecciona el runner:[/bold]")
        default_runner_tags = ['buildkit', 'scaleway', 'worko-internal']
        runner_tags = select_runner_interactive(available_runners, default_runner_tags)
        
        # Prefijo
        suggested_prefix = project_name.split('-')[0] if '-' in project_name else project_name[:4]
        tag_prefix = Prompt.ask(
            "Prefijo para tags de release",
            default=suggested_prefix
        )
        
        # Configurar clusters por entorno
        env_list = [e.strip() for e in environments.split(',')]
        kube_contexts = {}
        
        console.print("\n[bold]Clusters por entorno:[/bold]")
        if available_clusters:
            for idx, cluster in enumerate(available_clusters, 1):
                console.print(f"  {idx}. {cluster}")
        
        for env in env_list:
            if available_clusters:
                cluster_choice = Prompt.ask(
                    f"Cluster para [cyan]{env}[/cyan]",
                    default="1"
                )
                try:
                    cluster_idx = int(cluster_choice) - 1
                    if 0 <= cluster_idx < len(available_clusters):
                        kube_contexts[env] = available_clusters[cluster_idx]
                    else:
                        kube_contexts[env] = cluster_choice
                except ValueError:
                    kube_contexts[env] = cluster_choice
            else:
                kube_contexts[env] = Prompt.ask(
                    f"KUBE_CONTEXT [cyan]{env}[/cyan]",
                    default=f"{config.get('template_repo')}:cluster-{env}"
                )
        
        # Variables del template
        variables = {
            'project_name': project['name'],
            'project_path': project_path,
            'namespace': namespace,
            'environments': env_list,
            'template_repo': config.get('template_repo'),
            'components': components,
            'runner_tags': runner_tags,
            'tag_prefix': tag_prefix,
            'use_docker': use_docker,
            'dockerfile_paths': dockerfile_paths,
        }
        
        # Variables adicionales de plantilla
        if template_vars:
            console.print("\n[bold]Variables de plantilla:[/bold]")
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
        
        # Variables CI/CD
        cicd_variables = {}
        if cicd_vars:
            console.print("\n[bold]Variables CI/CD:[/bold]")
            for var in cicd_vars:
                value = Prompt.ask(f"{var}")
                is_protected = Confirm.ask(f"  Protegida?", default=False)
                is_masked = Confirm.ask(f"  Enmascarada?", default=True)
                
                cicd_variables[var] = {
                    'value': value,
                    'protected': is_protected,
                    'masked': is_masked
                }
        
        # Generar archivos
        console.print("\n[dim]Generando archivos...[/dim]")
        generator = K8sGenerator()
        generator.set_cicd_vars(cicd_vars)
        processed_files = generator.process_templates(templates, variables, preserve_cicd_vars=True)
        
        # Crear archivos en el repositorio
        for file_path, content in processed_files.items():
            client.create_or_update_file(
                project['id'],
                file_path,
                content,
                f"Add CI/CD: {file_path}"
            )
        console.print(f"[green]✓[/green] {len(processed_files)} archivo(s) creado(s)")
        
        # Configurar variables
        console.print("[dim]Configurando variables...[/dim]")
        for env, kube_context in kube_contexts.items():
            client.create_or_update_variable(
                project['id'],
                'KUBE_CONTEXT',
                kube_context,
                protected=False,
                masked=False,
                environment_scope=env
            )
        
        if cicd_variables:
            for key, var_config in cicd_variables.items():
                client.create_or_update_variable(
                    project['id'],
                    key,
                    var_config['value'],
                    protected=var_config['protected'],
                    masked=var_config['masked']
                )
        console.print(f"[green]✓[/green] Variables configuradas")
        
        console.print(f"\n[bold green]✓ CI/CD configurado![/bold green]")
        console.print(f"[dim]Ver pipeline:[/dim] {project['web_url']}/-/pipelines")
        
    except gitlab.exceptions.GitlabAuthenticationError as e:
        console.print("[red]✗[/red] Error de autenticación: Token de GitLab inválido o expirado")
        console.print("\n[yellow]💡 Solución:[/yellow]")
        console.print("  1. Genera un nuevo token en GitLab:")
        console.print(f"     [cyan]{config.get('gitlab_url')}/-/user_settings/personal_access_tokens[/cyan]")
        console.print("  2. Permisos requeridos: [bold]api[/bold], [bold]read_repository[/bold], [bold]write_repository[/bold]")
        console.print("  3. Reinicializa la configuración:")
        console.print("     [cyan]gitlab-cicd init[/cyan]")
    except gitlab.exceptions.GitlabGetError as e:
        if "404" in str(e):
            console.print(f"[red]✗[/red] No se encontró el recurso solicitado")
            console.print("[yellow]💡[/yellow] Verifica que el proyecto/grupo existe y tienes acceso")
        else:
            console.print(f"[red]✗[/red] Error al acceder a GitLab: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        console.print(f"[red]✗[/red] Error: {error_msg}")
        if '--debug' in click.get_current_context().args:
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
            
    except gitlab.exceptions.GitlabAuthenticationError:
        console.print("[red]✗[/red] Error de autenticación: Token de GitLab inválido o expirado")
        console.print("[yellow]💡[/yellow] Ejecuta [cyan]gitlab-cicd init[/cyan] para reconfigurar")
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
        console.print("[yellow]💡[/yellow] Ejecuta [cyan]gitlab-cicd init[/cyan] para reconfigurar")
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
            
    except gitlab.exceptions.GitlabAuthenticationError:
        console.print("[red]✗[/red] Error de autenticación: Token de GitLab inválido o expirado")
        console.print("[yellow]💡[/yellow] Ejecuta [cyan]gitlab-cicd init[/cyan] para reconfigurar")
    except gitlab.exceptions.GitlabGetError as e:
        if "404" in str(e):
            console.print(f"[red]✗[/red] Repositorio de plantillas '{config.get('template_repo')}' no encontrado")
            console.print("[yellow]💡[/yellow] Verifica la configuración con [cyan]gitlab-cicd init[/cyan]")
        else:
            console.print(f"[red]✗[/red] Error al acceder a GitLab: {str(e)}")
    except Exception as e:
        console.print(f"[red]✗[/red] Error: {str(e)}")


if __name__ == '__main__':
    main()
