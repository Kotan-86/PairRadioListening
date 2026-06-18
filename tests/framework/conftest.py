# 仕様: docs/spec/framework.md#5
from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from framework.bootstrap import AppDeps, build_deps, create_app
from framework.settings import load_settings


@pytest.fixture
def deps() -> AppDeps:
    # .env の AMIVOICE_API_KEY があっても HTTP 統合テストは Null Bridge を使う。
    settings = replace(load_settings(), amivoice_api_key=None)
    return build_deps(settings)


@pytest.fixture
def app(deps: AppDeps):
    return create_app(deps, testing=True)


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
