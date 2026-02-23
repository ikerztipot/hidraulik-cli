"""
Tests para los servicios: VariableService, RunnerService, K8sConfigService
"""

import pytest
from unittest.mock import Mock, patch
from io import StringIO
from rich.console import Console

from hidraulik.services import VariableService, RunnerService, K8sConfigService


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _console():
    return Console(file=StringIO(), highlight=False)


# ─────────────────────────────────────────────────────────────────────────────
# VariableService – init
# ─────────────────────────────────────────────────────────────────────────────

class TestVariableService:
    def test_init(self):
        service = VariableService(_console())
        assert service.console is not None

    # ── create_gitlab_variables ──────────────────────────────────────────────

    def test_create_gitlab_variables_empty(self):
        """Con dicts vacíos, sólo crea KUBE_CONTEXT"""
        client = Mock()
        service = VariableService(_console())
        count = service.create_gitlab_variables(
            client,
            'group/proj',
            config_vars={},
            secret_vars={},
            kube_contexts={'production': 'prod-context'},
        )
        assert count == 1
        client.create_or_update_variable.assert_called_once_with(
            'group/proj',
            'KUBE_CONTEXT',
            'prod-context',
            protected=False,
            masked=False,
            environment_scope='production',
        )

    def test_create_gitlab_variables_with_config_and_secrets(self):
        """Crea variables de config y secretas"""
        client = Mock()
        service = VariableService(_console())
        count = service.create_gitlab_variables(
            client,
            'group/proj',
            config_vars={'api': ['DATABASE_URL', 'REDIS_URL']},
            secret_vars={'api': ['JWT_SECRET']},
            kube_contexts={'prod': 'prod-ctx', 'staging': 'staging-ctx'},
        )
        # 2 kube_contexts + 2 config vars + 1 secret = 5
        assert count == 5
        assert client.create_or_update_variable.call_count == 5

    def test_create_gitlab_variables_secrets_masked(self):
        """Las variables secretas se crean con masked=True"""
        client = Mock()
        service = VariableService(_console())
        service.create_gitlab_variables(
            client,
            'group/proj',
            config_vars={},
            secret_vars={'app': ['MY_SECRET']},
            kube_contexts={},
        )
        args, kwargs = client.create_or_update_variable.call_args
        assert kwargs.get('masked') is True

    def test_create_gitlab_variables_config_not_masked(self):
        """Las variables de config se crean sin masked"""
        client = Mock()
        service = VariableService(_console())
        service.create_gitlab_variables(
            client,
            'group/proj',
            config_vars={'app': ['APP_ENV']},
            secret_vars={},
            kube_contexts={},
        )
        args, kwargs = client.create_or_update_variable.call_args
        assert kwargs.get('masked') is False

    # ── display_pending_configuration ───────────────────────────────────────

    def test_display_pending_configuration_no_vars(self):
        """No imprime nada si no hay variables"""
        out = StringIO()
        service = VariableService(Console(file=out, highlight=False))
        service.display_pending_configuration({}, {}, 'https://gitlab.com/proj')
        assert out.getvalue() == ''

    def test_display_pending_configuration_with_vars(self):
        """Imprime warning con el número de variables"""
        out = StringIO()
        service = VariableService(Console(file=out, highlight=False))
        service.display_pending_configuration(
            config_vars={'app': ['DB_URL']},
            secret_vars={'app': ['SECRET_KEY']},
            project_web_url='https://gitlab.com/proj',
        )
        output = out.getvalue()
        assert '2' in output or 'variable' in output.lower()

    # ── collect_component_variables ──────────────────────────────────────────

    def test_collect_component_variables_empty_input(self):
        """Sin variables ingresadas retorna listas vacías"""
        with patch('hidraulik.services.variable_service.Prompt.ask', return_value=''):
            service = VariableService(_console())
            config_vars, secret_vars = service.collect_component_variables('frontend')
        assert config_vars == []
        assert secret_vars == []

    def test_collect_component_variables_one_config(self):
        """Agrega una variable de config (no secret)"""
        ask_answers = iter(['DB_URL', ''])
        with patch('hidraulik.services.variable_service.Prompt.ask', side_effect=ask_answers):
            with patch('hidraulik.services.variable_service.Confirm.ask', return_value=False):
                service = VariableService(_console())
                config_vars, secret_vars = service.collect_component_variables('api')
        assert 'DB_URL' in config_vars
        assert secret_vars == []

    def test_collect_component_variables_one_secret(self):
        """Agrega una variable como secret"""
        ask_answers = iter(['JWT_SECRET', ''])
        with patch('hidraulik.services.variable_service.Prompt.ask', side_effect=ask_answers):
            with patch('hidraulik.services.variable_service.Confirm.ask', return_value=True):
                service = VariableService(_console())
                config_vars, secret_vars = service.collect_component_variables('api')
        assert 'JWT_SECRET' in secret_vars
        assert config_vars == []

    def test_collect_component_variables_invalid_then_valid(self):
        """Reintenta con nombre inválido hasta obtener uno válido"""
        # '123invalid' es inválido (empieza con número), 'VALID_VAR' es válido
        ask_answers = iter(['123invalid', 'VALID_VAR', ''])
        confirm_answers = iter([False])
        with patch('hidraulik.services.variable_service.Prompt.ask', side_effect=ask_answers):
            with patch('hidraulik.services.variable_service.Confirm.ask', side_effect=confirm_answers):
                service = VariableService(_console())
                config_vars, secret_vars = service.collect_component_variables('api')
        assert 'VALID_VAR' in config_vars
        assert '123invalid' not in config_vars


# ─────────────────────────────────────────────────────────────────────────────
# RunnerService – init
# ─────────────────────────────────────────────────────────────────────────────

class TestRunnerService:
    def test_init(self):
        service = RunnerService(Mock(), _console())
        assert service.client is not None

    # ── _fetch_and_add_runners ───────────────────────────────────────────────

    def test_fetch_and_add_runners_deduplicates(self):
        """No añade runners con el mismo id"""
        service = RunnerService(Mock(), _console())
        all_runners = [{'id': 1, 'tags': ['docker']}]
        seen_ids = {1}
        service._fetch_and_add_runners(
            lambda: [{'id': 1, 'tags': ['docker']}, {'id': 2, 'tags': ['k8s']}],
            all_runners,
            seen_ids,
        )
        assert len(all_runners) == 2  # solo añade id=2
        assert all_runners[1]['id'] == 2

    def test_fetch_and_add_runners_skips_no_tags(self):
        """No añade runners sin tags"""
        service = RunnerService(Mock(), _console())
        all_runners = []
        seen_ids = set()
        service._fetch_and_add_runners(
            lambda: [{'id': 5, 'tags': []}],
            all_runners,
            seen_ids,
        )
        assert all_runners == []

    def test_fetch_and_add_runners_silences_error(self):
        """Silencia excepciones del fetcher"""
        service = RunnerService(Mock(), _console())
        all_runners = []
        seen_ids = set()

        def raise_err():
            raise Exception("permission denied")

        service._fetch_and_add_runners(raise_err, all_runners, seen_ids)
        assert all_runners == []

    # ── discover_available_runners ───────────────────────────────────────────

    def test_discover_available_runners_basic(self):
        client = Mock()
        client.get_available_runners.return_value = [
            {'id': 1, 'tags': ['docker'], 'description': 'R1'},
        ]
        client.get_group_runners.return_value = []
        client.get_project_runners.return_value = []

        service = RunnerService(client, _console())
        runners = service.discover_available_runners(
            project_path='group/proj',
            template_repo='group/tmpl',
        )
        assert any(r['id'] == 1 for r in runners)

    def test_discover_available_runners_no_paths(self):
        client = Mock()
        client.get_available_runners.return_value = [
            {'id': 1, 'tags': ['docker']}
        ]
        service = RunnerService(client, _console())
        runners = service.discover_available_runners()
        assert any(r['id'] == 1 for r in runners)

    # ── _find_default_runner_index ───────────────────────────────────────────

    def test_find_default_runner_index_match(self):
        service = RunnerService(Mock(), _console())
        runners = [
            {'id': 1, 'tags': ['linux']},
            {'id': 2, 'tags': ['docker', 'linux']},
        ]
        idx = service._find_default_runner_index(runners, ['docker', 'linux'])
        assert idx == 1

    def test_find_default_runner_index_no_match(self):
        service = RunnerService(Mock(), _console())
        runners = [{'id': 1, 'tags': ['linux']}]
        idx = service._find_default_runner_index(runners, ['windows'])
        assert idx == 0

    def test_find_default_runner_index_no_defaults(self):
        service = RunnerService(Mock(), _console())
        idx = service._find_default_runner_index(
            [{'id': 1, 'tags': ['docker']}], None
        )
        assert idx == 0

    # ── _display_runners ────────────────────────────────────────────────────

    def test_display_runners(self):
        out = StringIO()
        service = RunnerService(Mock(), Console(file=out, highlight=False))
        service._display_runners([
            {'id': 1, 'description': 'Runner A', 'tags': ['docker'], 'online': True},
            {'id': 2, 'description': 'Runner B', 'tags': [], 'online': False},
        ])
        output = out.getvalue()
        assert 'Runner A' in output

    # ── select_runner_interactive ────────────────────────────────────────────

    def test_select_runner_interactive_no_runners_manual(self):
        """Sin runners disponibles pide tags manual"""
        with patch('hidraulik.services.runner_service.Prompt.ask', return_value='docker,linux'):
            from hidraulik.validators import validate_runner_tags
            service = RunnerService(Mock(), _console())
            tags = service.select_runner_interactive([], default_tags=['docker'])
            assert 'docker' in tags

    def test_select_runner_interactive_valid_choice(self):
        runners = [{'id': 1, 'tags': ['docker'], 'description': 'R', 'online': True}]
        with patch('hidraulik.services.runner_service.Prompt.ask', return_value='1'):
            service = RunnerService(Mock(), _console())
            tags = service.select_runner_interactive(runners)
            assert tags == ['docker']

    def test_select_runner_interactive_invalid_index_fallback(self):
        """Índice fuera de rango cae a prompt manual"""
        runners = [{'id': 1, 'tags': ['docker'], 'description': 'R', 'online': True}]
        with patch(
            'hidraulik.services.runner_service.Prompt.ask',
            side_effect=['99', 'docker']
        ):
            service = RunnerService(Mock(), _console())
            tags = service.select_runner_interactive(runners)
            assert 'docker' in tags

    def test_select_runner_interactive_empty_tags_fallback(self):
        """Runner con tags vacíos cae a prompt manual (ValidationError)"""
        # Runner con tags vacíos -> validation falla -> _prompt_manual_tags
        runners = [{'id': 1, 'tags': [], 'description': 'R', 'online': True}]
        with patch(
            'hidraulik.services.runner_service.Prompt.ask',
            side_effect=['1', 'docker,linux']
        ):
            service = RunnerService(Mock(), _console())
            tags = service.select_runner_interactive(runners)
            assert 'docker' in tags

    def test_prompt_manual_tags_retry_on_invalid(self):
        """_prompt_manual_tags reintenta si los tags son inválidos (vacíos)"""
        # Primera entrada vacía (inválida), segunda con tags válidos
        with patch(
            'hidraulik.services.runner_service.Prompt.ask',
            side_effect=['', 'kubernetes,linux']
        ):
            service = RunnerService(Mock(), _console())
            tags = service._prompt_manual_tags(['docker'])
            assert 'kubernetes' in tags


# ─────────────────────────────────────────────────────────────────────────────
# K8sConfigService
# ─────────────────────────────────────────────────────────────────────────────

class TestK8sConfigService:
    def test_init(self):
        service = K8sConfigService(_console())
        assert service.console is not None

    def test_profiles(self):
        assert hasattr(K8sConfigService, 'RESOURCE_PROFILES')
        assert 'medium' in K8sConfigService.RESOURCE_PROFILES
        assert 'xsmall' in K8sConfigService.RESOURCE_PROFILES
        assert 'xlarge' in K8sConfigService.RESOURCE_PROFILES

    def test_manifest_types(self):
        assert 'deployment' in K8sConfigService.MANIFEST_TYPES
        assert 'secrets' in K8sConfigService.MANIFEST_TYPES

    # ── display_resource_profiles ────────────────────────────────────────────

    def test_display_resource_profiles(self):
        out = StringIO()
        service = K8sConfigService(Console(file=out, highlight=False))
        service.display_resource_profiles()
        output = out.getvalue()
        assert 'medium' in output
        assert 'CPU' in output

    # ── configure_component_deployment ──────────────────────────────────────

    def test_configure_component_deployment_no_k8s(self):
        """Si el usuario dice No, retorna (False, [])"""
        with patch('hidraulik.services.k8s_config_service.Confirm.ask', return_value=False):
            service = K8sConfigService(_console())
            deploy, manifests = service.configure_component_deployment('frontend')
        assert deploy is False
        assert manifests == []

    def test_configure_component_deployment_with_all_manifests(self):
        """Si el usuario dice Sí a todo, retorna lista de manifiestos"""
        answers = iter([True, True, True, True, True, True, True, True])
        with patch('hidraulik.services.k8s_config_service.Confirm.ask', side_effect=answers):
            service = K8sConfigService(_console())
            deploy, manifests = service.configure_component_deployment(
                'backend', has_config_vars=False, has_secret_vars=False
            )
        assert deploy is True
        assert 'deployment' in manifests

    def test_configure_component_deployment_auto_activates_on_vars(self):
        """Secrets/ConfigMaps se auto-activan si hay variables"""
        # Sólo pregunta por deployment, ingress, service, pvc (no secrets/configs/namespace)
        confirm_answers = [True, True, True, True, True, False]
        idx = 0

        def fake_confirm(question, default=True):
            nonlocal idx
            # primer ask es "¿se despliega en K8s?"
            if '¿' in question and 'despliega' in question:
                return True
            nonlocal confirm_answers
            val = confirm_answers[idx % len(confirm_answers)]
            idx += 1  # type: ignore
            return val

        with patch('hidraulik.services.k8s_config_service.Confirm.ask', side_effect=fake_confirm):
            service = K8sConfigService(_console())
            deploy, manifests = service.configure_component_deployment(
                'app',
                has_config_vars=True,
                has_secret_vars=True,
                namespace_provided=True,
            )
        assert deploy is True
        assert 'namespace' in manifests
        assert 'secrets' in manifests
        assert 'configs' in manifests

    # ── select_resource_profile ──────────────────────────────────────────────

    def test_select_resource_profile(self):
        with patch('hidraulik.services.k8s_config_service.Prompt.ask', return_value='small'):
            service = K8sConfigService(_console())
            profile = service.select_resource_profile('api')
        assert profile == 'small'

    # ── configure_pvc_volumes ────────────────────────────────────────────────

    def test_configure_pvc_volumes_empty(self):
        """Sin volúmenes ingresados retorna lista vacía"""
        with patch('hidraulik.services.k8s_config_service.Prompt.ask', return_value=''):
            service = K8sConfigService(_console())
            volumes = service.configure_pvc_volumes('app')
        assert volumes == []

    def test_configure_pvc_volumes_one(self):
        """Configura un volumen y termina"""
        ask_answers = iter(['uploads', '/opt/uploads', '5Gi', ''])
        with patch('hidraulik.services.k8s_config_service.Prompt.ask', side_effect=ask_answers):
            service = K8sConfigService(_console())
            volumes = service.configure_pvc_volumes('app')
        assert len(volumes) == 1
        assert volumes[0]['name'] == 'uploads'
        assert volumes[0]['storage'] == '5Gi'

    def test_configure_pvc_volumes_invalid_storage_then_valid(self):
        """Reintenta con storage inválido hasta obtener uno válido"""
        ask_answers = iter(['data', '/data', 'bad-size', '10Gi', ''])
        with patch('hidraulik.services.k8s_config_service.Prompt.ask', side_effect=ask_answers):
            service = K8sConfigService(_console())
            volumes = service.configure_pvc_volumes('app')
        assert volumes[0]['storage'] == '10Gi'

    # ── configure_container_port ─────────────────────────────────────────────

    def test_configure_container_port_valid(self):
        with patch('hidraulik.services.k8s_config_service.Prompt.ask', return_value='8080'):
            service = K8sConfigService(_console())
            port = service.configure_container_port('api')
        assert port == '8080'

    def test_configure_container_port_invalid_then_valid(self):
        """Reintenta con puerto inválido hasta obtener uno válido"""
        with patch(
            'hidraulik.services.k8s_config_service.Prompt.ask',
            side_effect=['99999', '3000'],
        ):
            service = K8sConfigService(_console())
            port = service.configure_container_port('api')
        assert port == '3000'
