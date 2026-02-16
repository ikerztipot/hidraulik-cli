"""
Servicio para configurar deployments de Kubernetes
"""

from typing import Dict, List, Tuple
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ..validators import validate_storage_size, validate_port
from ..exceptions import ValidationError


class K8sConfigService:
    """Servicio para configurar deployments de Kubernetes"""
    
    RESOURCE_PROFILES = {
        'xsmall': {
            'cpu_request': '100m',
            'cpu_limit': '500m',
            'memory_request': '64Mi',
            'memory_limit': '256Mi',
        },
        'small': {
            'cpu_request': '250m',
            'cpu_limit': '500m',
            'memory_request': '256Mi',
            'memory_limit': '512Mi',
        },
        'medium': {
            'cpu_request': '500m',
            'cpu_limit': '1000m',
            'memory_request': '512Mi',
            'memory_limit': '1Gi',
        },
        'large': {
            'cpu_request': '1000m',
            'cpu_limit': '2000m',
            'memory_request': '1Gi',
            'memory_limit': '2Gi',
        },
        'xlarge': {
            'cpu_request': '2000m',
            'cpu_limit': '4000m',
            'memory_request': '2Gi',
            'memory_limit': '4Gi',
        },
    }
    
    MANIFEST_TYPES = [
        'namespace',
        'secrets',
        'configs',
        'deployment',
        'ingress',
        'service',
        'pvc',
    ]
    
    def __init__(self, console: Console):
        self.console = console
    
    def configure_component_deployment(
        self,
        component: str,
        has_config_vars: bool = False,
        has_secret_vars: bool = False,
        namespace_provided: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Configura deployment de K8s para un componente
        
        Args:
            component: Nombre del componente
            has_config_vars: Si tiene variables de configuración
            has_secret_vars: Si tiene variables secretas
            namespace_provided: Si se especificó --namespace explícitamente
        
        Returns:
            Tupla de (deploy_to_k8s, manifests_list)
        """
        deploy_to_k8s = Confirm.ask(
            f"¿'{component}' se despliega en Kubernetes?",
            default=True
        )
        
        if not deploy_to_k8s:
            return False, []
        
        self.console.print(f"  Manifiestos para '{component}':")
        manifests = []
        
        # Namespace (auto-activar si fue especificado en --namespace)
        if namespace_provided:
            manifests.append('namespace')
            self.console.print(
                "    - Namespace [dim](activado automáticamente)[/dim]"
            )
        elif Confirm.ask("    - Namespace", default=True):
            manifests.append('namespace')
        
        # Secrets (auto-activar si hay secret_vars)
        if has_secret_vars:
            manifests.append('secrets')
            self.console.print(
                "    - Secrets [dim](activado automáticamente)[/dim]"
            )
        elif Confirm.ask("    - Secrets", default=True):
            manifests.append('secrets')
        
        # ConfigMaps (auto-activar si hay config_vars)
        if has_config_vars:
            manifests.append('configs')
            self.console.print(
                "    - ConfigMaps [dim](activado automáticamente)[/dim]"
            )
        elif Confirm.ask("    - ConfigMaps", default=True):
            manifests.append('configs')
        
        # Resto de manifiestos
        if Confirm.ask("    - Deployment", default=True):
            manifests.append('deployment')
        if Confirm.ask("    - Ingress", default=True):
            manifests.append('ingress')
        if Confirm.ask("    - Service", default=True):
            manifests.append('service')
        if Confirm.ask("    - PVC (PersistentVolumeClaim)", default=False):
            manifests.append('pvc')
        
        self.console.print(f"  [green]✓[/green] {', '.join(manifests)}")
        return True, manifests
    
    def select_resource_profile(self, component: str) -> str:
        """
        Permite seleccionar perfil de recursos interactivamente
        
        Args:
            component: Nombre del componente
        
        Returns:
            Nombre del perfil seleccionado
        """
        # Mostrar perfiles disponibles justo antes de preguntar
        self.console.print("\n[dim]Perfiles disponibles:[/dim]")
        for profile_name, resources in self.RESOURCE_PROFILES.items():
            self.console.print(
                f"  [cyan]{profile_name:8}[/cyan]: "
                f"CPU {resources['cpu_request']}-{resources['cpu_limit']}, "
                f"RAM {resources['memory_request']}-{resources['memory_limit']}"
            )
        
        profile = Prompt.ask(
            f"Perfil de recursos para '{component}'",
            choices=list(self.RESOURCE_PROFILES.keys()),
            default="medium"
        )
        
        self.console.print(f"  [green]✓[/green] {component}: {profile}")
        return profile
    
    def display_resource_profiles(self) -> None:
        """Muestra la tabla de perfiles de recursos disponibles"""
        self.console.print("\n[bold]Perfiles de recursos disponibles:[/bold]")
        for profile_name, resources in self.RESOURCE_PROFILES.items():
            self.console.print(
                f"  [cyan]{profile_name:8}[/cyan]: "
                f"CPU {resources['cpu_request']}-{resources['cpu_limit']}, "
                f"RAM {resources['memory_request']}-{resources['memory_limit']}"
            )
    
    def configure_pvc_volumes(self, component: str) -> List[Dict[str, str]]:
        """
        Configura volúmenes PVC para un componente
        
        Args:
            component: Nombre del componente
        
        Returns:
            Lista de configuraciones de volúmenes
        """
        self.console.print(
            f"\n[bold]Configuración de PVC para '{component}':[/bold]"
        )
        self.console.print("[dim]Puedes definir múltiples volúmenes[/dim]")
        
        volumes_list = []
        
        while True:
            default_name = "uploads" if not volumes_list else ""
            volume_name = Prompt.ask(
                "Nombre del volumen (vacío para terminar)",
                default=default_name
            )
            
            if not volume_name.strip():
                break
            
            mount_path = Prompt.ask(
                f"Ruta de montaje para '{volume_name}'",
                default="/opt/app/public/uploads"
            )
            
            # Validar storage size con reintentos
            while True:
                storage = Prompt.ask(
                    f"Tamaño de storage (ej: 5Gi, 10Gi)",
                    default="5Gi"
                )
                
                try:
                    validate_storage_size(storage)
                    break
                except ValidationError as e:
                    self.console.print(f"[red]✗[/red] {e.message}")
                    self.console.print(f"[dim]{e.reason}[/dim]")
            
            volumes_list.append({
                'name': volume_name,
                'mount_path': mount_path,
                'storage': storage
            })
            
            self.console.print(
                f"  [green]✓[/green] {volume_name} → {mount_path} ({storage})"
            )
        
        if volumes_list:
            self.console.print(
                f"  [green]✓[/green] {len(volumes_list)} volumen(es) configurado(s)"
            )
        else:
            self.console.print("  [dim]Sin volúmenes[/dim]")
        
        return volumes_list
    
    def configure_container_port(
        self,
        component: str,
        default_port: str = "80"
    ) -> str:
        """
        Configura el puerto del contenedor con validación
        
        Args:
            component: Nombre del componente
            default_port: Puerto por defecto
        
        Returns:
            Puerto validado como string
        """
        while True:
            port = Prompt.ask(
                f"Puerto expuesto por '{component}'",
                default=default_port
            )
            
            try:
                validate_port(port)
                return port
            except ValidationError as e:
                self.console.print(f"[red]✗[/red] {e.message}")
                self.console.print(f"[dim]{e.reason}[/dim]")
