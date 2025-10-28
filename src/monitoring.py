#!/usr/bin/env python3
"""
Advanced monitoring and analytics system.
Provides comprehensive system monitoring, performance analytics, and alerting.
"""

import psutil
import time
import threading
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics
import logging
import schedule
import logging
import requests

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_used: int
    disk_usage_percent: float
    disk_free: int
    disk_used: int
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: List[float]
    temperature: Optional[float] = None

@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    timestamp: datetime
    active_sessions: int
    total_requests: int
    failed_requests: int
    average_response_time: float
    database_connections: int
    cache_hit_rate: float
    websocket_connections: int
    file_operations: int
    command_executions: int

@dataclass
class Alert:
    """System alert definition."""
    id: str
    severity: str  # critical, warning, info
    title: str
    description: str
    timestamp: datetime
    resolved: bool = False
    acknowledged: bool = False
    metric_type: str = ""
    threshold_value: float = 0.0
    current_value: float = 0.0

class MetricsCollector:
    """Collect system and application metrics."""
    
    def __init__(self):
        self.last_network_io = None
        self.start_time = datetime.now()
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network_io = psutil.net_io_counters()
            
            # Process count
            process_count = len(psutil.pids())
            
            # Load average (Unix only)
            try:
                load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_average = [0.0, 0.0, 0.0]
            
            # Temperature (if available)
            temperature = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get first available temperature sensor
                    for name, entries in temps.items():
                        if entries:
                            temperature = entries[0].current
                            break
            except (AttributeError, OSError):
                pass
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                memory_used=memory.used,
                disk_usage_percent=disk.percent,
                disk_free=disk.free,
                disk_used=disk.used,
                network_bytes_sent=network_io.bytes_sent,
                network_bytes_recv=network_io.bytes_recv,
                process_count=process_count,
                load_average=load_average,
                temperature=temperature
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available=0,
                memory_used=0,
                disk_usage_percent=0.0,
                disk_free=0,
                disk_used=0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                process_count=0,
                load_average=[0.0, 0.0, 0.0]
            )

class MetricsStorage:
    """Store and retrieve metrics data."""
    
    def __init__(self, db_path: str = "data/metrics.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize metrics database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # System metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        memory_available INTEGER,
                        memory_used INTEGER,
                        disk_usage_percent REAL,
                        disk_free INTEGER,
                        disk_used INTEGER,
                        network_bytes_sent INTEGER,
                        network_bytes_recv INTEGER,
                        process_count INTEGER,
                        load_average TEXT,
                        temperature REAL
                    )
                """)
                
                # Application metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS application_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        active_sessions INTEGER,
                        total_requests INTEGER,
                        failed_requests INTEGER,
                        average_response_time REAL,
                        database_connections INTEGER,
                        cache_hit_rate REAL,
                        websocket_connections INTEGER,
                        file_operations INTEGER,
                        command_executions INTEGER
                    )
                """)
                
                # Alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        severity TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        timestamp TEXT NOT NULL,
                        resolved BOOLEAN DEFAULT FALSE,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        metric_type TEXT,
                        threshold_value REAL,
                        current_value REAL
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_timestamp ON application_metrics(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")

                # Request logs table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS request_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        request_id TEXT,
                        method TEXT,
                        path TEXT,
                        status INTEGER,
                        latency_ms INTEGER
                    )
                    """
                )
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_req_time ON request_logs(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_req_path ON request_logs(path)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_req_method ON request_logs(method)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing metrics database: {e}")
    
    def store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, memory_available,
                        memory_used, disk_usage_percent, disk_free, disk_used,
                        network_bytes_sent, network_bytes_recv, process_count,
                        load_average, temperature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.memory_available,
                    metrics.memory_used,
                    metrics.disk_usage_percent,
                    metrics.disk_free,
                    metrics.disk_used,
                    metrics.network_bytes_sent,
                    metrics.network_bytes_recv,
                    metrics.process_count,
                    json.dumps(metrics.load_average),
                    metrics.temperature
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")
    
    def store_application_metrics(self, metrics: ApplicationMetrics):
        """Store application metrics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO application_metrics (
                        timestamp, active_sessions, total_requests, failed_requests,
                        average_response_time, database_connections, cache_hit_rate,
                        websocket_connections, file_operations, command_executions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.active_sessions,
                    metrics.total_requests,
                    metrics.failed_requests,
                    metrics.average_response_time,
                    metrics.database_connections,
                    metrics.cache_hit_rate,
                    metrics.websocket_connections,
                    metrics.file_operations,
                    metrics.command_executions
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing application metrics: {e}")

    def store_request_log(self, entry: Dict[str, Any]):
        """Persist a single request log entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO request_logs (timestamp, request_id, method, path, status, latency_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.get('timestamp') or datetime.now().isoformat(),
                        entry.get('request_id'),
                        entry.get('method'),
                        entry.get('path'),
                        int(entry.get('status') or 0),
                        int(entry.get('latency_ms') or 0)
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing request log: {e}")

    def get_recent_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent request logs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT timestamp, request_id, method, path, status, latency_ms
                    FROM request_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (int(limit),)
                )
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            logger.error(f"Error retrieving recent requests: {e}")
            return []

    def get_endpoint_breakdown(self, hours: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """Aggregate per-endpoint stats over a time window."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT method, path,
                           COUNT(*) AS count,
                           AVG(latency_ms) AS avg_latency_ms,
                           MIN(latency_ms) AS min_latency_ms,
                           MAX(latency_ms) AS max_latency_ms,
                           SUM(CASE WHEN status >= 400 THEN 1 ELSE 0 END) AS error_count
                    FROM request_logs
                    WHERE timestamp >= ?
                    GROUP BY method, path
                    ORDER BY count DESC
                    LIMIT ?
                    """,
                    (since.isoformat(), int(limit))
                )
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description]
                return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            logger.error(f"Error aggregating endpoint breakdown: {e}")
            return []
    
    def get_metrics_history(self, metric_type: str = "system", 
                           hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for the specified time period."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if metric_type == "system":
                    cursor.execute("""
                        SELECT * FROM system_metrics 
                        WHERE timestamp >= ? 
                        ORDER BY timestamp DESC
                    """, (since.isoformat(),))
                else:
                    cursor.execute("""
                        SELECT * FROM application_metrics 
                        WHERE timestamp >= ? 
                        ORDER BY timestamp DESC
                    """, (since.isoformat(),))
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error retrieving metrics history: {e}")
            return []

class AlertManager:
    """Manage system alerts and notifications."""
    
    def __init__(self, storage: MetricsStorage, config: Dict[str, Any] = None):
        self.storage = storage
        self.config = config or {}
        self.alert_rules = {}
        self.notification_handlers = []
        
        # Default alert thresholds
        self.default_thresholds = {
            "cpu_percent": {"warning": 80.0, "critical": 95.0},
            "memory_percent": {"warning": 85.0, "critical": 95.0},
            "disk_usage_percent": {"warning": 85.0, "critical": 95.0},
            "load_average": {"warning": 2.0, "critical": 5.0},
            "response_time": {"warning": 1000.0, "critical": 5000.0},
            "failed_requests": {"warning": 10, "critical": 50},
            "temperature": {"warning": 70.0, "critical": 85.0}
        }
        
        # Load custom thresholds from config
        if "alert_thresholds" in self.config:
            self.default_thresholds.update(self.config["alert_thresholds"])
    
    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """Add notification handler for alerts."""
        self.notification_handlers.append(handler)
    
    def check_system_metrics(self, metrics: SystemMetrics) -> List[Alert]:
        """Check system metrics against alert thresholds."""
        alerts = []
        
        # Check CPU usage
        cpu_alert = self._check_threshold(
            "cpu_percent", metrics.cpu_percent, metrics.timestamp,
            "High CPU Usage", f"CPU usage is {metrics.cpu_percent:.1f}%"
        )
        if cpu_alert:
            alerts.append(cpu_alert)
        
        # Check memory usage
        memory_alert = self._check_threshold(
            "memory_percent", metrics.memory_percent, metrics.timestamp,
            "High Memory Usage", f"Memory usage is {metrics.memory_percent:.1f}%"
        )
        if memory_alert:
            alerts.append(memory_alert)
        
        # Check disk usage
        disk_alert = self._check_threshold(
            "disk_usage_percent", metrics.disk_usage_percent, metrics.timestamp,
            "High Disk Usage", f"Disk usage is {metrics.disk_usage_percent:.1f}%"
        )
        if disk_alert:
            alerts.append(disk_alert)
        
        # Check load average (1-minute load)
        if metrics.load_average and len(metrics.load_average) > 0:
            load_alert = self._check_threshold(
                "load_average", metrics.load_average[0], metrics.timestamp,
                "High System Load", f"1-minute load average is {metrics.load_average[0]:.2f}"
            )
            if load_alert:
                alerts.append(load_alert)
        
        # Check temperature
        if metrics.temperature:
            temp_alert = self._check_threshold(
                "temperature", metrics.temperature, metrics.timestamp,
                "High Temperature", f"System temperature is {metrics.temperature:.1f}°C"
            )
            if temp_alert:
                alerts.append(temp_alert)
        
        return alerts
    
    def check_application_metrics(self, metrics: ApplicationMetrics) -> List[Alert]:
        """Check application metrics against alert thresholds."""
        alerts = []
        
        # Check response time
        response_time_alert = self._check_threshold(
            "response_time", metrics.average_response_time, metrics.timestamp,
            "High Response Time", f"Average response time is {metrics.average_response_time:.1f}ms"
        )
        if response_time_alert:
            alerts.append(response_time_alert)
        
        # Check failed requests
        if metrics.total_requests > 0:
            failure_rate = (metrics.failed_requests / metrics.total_requests) * 100
            if failure_rate > 10:  # More than 10% failure rate
                alert = Alert(
                    id=f"high_failure_rate_{int(time.time())}",
                    severity="warning" if failure_rate < 25 else "critical",
                    title="High Request Failure Rate",
                    description=f"Request failure rate is {failure_rate:.1f}%",
                    timestamp=metrics.timestamp,
                    metric_type="failure_rate",
                    threshold_value=10.0,
                    current_value=failure_rate
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_threshold(self, metric_name: str, value: float, timestamp: datetime,
                        title: str, description: str) -> Optional[Alert]:
        """Check if a metric exceeds its thresholds."""
        if metric_name not in self.default_thresholds:
            return None
        
        thresholds = self.default_thresholds[metric_name]
        severity = None
        threshold_value = 0.0
        
        if value >= thresholds.get("critical", float('inf')):
            severity = "critical"
            threshold_value = thresholds["critical"]
        elif value >= thresholds.get("warning", float('inf')):
            severity = "warning"
            threshold_value = thresholds["warning"]
        
        if severity:
            alert = Alert(
                id=f"{metric_name}_{severity}_{int(time.time())}",
                severity=severity,
                title=title,
                description=description,
                timestamp=timestamp,
                metric_type=metric_name,
                threshold_value=threshold_value,
                current_value=value
            )
            return alert
        
        return None
    
    def store_alert(self, alert: Alert):
        """Store alert in database."""
        try:
            with sqlite3.connect(self.storage.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO alerts (
                        id, severity, title, description, timestamp,
                        resolved, acknowledged, metric_type, threshold_value, current_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id, alert.severity, alert.title, alert.description,
                    alert.timestamp.isoformat(), alert.resolved, alert.acknowledged,
                    alert.metric_type, alert.threshold_value, alert.current_value
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    def process_alerts(self, alerts: List[Alert]):
        """Process and notify about alerts."""
        for alert in alerts:
            # Store alert
            self.store_alert(alert)
            
            # Send notifications
            for handler in self.notification_handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Error in notification handler: {e}")

class NotificationManager:
    """Handle alert notifications via various channels."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    def send_email_notification(self, alert: Alert):
        """Send email notification for alert."""
        email_config = self.config.get("email", {})
        if not email_config.get("enabled", False):
            return
        
        try:
            # Email functionality would require additional setup
            # For now, just log the alert
            logger.info(f"Email notification would be sent for alert: {alert.title}")
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    def send_webhook_notification(self, alert: Alert):
        """Send webhook notification for alert."""
        webhook_config = self.config.get("webhook", {})
        if not webhook_config.get("enabled", False):
            return
        
        try:
            url = webhook_config.get("url")
            if not url:
                return
            
            payload = {
                "alert": asdict(alert),
                "timestamp": alert.timestamp.isoformat()
            }
            
            headers = webhook_config.get("headers", {"Content-Type": "application/json"})
            timeout = webhook_config.get("timeout", 10)
            
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent for alert: {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")

class MonitoringManager:
    """Main monitoring and analytics manager."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.collector = MetricsCollector()
        self.storage = MetricsStorage()
        self.alert_manager = AlertManager(self.storage, config)
        self.notification_manager = NotificationManager(config)
        
        # Application metrics tracking
        self.app_metrics = {
            "active_sessions": 0,
            "total_requests": 0,
            "failed_requests": 0,
            "response_times": deque(maxlen=1000),
            "database_connections": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "websocket_connections": 0,
            "file_operations": 0,
            "command_executions": 0
        }
        
        # Setup notification handlers
        self.alert_manager.add_notification_handler(
            self.notification_manager.send_email_notification
        )
        self.alert_manager.add_notification_handler(
            self.notification_manager.send_webhook_notification
        )
        
        # Monitoring thread
        self._monitoring_active = False
        self._monitoring_thread = None
        
        # Schedule cleanup tasks
        schedule.every().day.at("02:00").do(self._cleanup_old_metrics)
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self.collector.collect_system_metrics()
                self.storage.store_system_metrics(system_metrics)
                
                # Collect application metrics
                app_metrics = self._get_application_metrics()
                self.storage.store_application_metrics(app_metrics)
                
                # Check for alerts
                system_alerts = self.alert_manager.check_system_metrics(system_metrics)
                app_alerts = self.alert_manager.check_application_metrics(app_metrics)
                
                all_alerts = system_alerts + app_alerts
                if all_alerts:
                    self.alert_manager.process_alerts(all_alerts)
                
                # Run scheduled tasks
                schedule.run_pending()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _get_application_metrics(self) -> ApplicationMetrics:
        """Get current application metrics."""
        avg_response_time = 0.0
        if self.app_metrics["response_times"]:
            avg_response_time = statistics.mean(self.app_metrics["response_times"])
        
        cache_total = self.app_metrics["cache_hits"] + self.app_metrics["cache_misses"]
        cache_hit_rate = 0.0
        if cache_total > 0:
            cache_hit_rate = (self.app_metrics["cache_hits"] / cache_total) * 100
        
        return ApplicationMetrics(
            timestamp=datetime.now(),
            active_sessions=self.app_metrics["active_sessions"],
            total_requests=self.app_metrics["total_requests"],
            failed_requests=self.app_metrics["failed_requests"],
            average_response_time=avg_response_time,
            database_connections=self.app_metrics["database_connections"],
            cache_hit_rate=cache_hit_rate,
            websocket_connections=self.app_metrics["websocket_connections"],
            file_operations=self.app_metrics["file_operations"],
            command_executions=self.app_metrics["command_executions"]
        )
    
    def record_request(self, response_time: float, success: bool = True):
        """Record application request metrics."""
        self.app_metrics["total_requests"] += 1
        if not success:
            self.app_metrics["failed_requests"] += 1
        self.app_metrics["response_times"].append(response_time)
    
    def record_cache_hit(self):
        """Record cache hit."""
        self.app_metrics["cache_hits"] += 1
    
    def record_cache_miss(self):
        """Record cache miss."""
        self.app_metrics["cache_misses"] += 1
    
    def record_file_operation(self):
        """Record file operation."""
        self.app_metrics["file_operations"] += 1
    
    def record_command_execution(self):
        """Record command execution."""
        self.app_metrics["command_executions"] += 1
    
    def update_active_sessions(self, count: int):
        """Update active session count."""
        self.app_metrics["active_sessions"] = count
    
    def update_websocket_connections(self, count: int):
        """Update WebSocket connection count."""
        self.app_metrics["websocket_connections"] = count
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        try:
            # Get recent metrics
            system_metrics = self.storage.get_metrics_history("system", hours=1)
            app_metrics = self.storage.get_metrics_history("application", hours=1)
            
            # Get current system status
            current_system = self.collector.collect_system_metrics()
            current_app = self._get_application_metrics()
            
            return {
                "current": {
                    "system": asdict(current_system),
                    "application": asdict(current_app)
                },
                "history": {
                    "system": system_metrics[-60:],  # Last 60 data points
                    "application": app_metrics[-60:]
                },
                "alerts": self._get_active_alerts(),
                "uptime": str(datetime.now() - self.collector.start_time)
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts."""
        try:
            with sqlite3.connect(self.storage.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM alerts 
                    WHERE resolved = FALSE 
                    ORDER BY timestamp DESC 
                    LIMIT 50
                """)
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics data."""
        try:
            # Keep metrics for 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            
            with sqlite3.connect(self.storage.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up system metrics
                cursor.execute("""
                    DELETE FROM system_metrics 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                # Clean up application metrics
                cursor.execute("""
                    DELETE FROM application_metrics 
                    WHERE timestamp < ?
                """, (cutoff_date.isoformat(),))
                
                # Clean up resolved alerts older than 7 days
                alert_cutoff = datetime.now() - timedelta(days=7)
                cursor.execute("""
                    DELETE FROM alerts 
                    WHERE resolved = TRUE AND timestamp < ?
                """, (alert_cutoff.isoformat(),))

                # Clean up old request logs (keep 7 days)
                req_cutoff = datetime.now() - timedelta(days=7)
                cursor.execute(
                    """
                    DELETE FROM request_logs
                    WHERE timestamp < ?
                    """,
                    (req_cutoff.isoformat(),)
                )
                
                conn.commit()
                logger.info("Old metrics data cleaned up")
                
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")

# Global monitoring instance
monitoring_manager = None

def initialize_monitoring(config: Dict[str, Any] = None) -> MonitoringManager:
    """Initialize monitoring system."""
    global monitoring_manager
    monitoring_manager = MonitoringManager(config)
    return monitoring_manager

def get_monitoring_manager() -> Optional[MonitoringManager]:
    """Get global monitoring manager."""
    return monitoring_manager