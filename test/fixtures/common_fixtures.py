# pylint: disable=missing-function-docstring, missing-module-docstring
# non-pytest fixtures
import os
import shutil
import pytest
from helpers import TestHelpers # pylint: disable=import-error


def empty_pickle():
    match_dict = {}
    inputs = {'pickle_tasks': match_dict}
    return inputs


@pytest.fixture()
def auth_cfg(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("config2")
    cfg_test = os.path.join(tmp, "auth.cfg")
    src_path = os.path.join(TestHelpers.get_root(), "source/auth.cfg")
    if os.path.exists(src_path):
        shutil.copy(src_path, cfg_test)
        os.chdir(tmp)
