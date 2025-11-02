#!/usr/bin/env python3
"""
Enhanced tests for program_store module improvements.
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from program_store import ProgramStore


class TestProgramStoreValidation:
    """Test input validation and security features"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.store = ProgramStore(programs_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_valid_python_upload(self):
        """Test uploading a valid Python program"""
        content = b"#!/usr/bin/env python3\nprint('Hello World')\n"
        result = self.store.store_program('test.py', content, 'Test program')
        
        assert result['program_type'] == 'python'
        assert result['filename'] == 'test.py'
        assert result['size'] == len(content)
        assert 'program_id' in result
    
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        # Create content larger than limit
        content = b'X' * (self.store.max_file_size + 1)
        
        with pytest.raises(ValueError, match='exceeds maximum allowed size'):
            self.store.store_program('large.py', content)
    
    def test_empty_file_rejected(self):
        """Test that empty files are rejected"""
        with pytest.raises(ValueError):
            self.store.store_program('empty.py', b'')
    
    def test_invalid_extension_rejected(self):
        """Test that invalid extensions are rejected"""
        content = b'malicious content'
        
        with pytest.raises(ValueError, match='not allowed'):
            self.store.store_program('malware.exe', content)
    
    def test_path_traversal_blocked(self):
        """Test path traversal attempt is blocked"""
        content = b'#!/bin/bash\necho "test"\n'
        
        with pytest.raises(ValueError):
            self.store.store_program('../../../etc/passwd', content)
    
    def test_dangerous_pattern_eval(self):
        """Test dangerous eval pattern is detected"""
        content = b'#!/usr/bin/env python3\neval(input("Enter code: "))\n'
        
        with pytest.raises(ValueError, match='dangerous pattern'):
            self.store.store_program('dangerous.py', content)
    
    def test_dangerous_pattern_exec(self):
        """Test dangerous exec pattern is detected"""
        content = b'#!/usr/bin/env python3\nexec("import os; os.system(\'rm -rf /\')")\n'
        
        with pytest.raises(ValueError, match='dangerous pattern'):
            self.store.store_program('dangerous.py', content)
    
    def test_fork_bomb_blocked(self):
        """Test fork bomb pattern is blocked"""
        content = b'#!/bin/bash\n:(){ :|:& };:\n'
        
        with pytest.raises(ValueError, match='dangerous pattern'):
            self.store.store_program('forkbomb.sh', content)
    
    def test_rm_rf_root_blocked(self):
        """Test dangerous rm command is blocked"""
        content = b'#!/bin/bash\nrm -rf /\n'
        
        with pytest.raises(ValueError, match='dangerous pattern'):
            self.store.store_program('dangerous.sh', content)
    
    def test_safe_subprocess_allowed(self):
        """Test that safe subprocess usage is allowed"""
        # This should pass - not matching the dangerous pattern
        content = b'#!/usr/bin/env python3\n# This is a comment about subprocess\nprint("test")\n'
        result = self.store.store_program('safe.py', content)
        assert 'program_id' in result
    
    def test_valid_shell_script(self):
        """Test valid shell script upload"""
        content = b'#!/bin/bash\necho "Hello from bash"\nls -la\n'
        result = self.store.store_program('script.sh', content, 'Test script')
        
        assert result['program_type'] == 'shell'
        assert 'program_id' in result
    
    def test_valid_javascript_upload(self):
        """Test valid JavaScript upload"""
        content = b'#!/usr/bin/env node\nconsole.log("Hello from Node");\n'
        result = self.store.store_program('script.js', content)
        
        assert result['program_type'] == 'javascript'
        assert 'program_id' in result
    
    def test_program_permissions(self):
        """Test that executable permissions are set correctly"""
        content = b'#!/usr/bin/env python3\nprint("test")\n'
        result = self.store.store_program('test.py', content)
        
        program_path = self.store.get_program_path(result['program_id'])
        assert program_path is not None
        
        # Check that file is executable
        assert os.access(program_path, os.X_OK)
    
    def test_metadata_persistence(self):
        """Test that metadata persists across store instances"""
        content = b'#!/usr/bin/env python3\nprint("test")\n'
        result = self.store.store_program('test.py', content)
        program_id = result['program_id']
        
        # Create new store instance
        new_store = ProgramStore(programs_dir=self.test_dir)
        
        # Verify program still exists
        programs = new_store.get_program_list()
        assert len(programs) == 1
        assert programs[0]['program_id'] == program_id


class TestProjectUpload:
    """Test project upload functionality"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.store = ProgramStore(programs_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_multi_file_project(self):
        """Test uploading a multi-file project"""
        files_data = [
            {
                'filename': 'main.py',
                'content': b'#!/usr/bin/env python3\nfrom utils import helper\nhelper()\n',
                'relative_path': 'main.py'
            },
            {
                'filename': 'utils.py',
                'content': b'def helper():\n    print("Helper function")\n',
                'relative_path': 'utils.py'
            }
        ]
        
        result = self.store.store_multiple_files(files_data, 'Test Project', 'A test project')
        
        assert result['type'] == 'project'
        assert result['file_count'] == 2
        assert result['main_file'] == 'main.py'
        assert 'project_id' in result
    
    def test_project_directory_structure(self):
        """Test that project maintains directory structure"""
        files_data = [
            {
                'filename': 'main.py',
                'content': b'print("main")',
                'relative_path': 'src/main.py'
            },
            {
                'filename': 'config.json',
                'content': b'{"key": "value"}',
                'relative_path': 'config/config.json'
            }
        ]
        
        result = self.store.store_multiple_files(files_data, 'Structured Project')
        
        project_path = self.store.get_program_path(result['project_id'])
        assert os.path.exists(os.path.join(project_path, 'src', 'main.py'))
        assert os.path.exists(os.path.join(project_path, 'config', 'config.json'))
    
    def test_project_size_limit(self):
        """Test project total size limit"""
        # Create files that exceed individual file limit
        # (Individual files are validated first, so we test that)
        large_content = b'X' * (self.store.max_file_size + 1)
        files_data = [
            {'filename': 'file1.txt', 'content': large_content}
        ]
        
        with pytest.raises(ValueError, match='File size.*exceeds maximum'):
            self.store.store_multiple_files(files_data, 'Too Large')
    
    def test_project_path_escape_blocked(self):
        """Test that path traversal in projects is blocked"""
        files_data = [
            {
                'filename': 'evil.py',
                'content': b'print("test")',
                'relative_path': '../../../etc/evil.py'
            }
        ]
        
        with pytest.raises(ValueError, match='Path contains invalid traversal characters'):
            self.store.store_multiple_files(files_data, 'Evil Project')
    
    def test_empty_project_rejected(self):
        """Test that empty projects are rejected"""
        with pytest.raises(ValueError, match='No files provided'):
            self.store.store_multiple_files([], 'Empty Project')
    
    def test_project_file_validation(self):
        """Test that individual files in project are validated"""
        files_data = [
            {
                'filename': 'good.py',
                'content': b'print("good")'
            },
            {
                'filename': 'bad.py',
                'content': b'eval(input())'  # Dangerous pattern
            }
        ]
        
        with pytest.raises(ValueError, match='dangerous pattern'):
            self.store.store_multiple_files(files_data, 'Mixed Project')


class TestProgramExecution:
    """Test program execution statistics and history"""
    
    def setup_method(self):
        """Create temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.store = ProgramStore(programs_dir=self.test_dir)
    
    def teardown_method(self):
        """Clean up temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_execution_stats_update(self):
        """Test that execution stats are updated"""
        content = b'#!/usr/bin/env python3\nprint("test")\n'
        result = self.store.store_program('test.py', content)
        program_id = result['program_id']
        
        # Initial stats
        info = self.store.get_program_info(program_id)
        assert info['execution_count'] == 0
        
        # Update stats
        self.store.update_execution_stats(program_id)
        
        # Check updated stats
        info = self.store.get_program_info(program_id)
        assert info['execution_count'] == 1
        assert info['last_executed'] is not None
    
    def test_execution_history_recording(self):
        """Test execution history recording"""
        content = b'#!/usr/bin/env python3\nprint("test")\n'
        result = self.store.store_program('test.py', content)
        program_id = result['program_id']
        
        # Record executions
        self.store.record_execution(
            program_id, 
            success=True, 
            exit_code=0, 
            duration_ms=100,
            command='python3 test.py',
            output_size=50
        )
        
        info = self.store.get_program_info(program_id)
        assert len(info['history']) == 1
        assert info['history'][0]['success'] == True
        assert info['history'][0]['exit_code'] == 0
    
    def test_execution_history_limit(self):
        """Test that execution history is limited to last 20"""
        content = b'#!/usr/bin/env python3\nprint("test")\n'
        result = self.store.store_program('test.py', content)
        program_id = result['program_id']
        
        # Record 25 executions
        for i in range(25):
            self.store.record_execution(
                program_id,
                success=True,
                exit_code=0,
                duration_ms=100,
                command=f'run {i}'
            )
        
        info = self.store.get_program_info(program_id)
        assert len(info['history']) == 20  # Only last 20 kept


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
