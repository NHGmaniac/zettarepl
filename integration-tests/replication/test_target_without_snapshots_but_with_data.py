# -*- coding=utf-8 -*-
import subprocess
import textwrap
import time

import pytest
import yaml

from zettarepl.utils.test import run_replication_test


@pytest.mark.parametrize("zvol", [False, True])
@pytest.mark.parametrize("mounted", [False, True])
@pytest.mark.parametrize("snapdir", [False, True])
def test_target_without_snapshots_but_with_data(zvol, mounted, snapdir):
    if zvol and (not mounted or snapdir):
        return

    subprocess.call("zfs destroy -r data/src", shell=True)
    subprocess.call("zfs receive -A data/dst", shell=True)
    subprocess.call("zfs destroy -r data/dst", shell=True)

    if zvol:
        subprocess.check_call("zfs create -V 1m data/src", shell=True)
    else:
        subprocess.check_call("zfs create data/src", shell=True)
    subprocess.check_call("zfs snapshot -r data/src@2018-10-01_01-00", shell=True)
    subprocess.check_call("zfs snapshot -r data/src@2018-10-01_02-00", shell=True)

    if zvol:
        subprocess.check_call("zfs create -V 20m data/dst", shell=True)
        subprocess.check_call("dd if=/dev/urandom of=/dev/zvol/data/dst bs=15m count=1", shell=True)
    else:
        subprocess.check_call("zfs create data/dst", shell=True)
        if snapdir:
            subprocess.check_call("zfs set snapdir=visible data/dst", shell=True)
        if mounted:
            bs = "1k"
        else:
            bs = "15m"
        subprocess.check_call(f"dd if=/dev/urandom of=/mnt/data/dst/test bs={bs} count=1", shell=True)
        if not mounted:
            subprocess.check_call("zfs unmount data/dst", shell=True)
    time.sleep(5)  # "used" property is not updated immediately

    definition = yaml.safe_load(textwrap.dedent("""\
        timezone: "UTC"

        replication-tasks:
          src:
            direction: push
            transport:
              type: local
            source-dataset: data/src
            target-dataset: data/dst
            recursive: true
            also-include-naming-schema:
              - "%Y-%m-%d_%H-%M"
            auto: false
            retention-policy: none
            retries: 1
    """))
    error = run_replication_test(definition, success=False)

    assert "Refusing to overwrite existing data" in error.error
