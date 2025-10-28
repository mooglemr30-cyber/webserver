#!/usr/bin/env python3
"""
Comprehensive test suite for all enhanced features.
Tests security, performance, error handling, UI/UX, and all other implemented systems.
"""

import os
import sys
import json
import time
import unittest
import tempfile
import shutil
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import all our modules
try:
    from security import RateLimiter, InputValidator, CSRFProtection, AuthenticationManager
    from config import config
    from enhanced_logging import logging_manager
    from backup_system import BackupManager
    from performance import CacheManager, DatabaseManager
    from websocket_manager import WebSocketManager
    from api_documentation import APIDocumentationManager
    from monitoring import MetricsCollector, MetricsStorage, AlertManager, MonitoringManager
    from error_handling import ErrorHandler, CircuitBreaker, CircuitBreakerConfig, RetryConfig, retry_with_backoff
    from flask_error_handler import FlaskErrorHandler
    from deployment import DockerManager, KubernetesManager, DeploymentManager
    from ui_manager import ThemeManager, UIComponentManager, AccessibilityManager
    from data_store import DataStore
    from file_store import FileStore
    from program_store import ProgramStore
except ImportError as e:
    print(f"Import error: {e}")
    # Continue with available modules
    pass

class TestSecurityFeatures(unittest.TestCase):
    """Test security enhancements."""
    
    def setUp(self):
        self.rate_limiter = RateLimiter()
        self.input_validator = InputValidator()
        self.csrf_protection = CSRFProtection()
        self.auth_manager = AuthenticationManager()
    
    def test_rate_limiter(self):
        """Test rate limiting functionality."""
        print("Testing rate limiter...")
        
        # Test basic rate limiting
        client_ip = "192.168.1.100"
        endpoint = "test_endpoint"
        
        # Should allow initial requests
        for i in range(10):
            allowed = self.rate_limiter.is_allowed(client_ip, endpoint)
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
        
        # Should block after limit
        blocked = self.rate_limiter.is_allowed(client_ip, endpoint)
        self.assertFalse(blocked, "Request should be blocked after limit")
        
        print("✅ Rate limiter test passed")
    
    def test_input_validator(self):
        """Test input validation."""
        print("Testing input validator...")
        
        # Test email validation
        self.assertTrue(self.input_validator.validate_email("test@example.com"))
        self.assertFalse(self.input_validator.validate_email("invalid-email"))
        
        # Test SQL injection detection
        safe_query = "SELECT * FROM users WHERE id = 1"
        malicious_query = "SELECT * FROM users WHERE id = 1; DROP TABLE users;"
        
        self.assertTrue(self.input_validator.is_safe_sql(safe_query))
        self.assertFalse(self.input_validator.is_safe_sql(malicious_query))
        
        # Test XSS detection
        safe_html = "<p>Hello world</p>"
        malicious_html = "<script>alert('xss')</script>"
        
        self.assertFalse(self.input_validator.contains_xss(safe_html))
        self.assertTrue(self.input_validator.contains_xss(malicious_html))
        
        print("✅ Input validator test passed")
    
    def test_csrf_protection(self):
        """Test CSRF protection."""
        print("Testing CSRF protection...")
        
        # Generate token
        token = self.csrf_protection.generate_token()
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)
        
        # Validate token (should be valid immediately)
        is_valid = self.csrf_protection.validate_token(token)
        self.assertTrue(is_valid)
        
        # Invalid token should fail
        invalid_token = "invalid_token_123"
        is_invalid = self.csrf_protection.validate_token(invalid_token)
        self.assertFalse(is_invalid)
        
        print("✅ CSRF protection test passed")
    
    def test_authentication_manager(self):
        """Test authentication functionality."""
        print("Testing authentication manager...")
        
        username = "testuser"
        password = "testpass123"
        
        # Create user
        success = self.auth_manager.create_user(username, password)
        self.assertTrue(success)
        
        # Verify password
        is_valid = self.auth_manager.verify_password(username, password)
        self.assertTrue(is_valid)
        
        # Wrong password should fail
        is_invalid = self.auth_manager.verify_password(username, "wrongpass")
        self.assertFalse(is_invalid)
        
        print("✅ Authentication manager test passed")

class TestPerformanceFeatures(unittest.TestCase):
    """Test performance and scalability features."""
    
    def setUp(self):
        # Use temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_manager(self):
        """Test caching functionality."""
        print("Testing cache manager...")
        
        # Test with memory cache (Redis might not be available)
        cache_manager = CacheManager(use_redis=False)
        
        # Test basic caching
        key = "test_key"
        value = {"data": "test_value", "timestamp": time.time()}
        
        # Set cache
        cache_manager.set(key, value)
        
        # Get cache
        cached_value = cache_manager.get(key)
        self.assertEqual(cached_value, value)
        
        # Test cache expiration
        cache_manager.set(key, value, ttl=1)  # 1 second TTL
        time.sleep(1.1)  # Wait for expiration
        expired_value = cache_manager.get(key)
        self.assertIsNone(expired_value)
        
        print("✅ Cache manager test passed")
    
    def test_database_manager(self):
        """Test database optimization."""
        print("Testing database manager...")
        
        db_path = os.path.join(self.temp_dir, "test.db")
        db_manager = DatabaseManager(db_path)
        
        # Test connection
        conn = db_manager.get_connection()
        self.assertIsNotNone(conn)
        
        # Test table creation and operations
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test_name",))
        conn.commit()
        
        # Query test data
        cursor.execute("SELECT * FROM test_table")
        results = cursor.fetchall()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "test_name")
        
        conn.close()
        print("✅ Database manager test passed")
    
    def test_websocket_manager(self):
        """Test WebSocket functionality."""
        print("Testing WebSocket manager...")
        
        # Mock Flask-SocketIO
        with patch('websocket_manager.SocketIO') as mock_socketio:
            ws_manager = WebSocketManager()
            
            # Test client management
            client_id = "test_client_123"
            ws_manager.add_client(client_id)
            
            self.assertIn(client_id, ws_manager.connected_clients)
            
            # Test broadcasting
            message = {"type": "test", "data": "hello"}
            ws_manager.broadcast_message("test_event", message)
            
            # Test progress tracking
            operation_id = "upload_123"
            ws_manager.start_progress_tracking(operation_id, "file_upload")
            ws_manager.update_progress(operation_id, 50, "Uploading...")
            ws_manager.complete_progress(operation_id, "Upload complete")
            
            # Remove client
            ws_manager.remove_client(client_id)
            self.assertNotIn(client_id, ws_manager.connected_clients)
        
        print("✅ WebSocket manager test passed")

class TestErrorHandling(unittest.TestCase):
    """Test error handling features."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.error_handler = ErrorHandler(os.path.join(self.temp_dir, "errors.db"))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_error_handler(self):
        """Test error handling and logging."""
        print("Testing error handler...")
        
        from error_handling import ErrorCategory, ErrorSeverity
        
        # Test error handling
        test_error = ValueError("Test error message")
        error_details = self.error_handler.handle_error(
            error=test_error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            request_id="test_request_123"
        )
        
        self.assertIsNotNone(error_details.error_id)
        self.assertEqual(error_details.error_type, "ValueError")
        self.assertEqual(error_details.message, "Test error message")
        self.assertEqual(error_details.category, ErrorCategory.VALIDATION)
        
        # Test error statistics
        stats = self.error_handler.get_error_statistics(hours=1)
        self.assertIsInstance(stats, dict)
        self.assertIn("total_errors", stats)
        
        print("✅ Error handler test passed")
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality."""
        print("Testing circuit breaker...")
        
        from error_handling import CircuitBreakerState
        
        config = CircuitBreakerConfig(failure_threshold=3, timeout=1)
        circuit_breaker = CircuitBreaker(config)
        
        # Test function that sometimes fails
        call_count = 0
        def unreliable_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("Service unavailable")
            return "success"
        
        # Test circuit breaker behavior
        self.assertEqual(circuit_breaker.state, CircuitBreakerState.CLOSED)
        
        # Should fail and eventually open circuit
        for i in range(4):
            try:
                circuit_breaker.call(unreliable_function)
            except Exception:
                pass
        
        self.assertEqual(circuit_breaker.state, CircuitBreakerState.OPEN)
        
        print("✅ Circuit breaker test passed")
    
    def test_retry_mechanism(self):
        """Test retry with backoff."""
        print("Testing retry mechanism...")
        
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        
        @retry_with_backoff(config)
        def flaky_function():
            if not hasattr(flaky_function, 'attempt_count'):
                flaky_function.attempt_count = 0
            flaky_function.attempt_count += 1
            
            if flaky_function.attempt_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        # Should succeed after retries
        result = flaky_function()
        self.assertEqual(result, "success")
        self.assertEqual(flaky_function.attempt_count, 3)
        
        print("✅ Retry mechanism test passed")

class TestMonitoring(unittest.TestCase):
    """Test monitoring and analytics."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_storage = MetricsStorage(os.path.join(self.temp_dir, "metrics.db"))
        self.alert_manager = AlertManager(self.metrics_storage)
        self.metrics_collector = MetricsCollector()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_metrics_collection(self):
        """Test system metrics collection."""
        print("Testing metrics collection...")
        
        # Collect system metrics
        metrics = self.metrics_collector.collect_system_metrics()
        
        self.assertIsNotNone(metrics.timestamp)
        self.assertIsInstance(metrics.cpu_percent, float)
        self.assertIsInstance(metrics.memory_percent, float)
        self.assertIsInstance(metrics.process_count, int)
        
        print("✅ Metrics collection test passed")
    
    def test_metrics_storage(self):
        """Test metrics storage and retrieval."""
        print("Testing metrics storage...")
        
        # Store test metrics
        metrics = self.metrics_collector.collect_system_metrics()
        self.metrics_storage.store_system_metrics(metrics)
        
        # Retrieve metrics
        history = self.metrics_storage.get_metrics_history("system", hours=1)
        self.assertIsInstance(history, list)
        
        print("✅ Metrics storage test passed")
    
    def test_alert_manager(self):
        """Test alert generation."""
        print("Testing alert manager...")
        
        # Create high CPU usage metrics to trigger alert
        from monitoring import SystemMetrics
        
        high_cpu_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=95.0,  # Should trigger critical alert
            memory_percent=50.0,
            memory_available=1000000,
            memory_used=500000,
            disk_usage_percent=50.0,
            disk_free=1000000,
            disk_used=500000,
            network_bytes_sent=1000,
            network_bytes_recv=1000,
            process_count=100,
            load_average=[1.0, 1.0, 1.0]
        )
        
        alerts = self.alert_manager.check_system_metrics(high_cpu_metrics)
        self.assertIsInstance(alerts, list)
        
        # Should generate alert for high CPU
        cpu_alerts = [alert for alert in alerts if alert.metric_type == "cpu_percent"]
        self.assertTrue(len(cpu_alerts) > 0)
        
        print("✅ Alert manager test passed")

class TestAPIDocumentation(unittest.TestCase):
    """Test API documentation features."""
    
    def test_api_documentation_manager(self):
        """Test API documentation generation."""
        print("Testing API documentation...")
        
        api_doc = APIDocumentationManager()
        
        # Test adding tags
        api_doc.add_tag("Test", "Test endpoints")
        
        # Test documenting endpoint
        api_doc.document_endpoint(
            path="/api/test",
            method="GET",
            summary="Test endpoint",
            description="A test endpoint for validation",
            tags=["Test"]
        )
        
        # Test OpenAPI spec generation
        spec = api_doc.get_openapi_spec()
        self.assertIsInstance(spec, dict)
        self.assertIn("openapi", spec)
        self.assertIn("paths", spec)
        self.assertIn("/api/test", spec["paths"])
        
        # Test Swagger UI HTML generation
        html = api_doc.generate_swagger_ui_html()
        self.assertIsInstance(html, str)
        self.assertIn("swagger-ui", html)
        
        # Test Postman collection export
        collection = api_doc.export_postman_collection()
        self.assertIsInstance(collection, dict)
        self.assertIn("info", collection)
        
        print("✅ API documentation test passed")

class TestUIManager(unittest.TestCase):
    """Test UI/UX features."""
    
    def test_theme_manager(self):
        """Test theme management."""
        print("Testing theme manager...")
        
        theme_manager = ThemeManager()
        
        # Test getting themes
        dark_theme = theme_manager.get_theme("dark")
        self.assertIsInstance(dark_theme, dict)
        self.assertIn("primary_color", dark_theme)
        
        # Test setting theme
        success = theme_manager.set_theme("light")
        self.assertTrue(success)
        self.assertEqual(theme_manager.current_theme, "light")
        
        # Test invalid theme
        invalid = theme_manager.set_theme("nonexistent")
        self.assertFalse(invalid)
        
        # Test CSS generation
        css = theme_manager.generate_css_variables("dark")
        self.assertIsInstance(css, str)
        self.assertIn(":root", css)
        self.assertIn("--primary-color", css)
        
        print("✅ Theme manager test passed")
    
    def test_ui_component_manager(self):
        """Test UI component generation."""
        print("Testing UI component manager...")
        
        theme_manager = ThemeManager()
        ui_manager = UIComponentManager(theme_manager)
        
        # Test template generation
        template = ui_manager.get_modern_ui_template()
        self.assertIsInstance(template, str)
        self.assertIn("<!DOCTYPE html>", template)
        self.assertIn("Enhanced Web Server", template)
        
        # Test dashboard template
        dashboard = ui_manager.get_dashboard_template()
        self.assertIsInstance(dashboard, str)
        self.assertIn("dashboard", dashboard)
        
        print("✅ UI component manager test passed")
    
    def test_accessibility_manager(self):
        """Test accessibility features."""
        print("Testing accessibility manager...")
        
        accessibility = AccessibilityManager()
        
        # Test accessibility CSS
        css = accessibility.get_accessibility_css()
        self.assertIsInstance(css, str)
        self.assertIn("prefers-contrast", css)
        self.assertIn("prefers-reduced-motion", css)
        
        # Test accessibility JavaScript
        js = accessibility.get_accessibility_js()
        self.assertIsInstance(js, str)
        self.assertIn("AccessibilityManager", js)
        self.assertIn("keyboard-navigation", js)
        
        print("✅ Accessibility manager test passed")

class TestDataStores(unittest.TestCase):
    """Test data storage functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_data_store(self):
        """Test basic data storage."""
        print("Testing data store...")
        
        data_file = os.path.join(self.temp_dir, "test_data.json")
        store = DataStore(data_file)
        
        # Test set and get
        store.set("test_key", "test_value")
        value = store.get("test_key")
        self.assertEqual(value, "test_value")
        
        # Test complex data
        complex_data = {"name": "test", "values": [1, 2, 3], "nested": {"a": 1}}
        store.set("complex", complex_data)
        retrieved = store.get("complex")
        self.assertEqual(retrieved, complex_data)
        
        # Test deletion
        deleted = store.delete("test_key")
        self.assertTrue(deleted)
        self.assertIsNone(store.get("test_key"))
        
        # Test get_all
        all_data = store.get_all()
        self.assertIn("complex", all_data)
        self.assertNotIn("test_key", all_data)
        
        print("✅ Data store test passed")
    
    def test_file_store(self):
        """Test file storage functionality."""
        print("Testing file store...")
        
        files_dir = os.path.join(self.temp_dir, "files")
        os.makedirs(files_dir, exist_ok=True)
        
        file_store = FileStore(files_dir)
        
        # Create test file
        test_content = b"This is test file content"
        test_filename = "test.txt"
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(test_content)
            temp_file_path = temp_file.name
        
        try:
            # Test file storage
            stored_filename = file_store.store_file(temp_file_path, test_filename)
            self.assertIsNotNone(stored_filename)
            
            # Test file retrieval
            stored_path = file_store.get_file_path(stored_filename)
            self.assertTrue(os.path.exists(stored_path))
            
            with open(stored_path, 'rb') as f:
                retrieved_content = f.read()
            self.assertEqual(retrieved_content, test_content)
            
            # Test file listing
            files = file_store.list_files()
            self.assertIsInstance(files, list)
            
            # Test file deletion
            deleted = file_store.delete_file(stored_filename)
            self.assertTrue(deleted)
            
        finally:
            os.unlink(temp_file_path)
        
        print("✅ File store test passed")

class TestDeployment(unittest.TestCase):
    """Test deployment features."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_docker_manager(self):
        """Test Docker deployment files generation."""
        print("Testing Docker manager...")
        
        docker_manager = DockerManager(self.temp_dir)
        
        # Test Dockerfile generation
        dockerfile_content = docker_manager.generate_dockerfile()
        self.assertIsInstance(dockerfile_content, str)
        self.assertIn("FROM python:", dockerfile_content)
        self.assertIn("WORKDIR /app", dockerfile_content)
        
        # Test .dockerignore generation
        dockerignore_content = docker_manager.generate_dockerignore()
        self.assertIsInstance(dockerignore_content, str)
        self.assertIn(".git", dockerignore_content)
        
        # Test docker-compose generation
        compose_content = docker_manager.generate_docker_compose()
        self.assertIsInstance(compose_content, str)
        self.assertIn("version:", compose_content)
        self.assertIn("services:", compose_content)
        
        print("✅ Docker manager test passed")
    
    def test_kubernetes_manager(self):
        """Test Kubernetes deployment files generation."""
        print("Testing Kubernetes manager...")
        
        k8s_manager = KubernetesManager(self.temp_dir)
        
        # Test manifest creation
        success = k8s_manager.create_k8s_manifests()
        self.assertTrue(success)
        
        # Check if files were created
        k8s_dir = os.path.join(self.temp_dir, "k8s")
        self.assertTrue(os.path.exists(k8s_dir))
        
        expected_files = [
            "namespace.yaml",
            "configmap.yaml",
            "secret.yaml",
            "deployment.yaml",
            "service.yaml",
            "ingress.yaml",
            "hpa.yaml",
            "redis.yaml"
        ]
        
        for filename in expected_files:
            filepath = os.path.join(k8s_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"Missing file: {filename}")
        
        print("✅ Kubernetes manager test passed")

def run_comprehensive_tests():
    """Run all tests and provide a comprehensive report."""
    print("🚀 Starting Comprehensive Feature Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestSecurityFeatures,
        TestPerformanceFeatures,
        TestErrorHandling,
        TestMonitoring,
        TestAPIDocumentation,
        TestUIManager,
        TestDataStores,
        TestDeployment
    ]
    
    for test_class in test_classes:
        tests = test_loader.loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 Test Suite Summary")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    
    if failures > 0:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if errors > 0:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
    print(f"\n🎯 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("🎉 EXCELLENT! All systems are working perfectly!")
    elif success_rate >= 80:
        print("✅ GOOD! Most systems are working well with minor issues.")
    elif success_rate >= 60:
        print("⚠️  FAIR! Some systems need attention.")
    else:
        print("🚨 POOR! Multiple systems require fixes.")
    
    return result

if __name__ == "__main__":
    # Run the comprehensive test suite
    result = run_comprehensive_tests()
    
    # Exit with appropriate code
    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)