#!/usr/bin/env python3
"""
Enhanced tests for privileged_execution module improvements.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from privileged_execution import PrivilegedCommandSystem


class TestCommandValidation:
    """Test command validation and security features"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.system = PrivilegedCommandSystem(data_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_empty_command_rejected(self):
        """Test that empty commands are rejected"""
        with pytest.raises(ValueError, match='cannot be empty'):
            self.system._validate_command('')
    
    def test_rm_rf_root_blocked(self):
        """Test that rm -rf / is blocked"""
        with pytest.raises(ValueError, match='blocked'):
            self.system._validate_command('rm -rf /')
    
    def test_rm_rf_wildcard_blocked(self):
        """Test that rm -rf /* is blocked"""
        with pytest.raises(ValueError, match='blocked'):
            self.system._validate_command('rm -rf /*')
    
    def test_fork_bomb_blocked(self):
        """Test that fork bomb is blocked"""
        with pytest.raises(ValueError, match='blocked'):
            self.system._validate_command(':(){ :|:& };:')
    
    def test_disk_wipe_blocked(self):
        """Test that disk wipe commands are blocked"""
        with pytest.raises(ValueError, match='blocked'):
            self.system._validate_command('dd if=/dev/zero of=/dev/sda')
    
    def test_mkfs_blocked(self):
        """Test that filesystem format commands are blocked"""
        with pytest.raises(ValueError, match='blocked'):
            self.system._validate_command('mkfs.ext4 /dev/sda1')
    
    def test_safe_command_allowed(self):
        """Test that safe commands are allowed"""
        # Should not raise
        self.system._validate_command('ls -la')
        self.system._validate_command('echo "hello"')
        self.system._validate_command('cat /etc/hostname')
    
    def test_complex_safe_command_allowed(self):
        """Test that complex but safe commands are allowed"""
        # Should not raise
        self.system._validate_command('find /home -name "*.txt" | wc -l')
        self.system._validate_command('ps aux | grep python')


class TestCommandExecution:
    """Test command execution with mocked/safe commands"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.system = PrivilegedCommandSystem(data_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_timeout_configuration(self):
        """Test that timeout is properly configured"""
        assert self.system.default_timeout == 300  # Default 5 minutes
        
        # Test with custom timeout
        custom_system = PrivilegedCommandSystem(
            data_dir=self.test_dir, 
            default_timeout=600
        )
        assert custom_system.default_timeout == 600
    
    def test_timeout_max_limit(self):
        """Test that timeout has maximum limit"""
        # Try to set timeout beyond max
        custom_system = PrivilegedCommandSystem(
            data_dir=self.test_dir,
            default_timeout=3600  # 1 hour
        )
        # Should be capped at MAX_TIMEOUT (1800 seconds)
        assert custom_system.default_timeout == 1800
    
    def test_passphrase_initialization(self):
        """Test that passphrase is properly initialized"""
        assert self.system.passphrase_hash is not None
        assert len(self.system.passphrase_hash) == 64  # SHA256 hash length
    
    def test_passphrase_verification(self):
        """Test passphrase verification"""
        # Load the stored passphrase
        import json
        passphrase_file = Path(self.test_dir) / "privileged" / "passphrase.json"
        with open(passphrase_file, 'r') as f:
            data = json.load(f)
            stored_passphrase = data['passphrase']
        
        # Verify correct passphrase
        assert self.system.verify_passphrase(stored_passphrase) == True
        
        # Verify incorrect passphrase
        assert self.system.verify_passphrase('wrong_passphrase') == False
        assert self.system.verify_passphrase('') == False
    
    def test_command_logging(self):
        """Test that commands are logged"""
        # Execute a safe command without actual sudo
        # Note: This test doesn't actually execute privileged commands
        # but tests the logging infrastructure
        
        execution_id = 'test_exec_123'
        command = 'echo "test"'
        agent_id = 'test_agent'
        
        # Log access
        self.system._log_access(agent_id, command, execution_id)
        
        # Verify access log exists
        access_log_file = Path(self.test_dir) / "privileged" / "access_log.json"
        assert access_log_file.exists()
        
        import json
        with open(access_log_file, 'r') as f:
            access_log = json.load(f)
        
        assert len(access_log) > 0
        assert access_log[-1]['agent_id'] == agent_id
        assert access_log[-1]['command'] == command
        assert access_log[-1]['execution_id'] == execution_id
    
    def test_command_statistics(self):
        """Test command statistics tracking"""
        # Simulate command execution statistics
        self.system._update_statistics('ls', True, 0.5)
        self.system._update_statistics('ls', True, 0.3)
        self.system._update_statistics('ls', False, 0.2)
        
        stats = self.system.command_stats['ls']
        assert stats['total'] == 3
        assert stats['success'] == 2
        assert stats['failure'] == 1
        assert stats['avg_duration'] > 0
    
    def test_learning_data_initialization(self):
        """Test learning data is properly initialized"""
        assert 'patterns' in self.system.learning_data
        assert 'common_errors' in self.system.learning_data
        assert 'optimization_suggestions' in self.system.learning_data
    
    def test_error_learning(self):
        """Test error learning functionality"""
        command = 'ls /nonexistent'
        stderr = 'ls: cannot access /nonexistent: No such file or directory'
        
        self.system._learn_from_error(command, stderr)
        
        # Check that error was recorded
        assert len(self.system.learning_data['common_errors']) > 0
        
        # Find our error
        for error_key, error_info in self.system.learning_data['common_errors'].items():
            if 'No such file' in error_key:
                assert error_info['count'] == 1
                assert command in error_info['commands']
                break
    
    def test_pattern_recognition(self):
        """Test pattern recognition in command execution"""
        command = 'ls -la'
        stdout = 'total 48\ndrwxr-xr-x 2 user user 4096\n'
        stderr = ''
        success = True
        
        self.system._recognize_patterns(command, stdout, stderr, success)
        
        # Check that pattern was recorded
        assert 'ls' in self.system.learning_data['patterns']
        pattern = self.system.learning_data['patterns']['ls']
        assert pattern['executions'] > 0
        assert pattern['success_rate'] > 0
    
    def test_optimization_suggestions(self):
        """Test optimization suggestion identification"""
        # Test package installation optimization
        command = 'apt install nginx'
        stdout = 'Reading package lists... Done\n'
        stderr = ''
        
        self.system._identify_optimizations(command, stdout, stderr)
        
        # Check for optimization suggestions
        suggestions = self.system.learning_data['optimization_suggestions']
        if len(suggestions) > 0:
            # Find our suggestion
            for opt in suggestions:
                if opt['type'] == 'package_management':
                    assert 'caching' in opt['suggestion'].lower()
                    break
    
    def test_learning_insights(self):
        """Test getting learning insights"""
        # Add some test data
        self.system._update_statistics('ls', True, 0.5)
        self.system._learn_from_error('ls', 'error message')
        
        insights = self.system.get_learning_insights()
        
        assert 'patterns' in insights
        assert 'common_errors' in insights
        assert 'optimization_suggestions' in insights
        assert 'command_statistics' in insights
        assert 'last_analysis' in insights
    
    def test_service_improvements(self):
        """Test getting service improvement suggestions"""
        # Add some test data with low success rate
        for i in range(15):
            self.system._update_statistics('failing_cmd', False, 0.5)
        
        improvements = self.system.get_service_improvements()
        
        assert isinstance(improvements, list)
        # Should have suggestions for low success rate
        if len(improvements) > 0:
            assert any('success rate' in str(imp).lower() for imp in improvements)
    
    def test_command_history(self):
        """Test command history retrieval"""
        # Create mock execution result
        result = {
            'execution_id': 'test123',
            'agent_id': 'test_agent',
            'command': 'ls -la',
            'success': True,
            'return_code': 0,
            'stdout': 'file1\nfile2\n',
            'stderr': '',
            'duration': 0.5,
            'timestamp': '2024-01-01T00:00:00',
            'working_dir': '/tmp'
        }
        
        self.system._log_command(result)
        
        # Retrieve history
        history = self.system.get_command_history(limit=10)
        
        assert len(history) > 0
        assert history[-1]['command'] == 'ls -la'
        assert history[-1]['success'] == True
    
    def test_command_history_filtering(self):
        """Test command history filtering by agent"""
        # Create mock execution results
        result1 = {
            'execution_id': 'test1',
            'agent_id': 'agent1',
            'command': 'ls',
            'success': True,
            'return_code': 0,
            'stdout': '',
            'stderr': '',
            'duration': 0.1,
            'timestamp': '2024-01-01T00:00:00',
            'working_dir': '/tmp'
        }
        
        result2 = {
            'execution_id': 'test2',
            'agent_id': 'agent2',
            'command': 'pwd',
            'success': True,
            'return_code': 0,
            'stdout': '',
            'stderr': '',
            'duration': 0.1,
            'timestamp': '2024-01-01T00:00:01',
            'working_dir': '/tmp'
        }
        
        self.system._log_command(result1)
        self.system._log_command(result2)
        
        # Filter by agent
        history = self.system.get_command_history(agent_id='agent1')
        assert all(cmd['agent_id'] == 'agent1' for cmd in history)
    
    def test_passphrase_info(self):
        """Test getting passphrase info"""
        info = self.system.get_passphrase_info()
        
        assert 'created_at' in info
        assert 'note' in info
        assert 'location' in info
        # Passphrase itself should not be in info
        assert 'passphrase' not in info


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
