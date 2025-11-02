#!/usr/bin/env python3
"""Persistent tunnel manager for exposing the local web server to the internet.

This was reconstructed as the original file was missing. The implementation
focuses on a single on-demand Cloudflare (cloudflared) ephemeral tunnel.

Interface contract (used by app.py):
    persistent_tunnel = PersistentTunnelManager()
    persistent_tunnel.start_tunnel(port=8000) -> dict with keys:
        success (bool), url (str|None), status (str), message (str), started_at (iso)
    persistent_tunnel.stop_tunnel() -> similar dict with updat-+ed status
    persistent_tunnel.get_status() -> dict status summary
    persistent_tunnel.get_mobile_config() -> dict consumed by /api/mobile/config

Behavior:
    * If cloudflared binary is available it launches:
          cloudflared tunnel --url http://localhost:<port>
      and parses stderr for the public URL.
    * If cloudflared is not installed, returns a graceful message with
      success=False without raising exceptions.
    * Repeated start calls when already running return current status.
    * Background monitor thread observes the process and marks status=error
      or restarts (optional) – currently we only mark status; auto-restart can
      be enabled by setting AUTO_RESTART_TUNNEL=1 env variable.

Security Notes:
    * This ephemeral tunnel is unauthenticated and should not be considered
      production-ready without additional auth middleware.
    * We deliberately avoid exposing details beyond the URL & status.
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
import datetime as _dt
from typing import Optional, Dict, Any


class PersistentTunnelManager:
    """Manage a single persistent cloudflared tunnel instance."""

    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._url: Optional[str] = None
        self._status: str = "stopped"  # stopped|starting|running|error
        self._started_at: Optional[_dt.datetime] = None
        self._last_status_check: Optional[_dt.datetime] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    # -------------------- Public API --------------------
    def start_tunnel(self, port: int = 8000) -> Dict[str, Any]:
        """Start tunnel if not already running.

        Returns a status dict (see module docstring). Does NOT raise.
        """
        with self._lock:
            if self._process and self._process.poll() is None:
                # Already running
                return self._build_response(success=True, message="Tunnel already running")

            # Reset state
            self._url = None
            self._status = "starting"
            self._started_at = _dt.datetime.utcnow()
            self._last_status_check = self._started_at
            self._stop_event.clear()

            # Verify binary availability
            if not self._cloudflared_available():
                self._status = "error"
                return self._build_response(
                    success=False,
                    message=(
                        "cloudflared binary not found. Install with: "
                        "wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb "
                        "&& sudo dpkg -i cloudflared-linux-amd64.deb"
                    )
                )

            # Launch process
            try:
                self._process = subprocess.Popen(
                    ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                )
            except Exception as e:
                self._status = "error"
                return self._build_response(success=False, message=f"Failed to start process: {e}")

            # Parse initial output to obtain URL
            self._url = self._extract_url(timeout=15.0)
            if self._url:
                self._status = "running"
            else:
                # Process might still be running; mark running with unknown URL or error based on exit code
                if self._process.poll() is None:
                    self._status = "running"  # URL may appear later
                else:
                    self._status = "error"

            # Start monitor thread
            self._ensure_monitor_thread()
            return self._build_response(success=self._status == "running", message=self._status)

    def stop_tunnel(self) -> Dict[str, Any]:
        """Stop tunnel if running."""
        with self._lock:
            if not self._process or self._process.poll() is not None:
                self._process = None
                self._status = "stopped"
                self._url = None
                return self._build_response(success=True, message="Tunnel already stopped")

            try:
                self._stop_event.set()
                self._process.terminate()
                # Grace period
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                finally:
                    self._process = None
            except Exception as e:
                self._status = "error"
                return self._build_response(success=False, message=f"Failed to stop tunnel: {e}")

            self._status = "stopped"
            self._url = None
            return self._build_response(success=True, message="Tunnel stopped")

    def get_status(self) -> Dict[str, Any]:
        """Return current status summary."""
        with self._lock:
            self._last_status_check = _dt.datetime.utcnow()
            alive = self._process is not None and self._process.poll() is None
            if not alive and self._status == "running":
                # Process died unexpectedly
                self._status = "error"
                if os.environ.get("AUTO_RESTART_TUNNEL") == "1":
                    # Attempt restart
                    port = self._infer_port() or 8000
                    self.start_tunnel(port=port)
            return {
                "status": self._status,
                "url": self._url,
                "process_alive": alive,
                "started_at": self._started_at.isoformat() if self._started_at else None,
                "last_check": self._last_status_check.isoformat() if self._last_status_check else None,
            }

    def get_mobile_config(self) -> Dict[str, Any]:
        """Return configuration blob for mobile clients."""
        status = self.get_status()
        local_port = self._infer_port() or 8000
        local_url = f"http://localhost:{local_port}"
        network_url = f"http://{self._get_local_ip()}:{local_port}"
        return {
            "tunnel_url": status.get("url"),
            "status": status.get("status"),
            "local_url": local_url,
            "network_url": network_url,
            "process_alive": status.get("process_alive"),
            "started_at": status.get("started_at"),
        }

    # -------------------- Internal Helpers --------------------
    def _cloudflared_available(self) -> bool:
        try:
            subprocess.run(["cloudflared", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def _extract_url(self, timeout: float = 10.0) -> Optional[str]:
        """Read stderr lines until URL found or timeout."""
        if not self._process:
            return None
        end_time = time.time() + timeout
        url: Optional[str] = None
        while time.time() < end_time and self._process.poll() is None:
            try:
                line = self._process.stderr.readline()
            except Exception:
                break
            if not line:
                time.sleep(0.25)
                continue
            lower = line.lower()
            if "error" in lower and "tunnel" in lower and not url:
                # Capture error state if starting fails early
                self._status = f"error"
            if "https://" in line and ("trycloudflare.com" in line or "cfargotunnel.com" in line):
                # Extract first https://... token
                import re
                m = re.search(r"https://[^\s]+", line)
                if m:
                    url = m.group(0).strip()
                    break
        return url

    def _ensure_monitor_thread(self) -> None:
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._monitor_thread = threading.Thread(target=self._monitor_loop, name="tunnel-monitor", daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self) -> None:
        """Lightweight monitor that marks status when process exits."""
        while not self._stop_event.is_set():
            with self._lock:
                if self._process and self._process.poll() is not None:
                    if self._status == "running":
                        self._status = "error"  # unexpected exit
                    break
            time.sleep(2.0)

    def _infer_port(self) -> Optional[int]:
        # We embed the port in the command line invocation; attempt to parse it.
        if not self._process or not self._process.args:
            return None
        try:
            args = list(self._process.args)
        except Exception:
            return None
        # Look for http://localhost:<port>
        for token in args:
            if isinstance(token, str) and token.startswith("http://localhost:"):
                try:
                    return int(token.split(":")[-1])
                except ValueError:
                    return None
        return None

    def _get_local_ip(self) -> str:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _build_response(self, *, success: bool, message: str) -> Dict[str, Any]:
        return {
            "success": success,
            "url": self._url,
            "status": self._status,
            "message": message,
            "started_at": self._started_at.isoformat() if self._started_at else None,
        }


__all__ = ["PersistentTunnelManager"]
