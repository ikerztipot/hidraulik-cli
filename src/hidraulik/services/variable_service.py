"""
Servicio para gestionar variables de entorno y secrets
"""

from typing import Dict, List, Tuple
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ..validators import validate_variable_name
from ..exceptions import ValidationError


class VariableService:
    """Servicio para gestionar variables de entorno y secrets"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def collect_component_variables(
        self,
        component: str
    ) -> Tuple[List[str], List[str]]:
        """
        Recopila variables para un componente interactivamente
        
        Args:
            component: Nombre del componente
        
        Returns:
            Tupla de (config_vars, secret_vars)
        """
        self.console.print(f"\n[bold cyan]{component}[/bold cyan]")
        self.console.print(
            "[dim]Introduce las variables (una por una, vacío para terminar)[/dim]"
        )
        
        config_vars = []
        secret_vars = []
        
        while True:
            var_name = Prompt.ask("Nombre de variable", default="")
            
            if not var_name.strip():
                break
            
            # Validar nombre
            try:
                validate_variable_name(var_name)
            except ValidationError as e:
                self.console.print(f"[red]✗[/red] {e.message}")
                self.console.print(f"[dim]{e.reason}[/dim]")
                continue
            
            is_secret = Confirm.ask(
                f"¿'{var_name}' es un secret?",
                default=False
            )
            
            if is_secret:
                secret_vars.append(var_name)
                self.console.print(f"  [red]🔒[/red] {var_name} → Secret")
            else:
                config_vars.append(var_name)
                self.console.print(f"  [green]✓[/green] {var_name} → ConfigMap")
        
        total = len(config_vars) + len(secret_vars)
        if total > 0:
            self.console.print(f"[green]✓[/green] {total} variable(s) configurada(s)")
        else:
            self.console.print("[dim]Sin variables[/dim]")
        
        return config_vars, secret_vars
    
    def create_gitlab_variables(
        self,
        client,
        project_id: str,
        config_vars: Dict[str, List[str]],
        secret_vars: Dict[str, List[str]],
        kube_contexts: Dict[str, str]
    ) -> int:
        """
        Crea variables en GitLab
        
        Args:
            client: Cliente de GitLab
            project_id: ID del proyecto
            config_vars: Variables de configuración por componente
            secret_vars: Variables secretas por componente
            kube_contexts: Contextos de Kubernetes por entorno
        
        Returns:
            Número de variables creadas
        """
        count = 0
        
        # KUBE_CONTEXT por entorno
        for env, kube_context in kube_contexts.items():
            client.create_or_update_variable(
                project_id,
                'KUBE_CONTEXT',
                kube_context,
                protected=False,
                masked=False,
                environment_scope=env
            )
            count += 1
        
        # Variables de ConfigMap (no protegidas, no enmascaradas)
        for component, vars_list in config_vars.items():
            for var_name in vars_list:
                client.create_or_update_variable(
                    project_id,
                    var_name,
                    'CHANGE_ME',
                    protected=False,
                    masked=False,
                    environment_scope='*',
                    raw=True
                )
                count += 1
        
        # Variables de Secrets (enmascaradas)
        for component, vars_list in secret_vars.items():
            for var_name in vars_list:
                client.create_or_update_variable(
                    project_id,
                    var_name,
                    'CHANGE_ME',
                    protected=False,
                    masked=True,
                    environment_scope='*',
                    raw=True
                )
                count += 1
        
        return count
    
    def display_pending_configuration(
        self,
        config_vars: Dict[str, List[str]],
        secret_vars: Dict[str, List[str]],
        project_web_url: str
    ) -> None:
        """
        Muestra información sobre variables que necesitan configuración
        
        Args:
            config_vars: Variables de configuración
            secret_vars: Variables secretas
            project_web_url: URL web del proyecto
        """
        total_vars = (
            sum(len(v) for v in config_vars.values()) +
            sum(len(v) for v in secret_vars.values())
        )
        
        if total_vars == 0:
            return
        
        self.console.print(
            f"\n[yellow]⚠[/yellow] {total_vars} variable(s) creada(s) con valor placeholder:"
        )
        
        for component, vars_list in config_vars.items():
            for var_name in vars_list:
                self.console.print(f"  • {var_name} (ConfigMap)")
        
        for component, vars_list in secret_vars.items():
            for var_name in vars_list:
                self.console.print(f"  • {var_name} (Secret)")
        
        self.console.print(
            f"\n[dim]Configúralas en:[/dim] {project_web_url}/-/settings/ci_cd"
        )
