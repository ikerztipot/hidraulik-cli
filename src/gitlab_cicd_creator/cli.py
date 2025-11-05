"""
CLI principal para GitLab CI/CD Creator
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .config import Config
from .gitlab_client import GitLabClient
from .template_manager import TemplateManager
from .k8s_generator import K8sGenerator

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
        client = GitLabClient(gitlab_url, token)
        user = client.get_current_user()
        console.print(f"[green]✓[/green] Conectado como: {user['username']}")
        
        # Verificar que el repositorio de plantillas existe
        console.print(f"\nVerificando repositorio de plantillas: {template_repo}")
        try:
            templates_project = client.get_project(template_repo)
            console.print(f"[green]✓[/green] Repositorio encontrado: {templates_project['name']}")
            
            # Verificar que hay archivos en el repositorio
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
@click.option('--k8s-cluster', help='Nombre del cluster de Kubernetes', required=True)
@click.option('--namespace', help='Namespace de Kubernetes', required=True)
@click.option('--environment', help='Ambiente (dev/staging/prod)', default='dev')
@click.option('--create-project', is_flag=True, help='Crear nuevo proyecto si no existe')
def create(project_path, k8s_cluster, namespace, environment, create_project):
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
            project = client.create_project_if_not_exists(project_path)
            console.print(f"[green]✓[/green] Proyecto listo: {project['web_url']}")
        else:
            project = client.get_project(project_path)
            console.print(f"[green]✓[/green] Proyecto encontrado: {project['name']}")
        
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
        
        # Recopilar información adicional para variables de plantilla
        console.print("\n[bold]Información requerida para las plantillas:[/bold]")
        
        variables = {
            'project_name': project['name'],
            'project_path': project_path,
            'k8s_cluster': k8s_cluster,
            'namespace': namespace,
            'environment': environment,
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
        
        # Crear variables CI/CD extraídas de las plantillas
        if cicd_variables:
            console.print("\n[bold]Configurando variables CI/CD en GitLab...[/bold]")
            
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
        
        # Listar variables
        console.print("\n[bold]Variables CI/CD:[/bold]")
        variables = client.get_variables(project['id'])
        for var in variables:
            console.print(f"  • {var['key']}")
            
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
