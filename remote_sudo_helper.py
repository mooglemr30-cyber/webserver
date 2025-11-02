#!/usr/bin/env python3
"""Remote sudo helper for AI agents.

Provides a function to run privileged commands on the remote host defined in
remote_config.json using SSH and an environment variable for password passing.

Usage:
    from remote_sudo_helper import remote_sudo
    success, output = remote_sudo('apt update')
"""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path
from typing import Tuple

CONFIG_PATH = Path(__file__).parent / 'remote_config.json'

def _load_config():
    with CONFIG_PATH.open('r', encoding='utf-8') as f:
        return json.load(f)

def remote_sudo(command: str, timeout: int = 120) -> Tuple[bool, str]:
    cfg = _load_config()
    host = cfg.get('remote_host')
    user = cfg.get('remote_user')
    port = cfg.get('remote_port', 22)
    pw_env = cfg.get('sudo_password_env')
    password = os.environ.get(pw_env or '')
    if not password:
        return False, f"Sudo password env '{pw_env}' not set. Export and retry."

    ssh_cmd = [
        'ssh', '-p', str(port), f'{user}@{host}',
        "bash -c 'echo \"" + password + "\" | sudo -S " + command.replace("'", "'\\''") + "'"
    ]
    try:
        proc = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        ok = proc.returncode == 0
        output = proc.stdout + proc.stderr
        return ok, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout}s running remote sudo command"
    except Exception as e:
        return False, f"Exception: {e}"  # noqa

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Provide command, e.g.: python remote_sudo_helper.py 'apt update'", flush=True)
        raise SystemExit(1)
    success, out = remote_sudo(' '.join(sys.argv[1:]))
    print(out)
    if not success:
        raise SystemExit(2)
