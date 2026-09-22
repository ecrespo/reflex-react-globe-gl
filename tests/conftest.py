"""Run tests from a scratch cwd: importing the package links its shared JS asset
into ``./assets/external``, which should not pollute the repository."""

import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _scratch_cwd(tmp_path_factory):
    old = os.getcwd()
    os.chdir(tmp_path_factory.mktemp("app"))
    yield
    os.chdir(old)
