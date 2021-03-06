# -*- coding=utf-8 -*-
import hashlib
import logging
import os

from .interface import Shell

logger = logging.getLogger(__name__)

__all__ = ["put_file"]


def put_file(name, shell: Shell):
    local_path = os.path.join(os.path.dirname(__file__), "..", name)
    with open(local_path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
        f.seek(0)

        remote_path = f"/tmp/zettarepl--{name.replace('/', '--')}--{md5}"
        if not shell.exists(remote_path):
            shell.put_file(f, remote_path)

    return remote_path
