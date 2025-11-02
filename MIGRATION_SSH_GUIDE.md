# SSH Migration Guide (Local -> pearce@192.168.1.29)

## Overview
This guide documents the steps and artifacts created to migrate the webserver project and AI Intelligence system from the current local environment to the remote host `192.168.1.29` under user `pearce`.

## 1. New Files Added
- `remote_config.json` - JSON config containing remote host, user, auth method, sudo user.
- `.env.remote` - Environment variable file (optional, not committed). Holds host/user and placeholder for exporting passwords.
- `deploy_to_remote.sh` - Rsync-based deployment script.
- `remote_setup.sh` - Remote dependency installation and virtualenv initialization.
- `remote_test.sh` - Basic remote validation (Python version, listing, optional AI intelligence test).
- Updated `setup_and_run.sh` to optionally sync to remote if `REMOTE_HOST` or `remote_config.json` present.

## 2. Required Remote Preparation
Run the following on the remote host once you have shell access (using the provided password or after configuring SSH keys):
```bash
# Create project root and essential packages
mkdir -p /home/pearce/webserver
sudo apt update
sudo apt install -y python3 python3-venv python3-pip rsync jq
```

## 3. Authentication Methods
Currently configured for `auth_method: password`. **Recommended improvement:** switch to SSH key authentication.

### Password Method
Export environment variables locally before running scripts:
```bash
export REMOTE_SSH_PASSWORD="pearce"
export REMOTE_SUDO_PASSWORD="pearce"
```
(Password is not embedded inside scripts; you will be prompted if keyless login fails.)

### SSH Key Method (Recommended)
```bash
ssh-keygen -t ed25519 -C "migration"
ssh-copy-id -i ~/.ssh/id_ed25519.pub pearce@192.168.1.29
# Test
ssh pearce@192.168.1.29 'echo key auth OK'
```
Update `remote_config.json`:
```json
"auth_method": "key"
```

## 4. Deployment Workflow
1. Local baseline test (optional):
```bash
./setup_and_run.sh LOCAL_ONLY=true
```
2. Deploy project files:
```bash
bash deploy_to_remote.sh
```
3. Remote setup (creates venv, installs deps):
```bash
bash remote_setup.sh
```
4. Remote tests:
```bash
bash remote_test.sh
```
5. (Optional) Start remote service manually:
```bash
ssh pearce@192.168.1.29 "cd /home/pearce/webserver && source .venv/bin/activate && python src/app.py"
```

## 5. Sudo Usage Strategy
Scripts avoid embedding sudo password; any command requiring privileges should prompt interactively. If automation with sudo is needed, consider configuring passwordless sudo for specific commands:
```bash
sudo visudo
# Add line:
pearce ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/journalctl
```

## 6. Security Considerations
| Item | Action |
|------|--------|
| Plain password | Avoid storing; use exported env variables only in active shell |
| SSH keys | Prefer ed25519 key; protect private key permissions (600) |
| rsync | Uses `--delete`; ensure remote root path is correct to avoid accidental deletion |
| Virtualenv | Isolated per host; no secrets inside venv |
| Logs | Consider shipping logs via scp/rsync if needed |

## 7. Rollback Plan
If deployment breaks remote environment:
```bash
mv /home/pearce/webserver /home/pearce/webserver.bak.$(date +%s)
mkdir -p /home/pearce/webserver
# Re-run deploy and setup scripts
```

## 8. Next Improvements
- Add systemd service file for remote daemonization.
- Integrate health check script (curl remote /health) with alerting.
- Add incremental deploy (exclude tests for prod).
- Add remote backup script (`tar` + timestamp) and retrieval.

## 9. Connectivity Status
Latest connectivity test result:
```
Permission denied (publickey,password). -> Remote requires password or key setup.
```
Action: Perform first manual SSH login: `ssh pearce@192.168.1.29` and enter password `pearce`, then (optionally) configure SSH key.

## 10. Usage Summary
| Script | Purpose |
|--------|---------|
| deploy_to_remote.sh | Sync local project to remote host |
| remote_setup.sh | Prepare Python environment and install deps |
| remote_test.sh | Perform basic functionality tests remotely |
| setup_and_run.sh | Local run + optional remote sync |

## 11. AI Intelligence Remote Notes
- TinyDB file will reside at `/home/pearce/webserver/data/ai/intelligence.json` once deployed.
- Ensure directory exists: `mkdir -p /home/pearce/webserver/data/ai`
- For MongoDB usage later, set `MONGODB_URI` in remote user's `.bashrc`.

---
**Status:** Migration scaffolding complete. Awaiting first authenticated SSH session to proceed with deployment.

## 12. Sudo Automation Addendum

### Overview
Automated privileged operations are now possible through two helpers:
1. `remote_setup.sh` (installs packages when sudo password env is set)
2. `remote_sudo_exec.sh` and `remote_sudo_helper.py` (ad-hoc remote sudo commands)

### Environment Variable
Export the password before use (do NOT commit):
```bash
export REMOTE_SUDO_PASSWORD="pearce"
```
The variable name must match `sudo_password_env` in `remote_config.json`.

### Bash Helper Example
```bash
REMOTE_SUDO_PASSWORD=pearce ./remote_sudo_exec.sh "apt update"
REMOTE_SUDO_PASSWORD=pearce ./remote_sudo_exec.sh "apt install -y htop"
```

### Python Helper Example
```python
from remote_sudo_helper import remote_sudo
success, output = remote_sudo('apt update')
print(output)
```

### Security Notes
| Risk | Mitigation |
|------|------------|
| Password in env | Use ephemeral shell export; avoid persistent profile files |
| Command injection | Helper does not interpret user input beyond direct passing; ensure trusted commands |
| Log exposure | Avoid echoing password; helpers pass via stdin to sudo |
| Wide sudo rights | Restrict sudoers to required commands (systemctl, apt) |

### Optional sudoers Hardening
Edit with `visudo`:
```
pearce ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/systemctl, /usr/bin/journalctl
```
Then you can omit password environment variable for those commands.

### Testing Sudo
```bash
REMOTE_SUDO_PASSWORD=pearce python3 remote_sudo_helper.py 'whoami'  # Expect 'root'
```

### Next Improvements
- Add systemd unit creation via automated sudo script.
- Implement remote log collection `remote_logs_pull.sh`.
- Integrate health + restart policy (systemd + watchdog).
