"""
Tests simplificados para servicios
"""

import pytest
from unittest.mock import Mock
from hidraulik.services import VariableService, RunnerService, K8sConfigService


class TestVariableService:
    def test_init(self):
        service = VariableService(Mock())
        assert service.console is not None


class TestRunnerService:
    def test_init(self):
        service = RunnerService(Mock(), Mock())
        assert service.client is not None


class TestK8sConfigService:
    def test_init(self):
        service = K8sConfigService(Mock())
        assert service.console is not None
    
    def test_profiles(self):
        assert hasattr(K8sConfigService, 'RESOURCE_PROFILES')
