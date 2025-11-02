"""Centralized path configuration for the webserver project.

All code that needs to reference a filesystem path should import from here
instead of hard‑coding relative strings. This improves portability and makes
future path changes a single‑file edit.

Usage:
    from path_config import PATHS
    logs_dir = PATHS['logs']

The module also ensures required directories exist at import time.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

_BASE = Path(__file__).resolve().parent.parent  # project root (folder containing src/)

"""Environment-aware path derivation.

Agent storage and memory locations may live outside the project tree (e.g. Samba
mounts or external drives). These can be overridden by environment variables:
    AGENT_STORAGE_PATH   -> overrides default /home/admin1/Documents/AIAGENTSTORAGE
    AGENT_MEMORY_PATH    -> overrides default /home/admin1/aimemory

If unset, sensible defaults are used so local development continues to work.
"""

DATA_DIR = _BASE / 'data'
CONFIG_DIR = DATA_DIR / 'config'
AI_DATA_DIR = DATA_DIR / 'ai'
LOGS_DIR = _BASE / 'logs'
EXPORTS_DIR = DATA_DIR / 'exports'
UPLOADS_DIR = DATA_DIR / 'uploads'
TMP_DIR = _BASE / 'tmp'
TEMPLATES_DIR = _BASE / 'src' / 'templates'
STATIC_DIR = _BASE / 'src' / 'static'

# External / cross-agent storage (can be Samba mounted)
DEFAULT_AGENT_STORAGE = Path('/home/admin1/Documents/AIAGENTSTORAGE')
DEFAULT_AGENT_MEMORY = Path('/home/admin1/aimemory')
AGENT_STORAGE_DIR = Path(os.environ.get('AGENT_STORAGE_PATH', str(DEFAULT_AGENT_STORAGE)))
AGENT_MEMORY_DIR = Path(os.environ.get('AGENT_MEMORY_PATH', str(DEFAULT_AGENT_MEMORY)))

# Ensure existence of important directories
for d in [DATA_DIR, CONFIG_DIR, AI_DATA_DIR, LOGS_DIR, EXPORTS_DIR, UPLOADS_DIR, TMP_DIR, AGENT_STORAGE_DIR, AGENT_MEMORY_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Avoid raising during import; application can still run even if one path fails
        pass

PATHS: Dict[str, str] = {
    'base': str(_BASE),
    'data': str(DATA_DIR),
    'config': str(CONFIG_DIR),
    'ai_data': str(AI_DATA_DIR),
    'logs': str(LOGS_DIR),
    'exports': str(EXPORTS_DIR),
    'uploads': str(UPLOADS_DIR),
    'tmp': str(TMP_DIR),
    'templates': str(TEMPLATES_DIR),
    'static': str(STATIC_DIR),
    'agent_storage': str(AGENT_STORAGE_DIR),
    'agent_memory': str(AGENT_MEMORY_DIR),
}

def describe_paths() -> Dict[str, Dict[str, str]]:
    """Return a structured description of all managed paths and their state."""
    desc = {}
    for key, p in PATHS.items():
        path_obj = Path(p)
        desc[key] = {
            'path': p,
            'exists': str(path_obj.exists()),
            'is_dir': str(path_obj.is_dir()),
            'writable': str(os.access(p, os.W_OK) if path_obj.exists() else False)
        }
    return desc

__all__ = ['PATHS', 'describe_paths']
