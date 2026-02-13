"""
Servicio para gestionar runners de GitLab
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt

from ..validators import validate_runner_tags
from ..exceptions import ValidationError


RunnerDict = Dict[str, Any]


class RunnerService:
    """Servicio para gestionar runners de GitLab"""
    
    def __init__(self, client, console: Console):
        self.client = client
        self.console = console
    
    def discover_available_runners(
        self,
        project_path: Optional[str] = None,
        template_repo: Optional[str] = None
    ) -> List[RunnerDict]:
        """
        Descubre runners disponibles en instancia, grupos y proyecto
        
        Args:
            project_path: Ruta del proyecto
            template_repo: Ruta del repositorio de plantillas
        
        Returns:
            Lista de runners únicos con tags
        """
        all_runners = []
        seen_ids = set()
        
        # Buscar en instancia
        self._fetch_and_add_runners(
            lambda: self.client.get_available_runners('active'),
            all_runners,
            seen_ids
        )
        
        # Buscar en grupos del template_repo
        if template_repo:
            parts = template_repo.split('/')
            for i in range(1, len(parts)):
                group_path = '/'.join(parts[:i])
                self._fetch_and_add_runners(
                    lambda gp=group_path: self.client.get_group_runners(gp),
                    all_runners,
                    seen_ids
                )
        
        # Buscar en grupos del proyecto
        if project_path:
            parts = project_path.split('/')[:-1]
            for i in range(1, len(parts) + 1):
                group_path = '/'.join(parts[:i])
                self._fetch_and_add_runners(
                    lambda gp=group_path: self.client.get_group_runners(gp),
                    all_runners,
                    seen_ids
                )
            
            # Buscar en proyecto específico
            self._fetch_and_add_runners(
                lambda: self.client.get_project_runners(project_path),
                all_runners,
                seen_ids
            )
        
        return all_runners
    
    def _fetch_and_add_runners(
        self,
        fetcher,
        all_runners: List[RunnerDict],
        seen_ids: set
    ) -> None:
        """
        Obtiene runners de una fuente y los añade a la lista si son únicos
        
        Args:
            fetcher: Función que obtiene runners
            all_runners: Lista donde añadir runners
            seen_ids: Set de IDs ya vistos
        """
        try:
            runners = fetcher()
            for runner in runners:
                if runner['id'] not in seen_ids and runner.get('tags'):
                    all_runners.append(runner)
                    seen_ids.add(runner['id'])
        except Exception:
            # Silenciar errores de permisos
            pass
    
    def select_runner_interactive(
        self,
        available_runners: List[RunnerDict],
        default_tags: Optional[List[str]] = None
    ) -> List[str]:
        """
        Permite al usuario seleccionar un runner interactivamente
        
        Args:
            available_runners: Lista de runners disponibles
            default_tags: Tags por defecto sugeridos
        
        Returns:
            Lista de tags del runner seleccionado
        """
        if not available_runners:
            self.console.print(
                "\n[yellow]⚠[/yellow] No se encontraron runners, "
                "ingresa los tags manualmente"
            )
            return self._prompt_manual_tags(default_tags)
        
        # Mostrar runners compactamente
        self._display_runners(available_runners)
        
        # Determinar default
        default_idx = self._find_default_runner_index(
            available_runners,
            default_tags
        )
        
        selection = Prompt.ask(
            "\nRunner a usar",
            default=str(default_idx + 1)
        )
        
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(available_runners):
                tags = available_runners[idx].get('tags', [])
                # Validar tags antes de retornar
                try:
                    validate_runner_tags(tags)
                    return tags
                except ValidationError as e:
                    self.console.print(f"[yellow]⚠[/yellow] {e.message}")
                    return self._prompt_manual_tags(default_tags)
        except ValueError:
            pass
        
        # Fallback a entrada manual
        return self._prompt_manual_tags(default_tags)
    
    def _display_runners(self, runners: List[RunnerDict]) -> None:
        """
        Muestra runners en formato compacto
        
        Args:
            runners: Lista de runners
        """
        self.console.print("")
        for idx, runner in enumerate(runners, 1):
            tags_str = ', '.join(runner.get('tags', []))
            status = "●" if runner.get('online') else "○"
            desc = runner.get('description', f"Runner #{runner['id']}")[:40]
            self.console.print(f"  {idx}. {status} {desc}")
            self.console.print(f"     [dim]{tags_str}[/dim]")
    
    def _find_default_runner_index(
        self,
        runners: List[RunnerDict],
        default_tags: Optional[List[str]]
    ) -> int:
        """
        Encuentra el índice del runner que mejor coincide con los tags
        
        Args:
            runners: Lista de runners
            default_tags: Tags por defecto
        
        Returns:
            Índice del runner (0-based)
        """
        if not default_tags:
            return 0
        
        default_set = set(default_tags)
        for idx, runner in enumerate(runners):
            runner_tags = set(runner.get('tags', []))
            if default_set.issubset(runner_tags):
                return idx
        
        return 0
    
    def _prompt_manual_tags(
        self,
        default_tags: Optional[List[str]]
    ) -> List[str]:
        """
        Solicita tags manualmente al usuario
        
        Args:
            default_tags: Tags por defecto
        
        Returns:
            Lista de tags ingresados
        """
        default_str = ','.join(default_tags) if default_tags else "docker"
        
        while True:
            tags_input = Prompt.ask(
                "Tags del runner (separados por coma)",
                default=default_str
            )
            
            tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            try:
                validate_runner_tags(tags)
                return tags
            except ValidationError as e:
                self.console.print(f"[red]✗[/red] {e.message}")
                self.console.print(f"[dim]{e.reason}[/dim]")
                # Volver a preguntar
