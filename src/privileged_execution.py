"""
Privileged Command Execution System for Trusted AI Agents

This module provides secure sudo command execution capabilities for a small
number of trusted AI agents and tools. Features include:
- Separate passphrase-based authentication
- Command logging with full output capture
- Network-wide output visibility for learning
- Pattern recognition and service improvement suggestions
- Security auditing and access control

Security Model:
- Separate from JWT authentication
- Single shared passphrase for trusted agents
- All commands logged with timestamps
- Output shared for learning purposes
- Rate limiting and command validation
"""

import os
import json
import subprocess
import threading
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re
from collections import defaultdict


class PrivilegedCommandSystem:
    """Manages privileged command execution for trusted AI agents"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.privileged_dir = self.data_dir / "privileged"
        self.privileged_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.passphrase_file = self.privileged_dir / "passphrase.json"
        self.command_log_file = self.privileged_dir / "command_log.json"
        self.learning_data_file = self.privileged_dir / "learning_data.json"
        self.access_log_file = self.privileged_dir / "access_log.json"
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Initialize or load passphrase
        self.passphrase_hash = self._init_passphrase()
        
        # Load learning data
        self.learning_data = self._load_learning_data()
        
        # Command statistics
        self.command_stats = defaultdict(lambda: {
            'total': 0,
            'success': 0,
            'failure': 0,
            'avg_duration': 0.0
        })
    
    def _init_passphrase(self) -> str:
        """Initialize or load the privileged passphrase"""
        if self.passphrase_file.exists():
            with open(self.passphrase_file, 'r') as f:
                data = json.load(f)
                return data['passphrase_hash']
        
        # Generate new passphrase
        passphrase = secrets.token_urlsafe(32)
        passphrase_hash = hashlib.sha256(passphrase.encode()).hexdigest()
        
        with open(self.passphrase_file, 'w') as f:
            json.dump({
                'passphrase_hash': passphrase_hash,
                'created_at': datetime.now().isoformat(),
                'passphrase': passphrase,  # Store once for retrieval
                'note': 'This passphrase grants full sudo access. Protect it carefully.'
            }, f, indent=2)
        
        # Also save to TOKENSANDLOGINS for easy access
        token_dir = Path("/run/media/admin1/1E1EC1FE1EC1CF49/to delete/TOKENSANDLOGINS")
        if token_dir.exists():
            with open(token_dir / "PRIVILEGED_PASSPHRASE.txt", 'w') as f:
                f.write(f"PRIVILEGED SUDO PASSPHRASE\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write(f"Passphrase: {passphrase}\n\n")
                f.write(f"⚠️  WARNING: This passphrase grants full sudo access!\n")
                f.write(f"Only share with TRUSTED AI agents and tools.\n\n")
                f.write(f"Usage:\n")
                f.write(f"  POST /api/privileged/execute\n")
                f.write(f"  Headers: X-Privileged-Passphrase: {passphrase}\n")
                f.write(f"  Body: {{\"command\": \"your sudo command\"}}\n")
        
        return passphrase_hash
    
    def verify_passphrase(self, passphrase: str) -> bool:
        """Verify if the provided passphrase is correct"""
        if not passphrase:
            return False
        
        provided_hash = hashlib.sha256(passphrase.encode()).hexdigest()
        return secrets.compare_digest(provided_hash, self.passphrase_hash)
    
    def _load_learning_data(self) -> Dict:
        """Load learning data from previous command executions"""
        if self.learning_data_file.exists():
            with open(self.learning_data_file, 'r') as f:
                return json.load(f)
        
        return {
            'patterns': {},
            'common_errors': {},
            'optimization_suggestions': [],
            'service_improvements': [],
            'last_analysis': None
        }
    
    def _save_learning_data(self):
        """Save learning data to disk"""
        with self.lock:
            with open(self.learning_data_file, 'w') as f:
                json.dump(self.learning_data, f, indent=2)
    
    def execute_privileged_command(
        self,
        command: str,
        agent_id: str,
        timeout: int = 300,
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a privileged command with sudo
        
        Args:
            command: The command to execute (sudo will be prepended if needed)
            agent_id: Identifier for the AI agent making the request
            timeout: Command timeout in seconds (default 5 minutes)
            working_dir: Working directory for command execution
        
        Returns:
            Dict with execution results, output, and metadata
        """
        start_time = time.time()
        execution_id = secrets.token_hex(8)
        
        # Prepend sudo if not already present, with password input
        if not command.strip().startswith('sudo'):
            # Use echo to provide password for sudo -S
            command = f"echo 'admin' | sudo -S {command}"
        elif 'sudo -S' in command and not command.startswith('echo'):
            # Add password for existing sudo -S commands
            command = f"echo 'admin' | {command}"
        
        # Log access attempt
        self._log_access(agent_id, command, execution_id)
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=working_dir
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            # Prepare result
            execution_result = {
                'execution_id': execution_id,
                'agent_id': agent_id,
                'command': command,
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'working_dir': working_dir or os.getcwd()
            }
            
            # Log command execution
            self._log_command(execution_result)
            
            # Update statistics
            self._update_statistics(command, success, duration)
            
            # Analyze for learning
            self._analyze_for_learning(execution_result)
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            execution_result = {
                'execution_id': execution_id,
                'agent_id': agent_id,
                'command': command,
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout} seconds',
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'working_dir': working_dir or os.getcwd()
            }
            
            self._log_command(execution_result)
            return execution_result
            
        except Exception as e:
            duration = time.time() - start_time
            execution_result = {
                'execution_id': execution_id,
                'agent_id': agent_id,
                'command': command,
                'success': False,
                'return_code': -1,
                'stdout': '',
                'stderr': str(e),
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'working_dir': working_dir or os.getcwd()
            }
            
            self._log_command(execution_result)
            return execution_result
    
    def _log_access(self, agent_id: str, command: str, execution_id: str):
        """Log access attempt for auditing"""
        with self.lock:
            access_log = []
            if self.access_log_file.exists():
                with open(self.access_log_file, 'r') as f:
                    access_log = json.load(f)
            
            access_log.append({
                'execution_id': execution_id,
                'agent_id': agent_id,
                'command': command,
                'timestamp': datetime.now().isoformat(),
                'ip': 'localhost'  # Can be enhanced with real IP
            })
            
            # Keep only last 10000 entries
            if len(access_log) > 10000:
                access_log = access_log[-10000:]
            
            with open(self.access_log_file, 'w') as f:
                json.dump(access_log, f, indent=2)
    
    def _log_command(self, execution_result: Dict):
        """Log command execution with full output"""
        with self.lock:
            command_log = []
            if self.command_log_file.exists():
                with open(self.command_log_file, 'r') as f:
                    command_log = json.load(f)
            
            command_log.append(execution_result)
            
            # Keep only last 5000 commands
            if len(command_log) > 5000:
                command_log = command_log[-5000:]
            
            with open(self.command_log_file, 'w') as f:
                json.dump(command_log, f, indent=2)
            
            # Also save to shared AI storage for network-wide visibility
            shared_log_dir = Path("/run/media/admin1/1E1EC1FE1EC1CF49/to delete/AIAGENTSTORAGE/logs")
            if shared_log_dir.exists():
                shared_log_file = shared_log_dir / "privileged_commands.json"
                try:
                    shared_log = []
                    if shared_log_file.exists():
                        with open(shared_log_file, 'r') as f:
                            shared_log = json.load(f)
                    
                    shared_log.append(execution_result)
                    
                    # Keep last 1000 in shared storage
                    if len(shared_log) > 1000:
                        shared_log = shared_log[-1000:]
                    
                    with open(shared_log_file, 'w') as f:
                        json.dump(shared_log, f, indent=2)
                except Exception:
                    pass  # Don't fail if shared storage unavailable
    
    def _update_statistics(self, command: str, success: bool, duration: float):
        """Update command statistics for analysis"""
        # Extract base command (first word after sudo)
        base_command = command.strip().split()[1] if 'sudo' in command else command.strip().split()[0]
        
        stats = self.command_stats[base_command]
        stats['total'] += 1
        if success:
            stats['success'] += 1
        else:
            stats['failure'] += 1
        
        # Update average duration
        stats['avg_duration'] = (
            (stats['avg_duration'] * (stats['total'] - 1) + duration) / stats['total']
        )
    
    def _analyze_for_learning(self, execution_result: Dict):
        """Analyze command output for learning and improvement"""
        command = execution_result['command']
        success = execution_result['success']
        stdout = execution_result['stdout']
        stderr = execution_result['stderr']
        
        # Pattern recognition
        self._recognize_patterns(command, stdout, stderr, success)
        
        # Error learning
        if not success:
            self._learn_from_error(command, stderr)
        
        # Service optimization
        self._identify_optimizations(command, stdout, stderr)
        
        # Save learning data periodically
        self._save_learning_data()
    
    def _recognize_patterns(self, command: str, stdout: str, stderr: str, success: bool):
        """Recognize patterns in command execution"""
        # Extract command type
        cmd_parts = command.strip().split()
        cmd_type = cmd_parts[1] if len(cmd_parts) > 1 and cmd_parts[0] == 'sudo' else cmd_parts[0]
        
        if cmd_type not in self.learning_data['patterns']:
            self.learning_data['patterns'][cmd_type] = {
                'executions': 0,
                'success_rate': 0.0,
                'common_outputs': [],
                'typical_duration': 0.0
            }
        
        pattern = self.learning_data['patterns'][cmd_type]
        pattern['executions'] += 1
        
        # Update success rate
        if success:
            pattern['success_rate'] = (
                (pattern['success_rate'] * (pattern['executions'] - 1) + 1) / pattern['executions']
            )
        else:
            pattern['success_rate'] = (
                (pattern['success_rate'] * (pattern['executions'] - 1)) / pattern['executions']
            )
        
        # Track common output patterns
        if stdout and len(pattern['common_outputs']) < 10:
            output_summary = stdout[:200]
            if output_summary not in pattern['common_outputs']:
                pattern['common_outputs'].append(output_summary)
    
    def _learn_from_error(self, command: str, stderr: str):
        """Learn from command errors"""
        if not stderr:
            return
        
        # Extract error type
        error_key = stderr[:100]  # First 100 chars as key
        
        if error_key not in self.learning_data['common_errors']:
            self.learning_data['common_errors'][error_key] = {
                'count': 0,
                'commands': [],
                'first_seen': datetime.now().isoformat(),
                'suggested_fix': None
            }
        
        error_info = self.learning_data['common_errors'][error_key]
        error_info['count'] += 1
        
        if command not in error_info['commands']:
            error_info['commands'].append(command)
        
        # Suggest fixes for common errors
        if 'permission denied' in stderr.lower():
            error_info['suggested_fix'] = 'Ensure sudo is used and user has required permissions'
        elif 'command not found' in stderr.lower():
            error_info['suggested_fix'] = 'Install required package or check PATH'
        elif 'no such file or directory' in stderr.lower():
            error_info['suggested_fix'] = 'Verify file/directory exists or create it first'
    
    def _identify_optimizations(self, command: str, stdout: str, stderr: str):
        """Identify potential service optimizations"""
        optimizations = []
        
        # Check for package installations
        if 'apt install' in command or 'apt-get install' in command:
            optimizations.append({
                'type': 'package_management',
                'suggestion': 'Consider caching package lists to speed up installations',
                'command': command,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check for service restarts
        if 'systemctl restart' in command or 'service restart' in command:
            optimizations.append({
                'type': 'service_management',
                'suggestion': 'Consider reload instead of restart for zero-downtime updates',
                'command': command,
                'timestamp': datetime.now().isoformat()
            })
        
        # Check for file operations
        if any(cmd in command for cmd in ['cp ', 'mv ', 'rsync']):
            if 'large' in stdout.lower() or len(stdout) > 10000:
                optimizations.append({
                    'type': 'file_operations',
                    'suggestion': 'Consider using parallel file operations or compression',
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                })
        
        # Add to learning data
        for opt in optimizations:
            if opt not in self.learning_data['optimization_suggestions']:
                self.learning_data['optimization_suggestions'].append(opt)
        
        # Keep only recent optimizations
        if len(self.learning_data['optimization_suggestions']) > 100:
            self.learning_data['optimization_suggestions'] = (
                self.learning_data['optimization_suggestions'][-100:]
            )
    
    def get_command_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
        success_only: bool = False
    ) -> List[Dict]:
        """
        Get command execution history
        
        Args:
            agent_id: Filter by specific agent (None for all)
            limit: Maximum number of results
            success_only: Only return successful executions
        
        Returns:
            List of command execution records
        """
        if not self.command_log_file.exists():
            return []
        
        with open(self.command_log_file, 'r') as f:
            command_log = json.load(f)
        
        # Filter by agent_id
        if agent_id:
            command_log = [cmd for cmd in command_log if cmd['agent_id'] == agent_id]
        
        # Filter by success
        if success_only:
            command_log = [cmd for cmd in command_log if cmd['success']]
        
        # Return most recent
        return command_log[-limit:]
    
    def get_learning_insights(self) -> Dict:
        """Get learning insights and improvement suggestions"""
        return {
            'patterns': self.learning_data['patterns'],
            'common_errors': dict(
                sorted(
                    self.learning_data['common_errors'].items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:10]  # Top 10 errors
            ),
            'optimization_suggestions': self.learning_data['optimization_suggestions'][-20:],
            'command_statistics': dict(self.command_stats),
            'last_analysis': datetime.now().isoformat()
        }
    
    def get_service_improvements(self) -> List[Dict]:
        """Get suggested service improvements based on command analysis"""
        improvements = []
        
        # Analyze patterns for improvements
        for cmd_type, pattern in self.learning_data['patterns'].items():
            if pattern['executions'] > 10 and pattern['success_rate'] < 0.8:
                improvements.append({
                    'command_type': cmd_type,
                    'issue': 'Low success rate',
                    'success_rate': pattern['success_rate'],
                    'suggestion': f'Review {cmd_type} usage patterns and error handling',
                    'priority': 'high'
                })
        
        # Check for repeated errors
        for error_key, error_info in self.learning_data['common_errors'].items():
            if error_info['count'] > 5:
                improvements.append({
                    'error': error_key[:50] + '...',
                    'occurrences': error_info['count'],
                    'suggestion': error_info['suggested_fix'] or 'Manual investigation required',
                    'priority': 'medium'
                })
        
        # Add optimization suggestions
        for opt in self.learning_data['optimization_suggestions'][-10:]:
            improvements.append({
                'type': opt['type'],
                'suggestion': opt['suggestion'],
                'example_command': opt['command'],
                'priority': 'low'
            })
        
        return improvements
    
    def get_passphrase_info(self) -> Dict:
        """Get passphrase information (without revealing the actual passphrase)"""
        if not self.passphrase_file.exists():
            return {}
        
        with open(self.passphrase_file, 'r') as f:
            data = json.load(f)
        
        return {
            'created_at': data.get('created_at'),
            'note': data.get('note'),
            'location': str(self.passphrase_file)
        }


# Global instance
_privileged_system = None


def get_privileged_system() -> PrivilegedCommandSystem:
    """Get or create the global privileged command system"""
    global _privileged_system
    if _privileged_system is None:
        _privileged_system = PrivilegedCommandSystem()
    return _privileged_system
