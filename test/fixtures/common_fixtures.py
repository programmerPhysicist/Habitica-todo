# pylint: disable=missing-function-docstring, missing-module-docstring
# non-pytest fixtures
import os
import shutil
import pytest

# pylint: disable=import-error
from helpers import TestHelpers


def empty_pickle():
    match_dict = {}
    inputs = {'pickle_tasks': match_dict}
    return inputs


@pytest.fixture
def fake_config_file(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config")
    cfg_for_test = os.path.join(tmp, "auth.cfg")
    cfg = open(cfg_for_test, 'w')
    line = ["[Habitica]\n", "url = https://habitica.com\n",
            "login = cd18fc9f-b649-4384-932a-f3bda6fe8102\n",
            "password = 18f22441-2c87-6d8e-fb2a-3fa670837b5a\n",
            "\n", "[Todoist]\n",
            "api-token = d1347120363c2b310653f610d382729bd51e13c6\n", "\n"]
    cfg.writelines(line)
    cfg.close()
    os.chdir(tmp)

    yield
    # clean-up
    shutil.rmtree(tmp)


@pytest.fixture()
def auth_cfg(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config2")
    cfg_test = os.path.join(tmp, "auth.cfg")
    src_path = os.path.join(TestHelpers.get_root(), "source/auth.cfg")
    if os.path.exists(src_path):
        shutil.copy(src_path, cfg_test)
        os.chdir(tmp)

    yield
    # clean-up
    shutil.rmtree(tmp)
