# Webserver Systemd Service Guide

## Service Status

The webserver is now running as a systemd service and will automatically start on boot.

## Useful Commands

### Check Service Status
```bash
sudo systemctl status webserver.service
```

### Start the Service
```bash
sudo systemctl start webserver.service
```

### Stop the Service
```bash
sudo systemctl stop webserver.service
```

### Restart the Service
```bash
sudo systemctl restart webserver.service
```

### Enable Auto-Start on Boot
```bash
sudo systemctl enable webserver.service
```

### Disable Auto-Start on Boot
```bash
sudo systemctl disable webserver.service
```

### View Logs (Live)
```bash
sudo journalctl -u webserver.service -f
```

### View Recent Logs
```bash
sudo journalctl -u webserver.service -n 100 --no-pager
```

### View Log Files
```bash
# Standard output
tail -f /home/admin1/Documents/webserver/logs/webserver.log

# Error output
tail -f /home/admin1/Documents/webserver/logs/webserver-error.log
```

## Service Configuration

**Service File Location**: `/etc/systemd/system/webserver.service`

**Key Features**:
- Runs as user `admin1`
- Uses virtual environment at `.venv/`
- Auto-restarts on failure (10 second delay)
- Logs to `logs/webserver.log` and `logs/webserver-error.log`
- Starts automatically on system boot

## Accessing the Server

- **Local**: http://localhost:8000
- **Network**: http://192.168.1.86:8000
- **Mobile Tunnel**: Check service logs for Cloudflare tunnel URL

## Troubleshooting

If the service fails to start:
1. Check logs: `sudo journalctl -u webserver.service -n 50`
2. Check permissions: Ensure `/home/admin1/Documents/webserver` is readable
3. Check virtual environment: Ensure `.venv/` has all dependencies installed
4. Manually test: `cd /home/admin1/Documents/webserver && .venv/bin/python3 src/app.py`

## Updating the Service

After making changes to the code:
```bash
sudo systemctl restart webserver.service
```

After modifying the service file:
```bash
sudo cp webserver.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart webserver.service
```
