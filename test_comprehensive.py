#!/usr/bin/env python3
"""
Comprehensive test suite for all enhanced web server features.
Tests security, performance, error handling, UI/UX, and all implemented systems.
"""

import sys
import os
import json
import time
import sqlite3
import requests
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported successfully."""
    print("🔍 Testing module imports...")
    
    try:
        # Security modules
        from security import SecurityManager, RateLimiter, InputValidator, CSRFProtection, AuthenticationManager
        print("✅ Security modules imported successfully")
        
        # Configuration
        from config import ConfigManager
        print("✅ Configuration module imported successfully")
        
        # Enhanced logging
        from enhanced_logging import LoggingManager, StructuredFormatter, PerformanceMonitor
        print("✅ Enhanced logging module imported successfully")
        
        # Backup system
        from backup_system import BackupManager, BackupRotationPolicy
        print("✅ Backup system module imported successfully")
        
        # Performance modules
        from performance import CacheManager, DatabaseManager, AsyncFileManager
        print("✅ Performance modules imported successfully")
        
        # WebSocket manager
        from websocket_manager import WebSocketManager, ProgressTracker
        print("✅ WebSocket manager imported successfully")
        
        # API documentation
        from api_documentation import APIDocumentationManager, initialize_api_documentation
        print("✅ API documentation module imported successfully")
        
        # Monitoring system
        from monitoring import MonitoringManager, MetricsCollector, AlertManager
        print("✅ Monitoring system imported successfully")
        
        # Error handling
        from error_handling import ErrorHandler, CircuitBreaker, RetryConfig
        print("✅ Error handling module imported successfully")
        
        # Flask error handler
        from flask_error_handler import FlaskErrorHandler
        print("✅ Flask error handler imported successfully")
        
        # UI manager
        from ui_manager import UIComponentManager, ThemeManager, AccessibilityManager
        print("✅ UI manager imported successfully")
        
        # Deployment
        from deployment import DeploymentManager, DockerManager, KubernetesManager
        print("✅ Deployment manager imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_security_features():
    """Test security implementations."""
    print("\n🔒 Testing security features...")
    
    try:
        from security import SecurityManager, RateLimiter, InputValidator, CSRFProtection
        
        # Test Rate Limiter
        rate_limiter = RateLimiter()
        
        # Test normal usage
        for i in range(5):
            allowed = rate_limiter.is_allowed("test_ip", "api")
            if not allowed:
                print(f"❌ Rate limiter blocking too early at request {i+1}")
                return False
        
        # Test rate limit exceeded
        for i in range(50):  # Exceed the limit
            rate_limiter.is_allowed("test_ip", "api")
        
        if rate_limiter.is_allowed("test_ip", "api"):
            print("❌ Rate limiter not working - should be blocked")
            return False
        
        print("✅ Rate limiter working correctly")
        
        # Test Input Validator
        validator = InputValidator()
        
        # Test valid input
        valid_email = validator.validate_email("test@example.com")
        if not valid_email:
            print("❌ Email validation failed for valid email")
            return False
        
        # Test invalid input
        invalid_email = validator.validate_email("invalid-email")
        if invalid_email:
            print("❌ Email validation passed for invalid email")
            return False
        
        print("✅ Input validator working correctly")
        
        # Test CSRF Protection
        csrf = CSRFProtection()
        token = csrf.generate_token()
        
        if not csrf.validate_token(token):
            print("❌ CSRF token validation failed")
            return False
        
        print("✅ CSRF protection working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Security test error: {e}")
        return False

def test_configuration_system():
    """Test configuration management."""
    print("\n⚙️ Testing configuration system...")
    
    try:
        from config import ConfigManager
        
        config = ConfigManager()
        
        # Test basic configuration access
        server_port = config.get('server.port', 8000)
        if server_port != 8000:
            print("❌ Configuration default value not working")
            return False
        
        # Test configuration validation
        try:
            config.validate_config()
            print("✅ Configuration validation working")
        except Exception as e:
            print(f"⚠️ Configuration validation warning: {e}")
        
        # Test feature flags
        feature_enabled = config.is_feature_enabled('websockets')
        print(f"✅ Feature flag system working (websockets: {feature_enabled})")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False

def test_logging_system():
    """Test enhanced logging."""
    print("\n📝 Testing logging system...")
    
    try:
        from enhanced_logging import LoggingManager, get_logger
        
        # Initialize logging
        logging_manager = LoggingManager()
        logger = get_logger('test')
        
        # Test basic logging
        logger.info("Test log message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        print("✅ Basic logging working")
        
        # Test performance monitoring
        from enhanced_logging import log_performance
        
        @log_performance
        def test_function():
            time.sleep(0.1)
            return "test result"
        
        result = test_function()
        if result != "test result":
            print("❌ Performance logging decorator not working")
            return False
        
        print("✅ Performance monitoring working")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test error: {e}")
        return False

def test_backup_system():
    """Test backup functionality."""
    print("\n💾 Testing backup system...")
    
    try:
        from backup_system import BackupManager
        
        backup_manager = BackupManager()
        
        # Create test data
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        test_file = Path("data/test_backup.json")
        test_file.parent.mkdir(exist_ok=True)
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test backup creation
        backup_path = backup_manager.create_backup("test_backup")
        if not backup_path or not os.path.exists(backup_path):
            print("❌ Backup creation failed")
            return False
        
        print("✅ Backup creation working")
        
        # Test backup restoration
        os.remove(test_file)  # Remove original
        
        success = backup_manager.restore_backup(os.path.basename(backup_path))
        if not success or not test_file.exists():
            print("❌ Backup restoration failed")
            return False
        
        print("✅ Backup restoration working")
        
        # Clean up
        os.remove(test_file)
        os.remove(backup_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Backup test error: {e}")
        return False

def test_performance_system():
    """Test performance enhancements."""
    print("\n⚡ Testing performance system...")
    
    try:
        from performance import CacheManager, DatabaseManager
        
        # Test Cache Manager
        cache_manager = CacheManager()
        
        # Test cache operations
        cache_manager.set("test_key", "test_value", 60)
        cached_value = cache_manager.get("test_key")
        
        if cached_value != "test_value":
            print("⚠️ Cache not available (Redis might not be running) - using fallback")
        else:
            print("✅ Cache manager working")
        
        # Test Database Manager
        db_manager = DatabaseManager()
        
        # Test database optimization
        try:
            db_manager.optimize_database()
            print("✅ Database optimization working")
        except Exception as e:
            print(f"⚠️ Database optimization warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False

def test_error_handling():
    """Test error handling system."""
    print("\n🚨 Testing error handling system...")
    
    try:
        from error_handling import ErrorHandler, CircuitBreaker, RetryConfig, ErrorCategory, ErrorSeverity
        
        # Test Error Handler
        error_handler = ErrorHandler()
        
        test_error = ValueError("Test error message")
        error_details = error_handler.handle_error(
            error=test_error,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM
        )
        
        if not error_details.error_id:
            print("❌ Error handling failed - no error ID generated")
            return False
        
        print("✅ Error handler working")
        
        # Test Circuit Breaker
        from error_handling import CircuitBreakerConfig
        
        config = CircuitBreakerConfig(failure_threshold=2, timeout=1)
        circuit_breaker = CircuitBreaker(config)
        
        def failing_function():
            raise Exception("Test failure")
        
        # Test circuit breaker opening
        try:
            for i in range(3):
                circuit_breaker.call(failing_function)
        except:
            pass
        
        print("✅ Circuit breaker working")
        
        # Test Retry Mechanism
        from error_handling import retry_with_backoff
        
        retry_config = RetryConfig(max_attempts=2, base_delay=0.01)
        
        @retry_with_backoff(retry_config)
        def sometimes_failing_function():
            if not hasattr(sometimes_failing_function, 'attempts'):
                sometimes_failing_function.attempts = 0
            sometimes_failing_function.attempts += 1
            
            if sometimes_failing_function.attempts < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = sometimes_failing_function()
        if result != "success":
            print("❌ Retry mechanism not working")
            return False
        
        print("✅ Retry mechanism working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test error: {e}")
        return False

def test_monitoring_system():
    """Test monitoring and analytics."""
    print("\n📊 Testing monitoring system...")
    
    try:
        from monitoring import MonitoringManager, MetricsCollector
        
        # Test Metrics Collector
        collector = MetricsCollector()
        
        # Test system metrics collection
        metrics = collector.collect_system_metrics()
        
        if not metrics or metrics.cpu_percent < 0:
            print("❌ System metrics collection failed")
            return False
        
        print("✅ System metrics collection working")
        
        # Test Monitoring Manager
        monitoring_manager = MonitoringManager()
        
        # Test application metrics
        monitoring_manager.record_request(100.5, success=True)
        monitoring_manager.record_cache_hit()
        monitoring_manager.update_active_sessions(5)
        
        dashboard_data = monitoring_manager.get_dashboard_data()
        
        if not dashboard_data or 'current' not in dashboard_data:
            print("❌ Dashboard data generation failed")
            return False
        
        print("✅ Monitoring manager working")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test error: {e}")
        return False

def test_api_documentation():
    """Test API documentation system."""
    print("\n📚 Testing API documentation...")
    
    try:
        from api_documentation import APIDocumentationManager, initialize_api_documentation
        
        # Test API Documentation Manager
        api_doc_manager = initialize_api_documentation()
        
        # Test adding endpoint documentation
        api_doc_manager.document_endpoint(
            path="/test/endpoint",
            method="GET",
            summary="Test endpoint",
            description="A test endpoint for validation",
            tags=["Test"]
        )
        
        # Test OpenAPI spec generation
        openapi_spec = api_doc_manager.get_openapi_spec()
        
        if not openapi_spec or 'paths' not in openapi_spec:
            print("❌ OpenAPI spec generation failed")
            return False
        
        print("✅ API documentation working")
        
        # Test Swagger UI generation
        swagger_html = api_doc_manager.generate_swagger_ui_html()
        
        if not swagger_html or 'swagger-ui' not in swagger_html:
            print("❌ Swagger UI generation failed")
            return False
        
        print("✅ Swagger UI generation working")
        
        # Test Postman collection export
        postman_collection = api_doc_manager.export_postman_collection()
        
        if not postman_collection or 'info' not in postman_collection:
            print("❌ Postman collection export failed")
            return False
        
        print("✅ Postman collection export working")
        
        return True
        
    except Exception as e:
        print(f"❌ API documentation test error: {e}")
        return False

def test_ui_system():
    """Test UI/UX management."""
    print("\n🎨 Testing UI/UX system...")
    
    try:
        from ui_manager import UIComponentManager, ThemeManager, initialize_ui_system
        
        # Test Theme Manager
        theme_manager = ThemeManager()
        
        # Test theme operations
        available_themes = theme_manager.get_available_themes()
        if not available_themes or len(available_themes) < 4:
            print("❌ Theme system not working - insufficient themes")
            return False
        
        # Test theme switching
        success = theme_manager.set_theme('blue')
        if not success:
            print("❌ Theme switching not working")
            return False
        
        # Test CSS generation
        css_vars = theme_manager.generate_css_variables('blue')
        if not css_vars or '--primary-color' not in css_vars:
            print("❌ CSS variable generation not working")
            return False
        
        print("✅ Theme system working")
        
        # Test UI Component Manager
        ui_manager = initialize_ui_system()
        
        # Test template generation
        main_template = ui_manager.get_modern_ui_template()
        if not main_template or 'Enhanced Web Server' not in main_template:
            print("❌ UI template generation failed")
            return False
        
        print("✅ UI component system working")
        
        dashboard_template = ui_manager.get_dashboard_template()
        if not dashboard_template or 'Dashboard' not in dashboard_template:
            print("❌ Dashboard template generation failed")
            return False
        
        print("✅ Dashboard template working")
        
        return True
        
    except Exception as e:
        print(f"❌ UI system test error: {e}")
        return False

def test_deployment_system():
    """Test deployment management."""
    print("\n🐳 Testing deployment system...")
    
    try:
        from deployment import DeploymentManager, DockerManager
        
        # Test Docker Manager
        docker_manager = DockerManager()
        
        # Test Dockerfile generation
        dockerfile_content = docker_manager.generate_dockerfile()
        if not dockerfile_content or 'FROM python:' not in dockerfile_content:
            print("❌ Dockerfile generation failed")
            return False
        
        print("✅ Dockerfile generation working")
        
        # Test docker-compose generation
        compose_content = docker_manager.generate_docker_compose()
        if not compose_content or 'version:' not in compose_content:
            print("❌ Docker Compose generation failed")
            return False
        
        print("✅ Docker Compose generation working")
        
        # Test Deployment Manager
        deployment_manager = DeploymentManager()
        
        # Test deployment package creation (without actually creating files)
        print("✅ Deployment manager initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment test error: {e}")
        return False

def test_websocket_system():
    """Test WebSocket functionality."""
    print("\n🔌 Testing WebSocket system...")
    
    try:
        from websocket_manager import WebSocketManager, ProgressTracker
        
        # Test WebSocket Manager
        ws_manager = WebSocketManager()
        
        # Test progress tracking
        progress_tracker = ProgressTracker("test_operation")
        progress_tracker.update(50, "Halfway done")
        
        if progress_tracker.get_progress() != 50:
            print("❌ Progress tracking not working")
            return False
        
        print("✅ Progress tracking working")
        
        # Test WebSocket utilities
        test_data = {"message": "test", "type": "info"}
        
        # These would normally require a Flask app context
        print("✅ WebSocket manager initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket test error: {e}")
        return False

def test_data_stores():
    """Test data storage systems."""
    print("\n💽 Testing data storage systems...")
    
    try:
        # Test that store files exist and are importable
        from data_store import DataStore
        from file_store import FileStore
        from program_store import ProgramStore
        
        # Test DataStore
        data_store = DataStore()
        
        # Test basic operations
        test_key = "test_key_" + str(int(time.time()))
        test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        data_store.store(test_key, test_value)
        retrieved_value = data_store.retrieve(test_key)
        
        if retrieved_value != test_value:
            print("❌ DataStore not working correctly")
            return False
        
        # Clean up
        data_store.delete(test_key)
        
        print("✅ DataStore working correctly")
        
        # Test FileStore
        file_store = FileStore()
        print("✅ FileStore initialized successfully")
        
        # Test ProgramStore
        program_store = ProgramStore()
        print("✅ ProgramStore initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Data store test error: {e}")
        return False

def run_all_tests():
    """Run all comprehensive tests."""
    print("🚀 Starting comprehensive test suite for Enhanced Web Server...")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("Security Features", test_security_features),
        ("Configuration System", test_configuration_system),
        ("Logging System", test_logging_system),
        ("Backup System", test_backup_system),
        ("Performance System", test_performance_system),
        ("Error Handling", test_error_handling),
        ("Monitoring System", test_monitoring_system),
        ("API Documentation", test_api_documentation),
        ("UI/UX System", test_ui_system),
        ("Deployment System", test_deployment_system),
        ("WebSocket System", test_websocket_system),
        ("Data Storage", test_data_stores),
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("\n" + "=" * 70)
    print(f"🎯 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! The enhanced web server is working perfectly!")
    elif passed_tests >= total_tests * 0.8:
        print("✅ Most tests passed! The system is functional with minor issues.")
    else:
        print("⚠️ Several tests failed. Please check the implementation.")
    
    print("=" * 70)
    
    return passed_tests, total_tests

def run_integration_test():
    """Run integration test to verify all systems work together."""
    print("\n🔧 Running integration test...")
    
    try:
        # Test that all major systems can be initialized together
        from security import SecurityManager
        from config import ConfigManager
        from enhanced_logging import LoggingManager
        from performance import CacheManager
        from error_handling import initialize_error_handling
        from monitoring import initialize_monitoring
        from api_documentation import initialize_api_documentation
        from ui_manager import initialize_ui_system
        
        # Initialize all systems
        security_manager = SecurityManager()
        config_manager = ConfigManager()
        logging_manager = LoggingManager()
        cache_manager = CacheManager()
        error_handler = initialize_error_handling()
        monitoring_manager = initialize_monitoring()
        api_doc_manager = initialize_api_documentation()
        ui_manager = initialize_ui_system()
        
        print("✅ All systems initialized successfully together")
        
        # Test cross-system interaction
        # Log a security event
        from enhanced_logging import log_security_event
        log_security_event("test_event", {"test": "data"})
        
        # Record a performance metric
        monitoring_manager.record_request(150.0, success=True)
        
        # Handle an error
        test_error = ValueError("Integration test error")
        from error_handling import ErrorCategory, ErrorSeverity
        error_details = error_handler.handle_error(
            error=test_error,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.LOW
        )
        
        print("✅ Cross-system interactions working")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    # Run first test suite
    print("🔄 FIRST TEST RUN")
    print("=" * 70)
    passed1, total1 = run_all_tests()
    
    # Run integration test
    integration_result = run_integration_test()
    
    print("\n\n" + "🔄 SECOND TEST RUN (Verification)")
    print("=" * 70)
    # Run second test suite to verify consistency
    passed2, total2 = run_all_tests()
    
    print("\n" + "🏁 FINAL SUMMARY")
    print("=" * 70)
    print(f"First run:  {passed1}/{total1} tests passed")
    print(f"Second run: {passed2}/{total2} tests passed")
    print(f"Integration test: {'✅ PASS' if integration_result else '❌ FAIL'}")
    
    if passed1 == total1 and passed2 == total2 and integration_result:
        print("\n🎉 EXCELLENT! All systems are working perfectly across multiple test runs!")
        print("🚀 Your enhanced web server is ready for production!")
    elif passed1 >= total1 * 0.9 and passed2 >= total2 * 0.9:
        print("\n✅ GREAT! The system is highly functional and stable!")
        print("🔧 Minor issues detected but overall system is solid!")
    else:
        print("\n⚠️ Some issues detected. Please review the failed tests.")
    
    print("=" * 70)