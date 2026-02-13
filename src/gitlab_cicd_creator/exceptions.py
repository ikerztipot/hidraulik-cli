"""
Jerarquía de excepciones personalizada para GitLab CI/CD Creator
"""


class GitLabCICDError(Exception):
    """Excepción base para el proyecto"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(GitLabCICDError):
    """Error en la configuración del CLI"""
    pass


class GitLabAPIError(GitLabCICDError):
    """Error al interactuar con GitLab API"""
    
    def __init__(
        self,
        message: str,
        status_code: int = None,
        response_data: dict = None
    ):
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(message, {'status_code': status_code})


class ProjectNotFoundError(GitLabAPIError):
    """Proyecto no encontrado en GitLab"""
    
    def __init__(self, project_path: str):
        super().__init__(
            f"Proyecto no encontrado: {project_path}",
            status_code=404
        )
        self.project_path = project_path


class AuthenticationError(GitLabAPIError):
    """Error de autenticación con GitLab"""
    
    def __init__(self, message: str = "Token inválido o expirado"):
        super().__init__(message, status_code=401)


class TemplateError(GitLabCICDError):
    """Error procesando plantillas"""
    pass


class TemplateNotFoundError(TemplateError):
    """Plantilla no encontrada"""
    
    def __init__(self, template_path: str):
        super().__init__(f"Plantilla no encontrada: {template_path}")
        self.template_path = template_path


class ValidationError(GitLabCICDError):
    """Error de validación de inputs"""
    
    def __init__(self, field: str, value: str, reason: str):
        super().__init__(f"Validación falló para '{field}': {reason}")
        self.field = field
        self.value = value
        self.reason = reason
