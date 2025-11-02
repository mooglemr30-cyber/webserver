# Path Configuration Reference

This document lists all managed filesystem paths exposed via `path_config.PATHS`.
Centralizing paths allows simple relocation when migrating to remote hosts or
mounting external storage (e.g. Samba shares).

| Key | Default (local) | Description | Env Override |
|-----|-----------------|-------------|--------------|
| base | /home/admin1/Documents/webserver | Project root | (N/A) |
| data | base/data | General data root | (N/A) |
| config | base/data/config | Configuration storage | (N/A) |
| ai_data | base/data/ai | Local AI fallback TinyDB JSON files | (N/A) |
| logs | base/logs | Runtime and request logs | (N/A) |
| exports | base/data/exports | Intelligence export bundles | (N/A) |
| uploads | base/data/uploads | User uploaded files | (N/A) |
| tmp | base/tmp | Temporary workspace | (N/A) |
| templates | base/src/templates | Flask templates | (N/A) |
| static | base/src/static | Static assets | (N/A) |
| agent_storage | /home/admin1/Documents/AIAGENTSTORAGE | Cross-agent shared documents & intelligence | AGENT_STORAGE_PATH |
| agent_memory | /home/admin1/aimemory | Samba mounted long-term memory volume | AGENT_MEMORY_PATH |

## Environment Overrides

Set these before starting the server (or in systemd unit):

```bash
export AGENT_STORAGE_PATH="/home/admin1/Documents/AIAGENTSTORAGE"
export AGENT_MEMORY_PATH="/home/admin1/aimemory"
```

## Remote Migration (pearce@192.168.1.29)

On the Ubuntu server:
1. Clone or sync project to `/home/pearce/webserver`.
2. Mount Samba share for memory if needed:
   ```bash
   bash remote_mount_memory.sh
   ```
3. Export overrides (if paths differ):
   ```bash
   export AGENT_STORAGE_PATH="/home/admin1/Documents/AIAGENTSTORAGE"
   export AGENT_MEMORY_PATH="/home/admin1/aimemory"
   export REMOTE_SUDO_PASSWORD=pearce
   ```
4. Start server:
   ```bash
   cd /home/pearce/webserver
   source .venv/bin/activate
   python src/app.py
   ```

## Verification Script (planned)
Run forthcoming `path_verify.py` to produce JSON report of existence & permissions.

## Notes
* Directories are created on import where possible.
* External mounts failure will not crash server; endpoints using them should handle absence gracefully.
* Document scanner consumes `agent_storage`; long-term memory strategies can move large exports into `agent_memory`.
