"""
Program storage module for the web server.
Manages uploaded executable programs and scripts.
"""

import json
import os
import stat
import shutil
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from werkzeug.utils import secure_filename

# Maximum file size for uploads (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# Dangerous file patterns to reject
DANGEROUS_PATTERNS = [
    r'\.\./',  # Path traversal
    r'__import__\s*\(\s*["\']os["\']',  # Python os import
    r'eval\s*\(',  # eval usage
    r'exec\s*\(',  # exec usage
    r'subprocess\.call|subprocess\.run|subprocess\.Popen',  # Direct subprocess
    r'rm\s+-rf\s+/',  # Dangerous rm commands
    r':\(\)\{.*:\|:.*\};:',  # Fork bomb pattern
]

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    '.py', '.sh', '.bash', '.js', '.pl', '.pm', '.rb', '.go', '.rs',
    '.java', '.c', '.cpp', '.h', '.hpp', '.txt', '.md', '.json', '.yaml', 
    '.yml', '.toml', '.cfg', '.conf', '.ini'
}

class ProgramStore:
    """Storage and management for executable programs."""
    
    def __init__(self, programs_dir: str = 'data/programs', max_file_size: int = MAX_FILE_SIZE):
        """
        Initialize the program store.
        
        Args:
            programs_dir: Directory to store programs
            max_file_size: Maximum file size in bytes (default: 100MB)
        """
        self.programs_dir = os.path.abspath(programs_dir)
        self.metadata_file = os.path.join(self.programs_dir, 'programs.json')
        self.max_file_size = max_file_size
        
        # Create programs directory if it doesn't exist
        if not os.path.exists(self.programs_dir):
            os.makedirs(self.programs_dir, mode=0o750)  # Secure permissions
        
        # Load or initialize metadata
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load program metadata from JSON file."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
            else:
                self.metadata = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load program metadata: {e}")
            self.metadata = {}
    
    def _save_metadata(self) -> None:
        """Save program metadata to JSON file."""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save program metadata: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename to sanitize
            
        Returns:
            Safe filename
            
        Raises:
            ValueError: If filename is invalid or dangerous
        """
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")
        
        # Use werkzeug's secure_filename and ensure it's safe
        safe_name = secure_filename(filename)
        if not safe_name:
            safe_name = "unnamed_program"
        
        # Check file extension
        _, ext = os.path.splitext(safe_name.lower())
        if ext and ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{ext}' is not allowed")
        
        return safe_name
    
    def _validate_content(self, content: bytes, filename: str) -> None:
        """
        Validate file content for security issues.
        
        Args:
            content: File content to validate
            filename: Filename for context
            
        Raises:
            ValueError: If content contains dangerous patterns or is too large
        """
        # Check file size
        if len(content) > self.max_file_size:
            raise ValueError(
                f"File size ({len(content)} bytes) exceeds maximum allowed "
                f"size ({self.max_file_size} bytes)"
            )
        
        # Check for dangerous patterns in text files
        try:
            content_str = content.decode('utf-8', errors='ignore')
            for pattern in DANGEROUS_PATTERNS:
                if re.search(pattern, content_str, re.IGNORECASE):
                    raise ValueError(
                        f"File contains potentially dangerous pattern: {pattern}"
                    )
        except UnicodeDecodeError:
            # Binary files - skip pattern check
            pass
    
    def _detect_program_type(self, filename: str, content: bytes) -> str:
        """Detect the type of program based on filename and content."""
        filename_lower = filename.lower()
        
        # Check file extension
        if filename_lower.endswith('.py'):
            return 'python'
        elif filename_lower.endswith(('.sh', '.bash')):
            return 'shell'
        elif filename_lower.endswith('.js'):
            return 'javascript'
        elif filename_lower.endswith(('.pl', '.pm')):
            return 'perl'
        elif filename_lower.endswith('.rb'):
            return 'ruby'
        
        # Check shebang line
        try:
            first_line = content.decode('utf-8').split('\n')[0]
            if first_line.startswith('#!'):
                if 'python' in first_line:
                    return 'python'
                elif 'bash' in first_line or 'sh' in first_line:
                    return 'shell'
                elif 'node' in first_line:
                    return 'javascript'
                elif 'perl' in first_line:
                    return 'perl'
                elif 'ruby' in first_line:
                    return 'ruby'
        except:
            pass
        
        return 'unknown'
    
    def store_program(self, filename: str, content: bytes, description: str = "") -> Dict[str, Any]:
        """
        Store a program file in its own directory.
        
        Args:
            filename: Original filename
            content: File content as bytes
            description: Optional description of the program
            
        Returns:
            Dictionary with program information
            
        Raises:
            ValueError: If file validation fails
        """
        # Validate content first
        self._validate_content(content, filename)
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        # Create a unique program ID based on timestamp
        upload_time = datetime.now()
        program_id = f"program_{int(upload_time.timestamp())}"
        
        # Check if program_id already exists and create unique name if needed
        counter = 1
        original_program_id = program_id
        while program_id in self.metadata:
            program_id = f"{original_program_id}_{counter}"
            counter += 1
        
        # Create program directory with secure permissions
        program_dir = os.path.join(self.programs_dir, program_id)
        os.makedirs(program_dir, mode=0o750, exist_ok=True)
        
        # Store the file inside the program directory
        program_path = os.path.join(program_dir, safe_filename)
        
        # Detect program type
        program_type = self._detect_program_type(filename, content)
        
        # Write program file with secure permissions
        try:
            with open(program_path, 'wb') as f:
                f.write(content)
            
            # Make file executable if it's a script
            if program_type in ['shell', 'python', 'javascript', 'perl', 'ruby']:
                os.chmod(program_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            else:
                # Regular file permissions
                os.chmod(program_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
        except Exception as e:
            # Clean up on error
            if os.path.exists(program_dir):
                shutil.rmtree(program_dir)
            raise ValueError(f"Failed to store program: {str(e)}")
        
        # Store metadata
        program_info = {
            'program_id': program_id,
            'filename': safe_filename,
            'original_filename': filename,
            'description': description,
            'program_type': program_type,
            'type': 'single',
            'size': len(content),
            'upload_time': upload_time.isoformat(),
            'execution_count': 0,
            'last_executed': None,
            'history': []
        }
        
        self.metadata[program_id] = program_info
        self._save_metadata()
        
        return program_info
    
    def store_multiple_files(self, files_data: List[Dict[str, Any]], project_name: str = "", description: str = "") -> Dict[str, Any]:
        """
        Store multiple files as a project.
        
        Args:
            files_data: List of dictionaries with 'filename', 'content', and optional 'relative_path'
            project_name: Name for the project
            description: Optional description of the project
            
        Returns:
            Dictionary with project information
            
        Raises:
            ValueError: If file validation fails or project is too large
        """
        if not files_data:
            raise ValueError("No files provided for project")
        
        # Validate all files first before storing
        total_size = 0
        for file_data in files_data:
            content = file_data['content']
            filename = file_data['filename']
            self._validate_content(content, filename)
            total_size += len(content)
        
        # Check total project size
        if total_size > self.max_file_size * 10:  # 10x limit for projects
            raise ValueError(
                f"Total project size ({total_size} bytes) exceeds maximum "
                f"allowed size ({self.max_file_size * 10} bytes)"
            )
        
        upload_time = datetime.now().isoformat()
        project_id = f"project_{int(datetime.now().timestamp())}"
        
        # Create project directory with secure permissions
        project_dir = os.path.join(self.programs_dir, project_id)
        os.makedirs(project_dir, mode=0o750, exist_ok=True)
        
        stored_files = []
        main_file = None
        
        try:
            for file_data in files_data:
                filename = file_data['filename']
                content = file_data['content']
                relative_path = file_data.get('relative_path', filename)
                
                # Sanitize the relative path
                safe_relative_path = self._sanitize_path(relative_path)
                file_path = os.path.join(project_dir, safe_relative_path)
                
                # Validate path doesn't escape project directory
                real_file_path = os.path.realpath(file_path)
                real_project_dir = os.path.realpath(project_dir)
                if not real_file_path.startswith(real_project_dir):
                    raise ValueError(f"Invalid path: {relative_path} escapes project directory")
                
                # Create directory structure if needed
                file_dir = os.path.dirname(file_path)
                if file_dir != project_dir:
                    os.makedirs(file_dir, mode=0o750, exist_ok=True)
                
                # Write file
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Detect program type and make executable if needed
                program_type = self._detect_program_type(filename, content)
                if program_type in ['shell', 'python', 'javascript', 'perl', 'ruby']:
                    os.chmod(file_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
                    if main_file is None:  # Set first executable as main file
                        main_file = safe_relative_path
                else:
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
                
                file_info = {
                    'filename': filename,
                    'relative_path': safe_relative_path,
                    'program_type': program_type,
                    'size': len(content)
                }
                stored_files.append(file_info)
        except Exception as e:
            # Clean up on error
            if os.path.exists(project_dir):
                shutil.rmtree(project_dir)
            raise ValueError(f"Failed to store project: {str(e)}")
        
        # Store project metadata
        project_info = {
            'project_id': project_id,
            'project_name': project_name or f"Project {project_id}",
            'description': description,
            'type': 'project',
            'files': stored_files,
            'main_file': main_file,
            'total_size': total_size,
            'file_count': len(stored_files),
            'upload_time': upload_time,
            'execution_count': 0,
            'last_executed': None,
            'history': []
        }
        
        self.metadata[project_id] = project_info
        self._save_metadata()
        
        return project_info
    
    def _sanitize_path(self, path: str) -> str:
        """Sanitize a file path for safe storage."""
        # Remove any dangerous path components
        path = path.replace('..', '').replace('\\', '/')
        path_parts = [self._sanitize_filename(part) for part in path.split('/') if part and part != '.']
        return '/'.join(path_parts)
    
    def get_program_list(self) -> List[Dict[str, Any]]:
        """Get list of all stored programs."""
        programs: List[Dict[str, Any]] = []
        stale_ids: List[str] = []

        for program_id, info in list(self.metadata.items()):
            program_path = os.path.join(self.programs_dir, program_id)
            if os.path.exists(program_path):
                programs.append(info.copy())
            else:
                # Defer removal until after iteration to avoid mutating dict mid-loop
                stale_ids.append(program_id)

        if stale_ids:
            for program_id in stale_ids:
                self.metadata.pop(program_id, None)
            self._save_metadata()

        return programs
    
    def get_program_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific program."""
        return self.metadata.get(filename)
    
    def get_program_path(self, filename: str) -> Optional[str]:
        """Get the full path to a program file or project."""
        if filename in self.metadata:
            metadata = self.metadata[filename]
            
            if metadata.get('type') == 'project':
                # For projects, return the project directory
                project_path = os.path.join(self.programs_dir, filename)
                if os.path.exists(project_path):
                    return project_path
            elif metadata.get('type') == 'single':
                # For single programs, return the file inside the program directory
                program_dir = os.path.join(self.programs_dir, filename)
                program_file = os.path.join(program_dir, metadata['filename'])
                if os.path.exists(program_file):
                    return program_file
            else:
                # Legacy support: old programs stored directly
                program_path = os.path.join(self.programs_dir, filename)
                if os.path.exists(program_path):
                    return program_path
        return None
    
    def get_project_main_file(self, project_id: str) -> Optional[str]:
        """Get the main executable file path for a project."""
        if project_id in self.metadata:
            metadata = self.metadata[project_id]
            if metadata.get('type') == 'project' and metadata.get('main_file'):
                project_dir = os.path.join(self.programs_dir, project_id)
                main_file_path = os.path.join(project_dir, metadata['main_file'])
                if os.path.exists(main_file_path):
                    return main_file_path
        return None

    def set_project_main_file(self, project_id: str, relative_path: str) -> bool:
        """Set the main executable file for a project by its relative path."""
        if project_id not in self.metadata:
            return False
        metadata = self.metadata[project_id]
        if metadata.get('type') != 'project':
            return False
        # Normalize and verify the file exists in project files listing
        rel_norm = self._sanitize_path(relative_path)
        files = [f.get('relative_path') for f in metadata.get('files', [])]
        if rel_norm not in files:
            return False
        metadata['main_file'] = rel_norm
        self.metadata[project_id] = metadata
        self._save_metadata()
        return True
    
    def list_project_files(self, project_id: str) -> List[Dict[str, Any]]:
        """List all files in a project."""
        if project_id not in self.metadata:
            return []
        
        metadata = self.metadata[project_id]
        if metadata.get('type') != 'project':
            return []
        
        project_dir = os.path.join(self.programs_dir, project_id)
        if not os.path.exists(project_dir):
            return []
        
        files = []
        for file_info in metadata.get('files', []):
            file_path = os.path.join(project_dir, file_info['relative_path'])
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                file_data = file_info.copy()
                file_data.update({
                    'full_path': file_path,
                    'modified_time': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    'is_executable': bool(stat_info.st_mode & stat.S_IXUSR)
                })
                files.append(file_data)
        
        return files
    
    def delete_program(self, filename: str) -> bool:
        """Delete a program file or project."""
        if filename not in self.metadata:
            return False
        
        metadata = self.metadata[filename]
        
        try:
            if metadata.get('type') in ['project', 'single']:
                # Delete entire program/project directory
                program_path = os.path.join(self.programs_dir, filename)
                if os.path.exists(program_path):
                    shutil.rmtree(program_path)
            else:
                # Legacy support: Delete single file directly
                program_path = os.path.join(self.programs_dir, filename)
                if os.path.exists(program_path):
                    os.remove(program_path)
            
            del self.metadata[filename]
            self._save_metadata()
            return True
        except Exception as e:
            print(f"Error deleting program {filename}: {e}")
            return False
    
    def update_execution_stats(self, filename: str) -> None:
        """Update execution statistics for a program."""
        if filename in self.metadata:
            self.metadata[filename]['execution_count'] += 1
            self.metadata[filename]['last_executed'] = datetime.now().isoformat()
            self._save_metadata()

    def record_execution(self, filename: str, success: bool, exit_code: int, duration_ms: int, command: str = '', output_size: int = 0) -> None:
        """Record an execution event with status and exit code (keeps last 20)."""
        if filename not in self.metadata:
            return
        entry = {
            'timestamp': datetime.now().isoformat(),
            'success': bool(success),
            'exit_code': int(exit_code),
            'duration_ms': int(duration_ms),
            'command': command,
            'output_size': int(output_size)
        }
        meta = self.metadata[filename]
        history = meta.get('history') or []
        history.append(entry)
        # Keep only last 20 entries
        if len(history) > 20:
            history = history[-20:]
        meta['history'] = history
        # Also maintain counters
        meta['execution_count'] = int(meta.get('execution_count', 0)) + 1
        meta['last_executed'] = entry['timestamp']
        self.metadata[filename] = meta
        self._save_metadata()
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information."""
        total_size = 0
        program_count = 0
        project_count = 0
        file_count = 0
        
        for filename, info in self.metadata.items():
            if info.get('type') == 'project':
                project_path = os.path.join(self.programs_dir, filename)
                if os.path.exists(project_path):
                    total_size += info.get('total_size', 0)
                    project_count += 1
                    file_count += info.get('file_count', 0)
            else:
                program_path = os.path.join(self.programs_dir, filename)
                if os.path.exists(program_path):
                    total_size += info.get('size', 0)
                    program_count += 1
                    file_count += 1
        
        return {
            'total_programs': program_count,
            'total_projects': project_count,
            'total_files': file_count,
            'total_size': total_size,
            'storage_path': self.programs_dir
        }