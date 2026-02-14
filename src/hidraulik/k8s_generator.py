"""
Generador de configuraciones para Kubernetes
"""

from typing import Dict, Any, List
from jinja2 import Environment, BaseLoader


class K8sGenerator:
    """Generador de configuraciones CI/CD para Kubernetes"""
    
    def __init__(self):
        """Inicializa el generador"""
        self.jinja_env = Environment(loader=BaseLoader())
        # Variables que no deben ser sustituidas (se guardarán como variables CI/CD)
        self.cicd_vars = []
    
    def set_cicd_vars(self, cicd_vars: List[str]):
        """
        Establece la lista de variables que deben guardarse como variables CI/CD
        (no serán sustituidas en las plantillas)
        
        Args:
            cicd_vars: Lista de nombres de variables CI/CD
        """
        self.cicd_vars = cicd_vars
    
    def process_templates(
        self,
        templates: Dict[str, str],
        variables: Dict[str, Any],
        preserve_cicd_vars: bool = True
    ) -> Dict[str, str]:
        """
        Procesa las plantillas sustituyendo solo las variables de plantilla.
        Las variables CI/CD (que empiezan con CICD_) se mantienen sin sustituir.
        
        Args:
            templates: Diccionario con plantillas
            variables: Variables para sustituir
            preserve_cicd_vars: Si True, preserva variables CICD_ sin sustituir
            
        Returns:
            Diccionario con archivos procesados
        """
        processed = {}
        
        # Filtrar variables: solo sustituir las que NO son variables CI/CD
        template_variables = {
            k: v for k, v in variables.items() 
            if not (preserve_cicd_vars and k.startswith('CICD_'))
        }
        
        for file_path, content in templates.items():
            try:
                template = self.jinja_env.from_string(content)
                processed_content = template.render(**template_variables)
                processed[file_path] = processed_content
            except Exception as e:
                print(f"Error procesando {file_path}: {str(e)}")
                # En caso de error, usar el contenido original
                processed[file_path] = content
        
        return processed
