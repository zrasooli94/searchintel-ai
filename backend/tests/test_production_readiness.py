import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.api.operator import require_operator
from app.main import (
    APP_VERSION,
    liveness,
    readiness,
    require_api_token,
    settings as app_settings,
)


class ProductionSettingsTests(unittest.TestCase):
    def test_provider_postgres_url_uses_psycopg_driver(self):
        settings = Settings(
            _env_file=None,
            database_url=(
                "postgresql://user:password@db.example/app"
            ),
        )

        self.assertEqual(
            settings.database_url,
            "postgresql+psycopg://"
            "user:password@db.example/app",
        )

    def test_explicit_psycopg_url_is_preserved(self):
        database_url = (
            "postgresql+psycopg://"
            "user:password@db.example/app"
        )
        settings = Settings(
            _env_file=None,
            database_url=database_url,
        )

        self.assertEqual(
            settings.database_url,
            database_url,
        )

    def test_production_requires_api_token(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                app_env="production",
                database_url="postgresql+psycopg://db/app",
                cors_origins="https://searchintel.example",
            )

    def test_production_rejects_localhost_cors(self):
        with self.assertRaises(ValidationError):
            Settings(
                _env_file=None,
                app_env="production",
                database_url="postgresql+psycopg://db/app",
                cors_origins="http://localhost:3000",
                api_token="placeholder-token",
            )

    def test_production_accepts_explicit_safe_settings(self):
        settings = Settings(
            _env_file=None,
            app_env="production",
            database_url="postgresql+psycopg://db/app",
            cors_origins="https://searchintel.example",
            api_token="placeholder-token",
        )

        self.assertEqual(
            settings.allowed_cors_origins,
            ["https://searchintel.example"],
        )


class HealthEndpointTests(unittest.TestCase):
    def test_liveness_does_not_require_database(self):
        self.assertEqual(
            liveness(),
            {
                "status": "ok",
                "version": APP_VERSION,
            },
        )

    @patch("app.main.SessionLocal")
    def test_readiness_checks_database(self, session_local):
        db = Mock()
        session_local.return_value.__enter__.return_value = db

        result = readiness()

        self.assertEqual(
            result,
            {
                "status": "ok",
                "database": "available",
                "version": APP_VERSION,
            },
        )
        db.execute.assert_called_once()

    @patch("app.main.logger")
    @patch("app.main.SessionLocal")
    def test_readiness_hides_database_error(
        self,
        session_local,
        logger,
    ):
        from sqlalchemy.exc import OperationalError

        db = Mock()
        session_local.return_value.__enter__.return_value = db
        db.execute.side_effect = OperationalError(
            "SELECT 1",
            {},
            Exception("private connection detail"),
        )

        result = readiness()

        self.assertIsInstance(result, JSONResponse)
        self.assertEqual(result.status_code, 503)
        self.assertNotIn(
            b"private connection detail",
            result.body,
        )
        logger.exception.assert_called_once_with(
            "Database readiness check failed."
        )


class OperatorAuthorizationTests(unittest.TestCase):
    def setUp(self):
        from app.api import operator

        self.operator_settings = operator.settings
        self.original_token = self.operator_settings.api_token
        self.operator_settings.api_token = SecretStr("test-token")

    def tearDown(self):
        self.operator_settings.api_token = self.original_token

    def test_unauthorized_paid_action_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            require_operator("wrong-token")

        self.assertEqual(context.exception.status_code, 403)
        self.assertNotIn(
            "test-token",
            context.exception.detail,
        )

    def test_authorized_operator_is_allowed(self):
        self.assertIsNone(
            require_operator("test-token")
        )

    def test_competitor_discovery_mutations_require_operator(self):
        from app.api.routes.competitors import router

        protected_paths = {
            "/projects/{project_id}/competitor-discovery-suggestions/generate",
            "/projects/{project_id}/competitor-discovery-suggestions/{suggestion_id}/approve",
            "/projects/{project_id}/competitor-discovery-suggestions/{suggestion_id}/ignore",
        }
        routes = {
            route.path: route
            for route in router.routes
            if getattr(route, "path", None) in protected_paths
        }
        self.assertEqual(set(routes), protected_paths)
        for route in routes.values():
            dependency_calls = {
                dependency.call
                for dependency in route.dependant.dependencies
            }
            self.assertIn(require_operator, dependency_calls)

    def test_prompt_generation_and_configuration_mutations_require_operator(self):
        from app.api.routes.prompts import router

        protected_paths = {
            "/projects/{project_id}/prompts/starter-generate",
            "/projects/{project_id}/prompts/starter-proposals/{proposal_id}/apply",
            "/projects/{project_id}/prompts/starter-proposals/{proposal_id}/semantic-reevaluate",
            "/projects/{project_id}/prompts/active-set",
            "/projects/{project_id}/prompts/bulk",
            "/projects/{project_id}/prompts",
            "/projects/{project_id}/prompts/{prompt_id}",
        }
        routes = {
            route.path: route
            for route in router.routes
            if getattr(route, "path", None) in protected_paths
            and "GET" not in getattr(route, "methods", set())
        }
        self.assertEqual(set(routes), protected_paths)
        for route in routes.values():
            self.assertIn(
                require_operator,
                {dependency.call for dependency in route.dependant.dependencies},
            )


class ApiTokenMiddlewareTests(
    unittest.IsolatedAsyncioTestCase
):
    async def asyncSetUp(self):
        self.original_token = app_settings.api_token
        app_settings.api_token = SecretStr("test-token")

    async def asyncTearDown(self):
        app_settings.api_token = self.original_token

    async def test_api_request_requires_matching_token(self):
        request = SimpleRequest(
            path="/api/v1/projects/workspaces",
            authorization="Bearer wrong-token",
        )
        call_next = Mock()

        result = await require_api_token(
            request,
            call_next,
        )

        self.assertEqual(result.status_code, 401)
        call_next.assert_not_called()

    async def test_health_request_remains_unauthenticated(self):
        request = SimpleRequest(path="/health")
        expected = object()

        async def call_next(_request):
            return expected

        result = await require_api_token(
            request,
            call_next,
        )

        self.assertIs(result, expected)

    async def test_matching_token_reaches_api(self):
        request = SimpleRequest(
            path="/api/v1/projects/workspaces",
            authorization="Bearer test-token",
        )
        expected = object()

        async def call_next(_request):
            return expected

        result = await require_api_token(
            request,
            call_next,
        )

        self.assertIs(result, expected)


class SimpleRequest:
    def __init__(
        self,
        path: str,
        authorization: str | None = None,
    ):
        self.url = type(
            "URL",
            (),
            {"path": path},
        )()
        self.headers = {}
        if authorization is not None:
            self.headers["authorization"] = authorization


if __name__ == "__main__":
    unittest.main()
