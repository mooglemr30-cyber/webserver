"""
AI Agent Integration Example - Privileged Command System

This example demonstrates how an AI agent can use the privileged
command system to perform system maintenance while learning and
improving from the results.
"""

import requests
import json
import time
from typing import Dict, List, Optional
from datetime import datetime


class PrivilegedAIAgent:
    """
    AI Agent with privileged command execution capabilities
    
    Features:
    - Execute sudo commands securely
    - Learn from command outputs
    - Suggest improvements
    - Share knowledge network-wide
    """
    
    def __init__(self, base_url: str, passphrase: str, agent_id: str):
        self.base_url = base_url
        self.passphrase = passphrase
        self.agent_id = agent_id
        self.command_history = []
        self.learning_data = {}
    
    def execute_privileged(self, command: str, timeout: int = 300) -> Dict:
        """Execute a privileged command"""
        headers = {
            'X-Privileged-Passphrase': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        data = {
            'command': command,
            'agent_id': self.agent_id,
            'timeout': timeout
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/privileged/execute',
                headers=headers,
                json=data,
                timeout=timeout + 10
            )
            
            result = response.json()
            self.command_history.append(result)
            
            # Analyze result
            self._analyze_result(result)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_result(self, result: Dict):
        """Analyze command result for learning"""
        if result.get('success'):
            print(f"✅ Command succeeded: {result['command']}")
            print(f"   Duration: {result['duration']:.2f}s")
        else:
            print(f"❌ Command failed: {result['command']}")
            print(f"   Error: {result['stderr'][:100]}")
    
    def learn_from_network(self) -> Dict:
        """Learn from all network agents' command executions"""
        try:
            response = requests.get(
                f'{self.base_url}/api/privileged/learning'
            )
            
            self.learning_data = response.json()
            return self.learning_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_improvement_suggestions(self) -> List[Dict]:
        """Get AI-suggested improvements"""
        try:
            response = requests.get(
                f'{self.base_url}/api/privileged/improvements'
            )
            
            return response.json().get('improvements', [])
            
        except Exception as e:
            return []
    
    def implement_suggestion(self, suggestion: Dict) -> bool:
        """Attempt to implement an improvement suggestion"""
        print(f"\n🔧 Implementing: {suggestion['suggestion']}")
        
        # This would contain logic to convert suggestions to commands
        # For now, just demonstrate the concept
        if 'example_command' in suggestion:
            result = self.execute_privileged(suggestion['example_command'])
            return result.get('success', False)
        
        return False
    
    def system_update_routine(self):
        """Automated system update routine with learning"""
        print(f"\n{'='*60}")
        print(f"🤖 AI Agent: {self.agent_id}")
        print(f"📅 Starting system update routine")
        print(f"{'='*60}\n")
        
        # Step 1: Update package lists
        print("Step 1: Updating package lists...")
        result = self.execute_privileged('apt update')
        
        if not result.get('success'):
            print("❌ Failed to update package lists. Aborting.")
            return
        
        # Step 2: Check for upgrades
        print("\nStep 2: Checking for available upgrades...")
        result = self.execute_privileged('apt list --upgradable')
        
        if result.get('success'):
            upgradable = result['stdout'].count('\n')
            print(f"📦 Found {upgradable} upgradable packages")
        
        # Step 3: Learn from network
        print("\nStep 3: Learning from network experiences...")
        learning = self.learn_from_network()
        
        if 'patterns' in learning:
            apt_pattern = learning['patterns'].get('apt', {})
            if apt_pattern:
                print(f"   📊 Network stats for 'apt':")
                print(f"      Executions: {apt_pattern.get('executions', 0)}")
                print(f"      Success rate: {apt_pattern.get('success_rate', 0)*100:.1f}%")
        
        # Step 4: Get and implement improvements
        print("\nStep 4: Checking for improvement suggestions...")
        improvements = self.get_improvement_suggestions()
        
        high_priority = [i for i in improvements if i.get('priority') == 'high']
        if high_priority:
            print(f"   🚨 Found {len(high_priority)} high priority improvements:")
            for imp in high_priority[:3]:  # Show top 3
                print(f"      - {imp['suggestion']}")
        
        print(f"\n{'='*60}")
        print(f"✅ System update routine completed")
        print(f"{'='*60}\n")
    
    def service_health_check(self, service_name: str):
        """Check service health and suggest optimizations"""
        print(f"\n🔍 Checking health of service: {service_name}")
        
        # Check service status
        result = self.execute_privileged(f'systemctl status {service_name}')
        
        if result.get('success'):
            stdout = result['stdout']
            
            if 'active (running)' in stdout:
                print(f"   ✅ {service_name} is running")
            elif 'inactive' in stdout:
                print(f"   ⚠️  {service_name} is inactive")
            elif 'failed' in stdout:
                print(f"   ❌ {service_name} has failed")
            
            # Check for issues in logs
            print(f"\n   Checking recent logs for errors...")
            log_result = self.execute_privileged(
                f'journalctl -u {service_name} -n 20 --no-pager'
            )
            
            if log_result.get('success'):
                errors = log_result['stdout'].lower().count('error')
                warnings = log_result['stdout'].lower().count('warning')
                print(f"      Errors: {errors}, Warnings: {warnings}")
        
        return result
    
    def disk_space_optimization(self):
        """Analyze and optimize disk space"""
        print("\n💾 Disk Space Optimization")
        
        # Check disk usage
        print("\nStep 1: Checking disk usage...")
        result = self.execute_privileged('df -h /')
        
        if result.get('success'):
            print(f"   {result['stdout']}")
        
        # Find large files
        print("\nStep 2: Finding large files (>100MB)...")
        result = self.execute_privileged(
            'find /var/log -type f -size +100M 2>/dev/null | head -10'
        )
        
        if result.get('success') and result['stdout']:
            print(f"   Large log files found:")
            for line in result['stdout'].strip().split('\n')[:5]:
                print(f"      - {line}")
        
        # Clean package cache
        print("\nStep 3: Cleaning package cache...")
        result = self.execute_privileged('apt clean')
        
        if result.get('success'):
            print("   ✅ Package cache cleaned")
    
    def security_audit(self):
        """Perform basic security audit"""
        print("\n🔒 Security Audit")
        
        checks = [
            ('Failed login attempts', 'grep "Failed password" /var/log/auth.log | tail -10'),
            ('Open ports', 'ss -tuln | grep LISTEN | head -10'),
            ('Running processes', 'ps aux | wc -l'),
            ('System updates needed', 'apt list --upgradable | wc -l')
        ]
        
        for check_name, command in checks:
            print(f"\n   Checking: {check_name}")
            result = self.execute_privileged(command)
            
            if result.get('success'):
                output = result['stdout'].strip()
                if output:
                    print(f"      Result: {output[:200]}")
                else:
                    print(f"      ✅ No issues found")
    
    def get_my_command_history(self, limit: int = 20) -> List[Dict]:
        """Get this agent's command history from server"""
        try:
            response = requests.get(
                f'{self.base_url}/api/privileged/history',
                params={
                    'agent_id': self.agent_id,
                    'limit': limit
                }
            )
            
            return response.json().get('history', [])
            
        except Exception as e:
            return []
    
    def report_statistics(self):
        """Report agent's execution statistics"""
        history = self.get_my_command_history(limit=100)
        
        if not history:
            print("No command history available")
            return
        
        total = len(history)
        successful = sum(1 for cmd in history if cmd.get('success'))
        failed = total - successful
        
        total_duration = sum(cmd.get('duration', 0) for cmd in history)
        avg_duration = total_duration / total if total > 0 else 0
        
        print(f"\n📊 Agent Statistics: {self.agent_id}")
        print(f"{'='*60}")
        print(f"Total commands executed: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"Average execution time: {avg_duration:.2f}s")
        print(f"{'='*60}\n")


# ========================================
# USAGE EXAMPLES
# ========================================

def example_system_maintenance():
    """Example: Automated system maintenance"""
    
    # Load passphrase (in production, use environment variable)
    passphrase_file = "/run/media/admin1/1E1EC1FE1EC1CF49/to delete/TOKENSANDLOGINS/PRIVILEGED_PASSPHRASE.txt"
    
    try:
        with open(passphrase_file, 'r') as f:
            # Extract passphrase from file
            for line in f:
                if line.startswith('Passphrase:'):
                    passphrase = line.split('Passphrase:')[1].strip()
                    break
    except:
        print("❌ Could not load passphrase. Please check file location.")
        return
    
    # Create AI agent
    agent = PrivilegedAIAgent(
        base_url='http://localhost:8000',
        passphrase=passphrase,
        agent_id='system-maintenance-bot'
    )
    
    # Run system update routine
    agent.system_update_routine()
    
    # Check service health
    agent.service_health_check('nginx')
    
    # Optimize disk space
    agent.disk_space_optimization()
    
    # Security audit
    agent.security_audit()
    
    # Report statistics
    agent.report_statistics()


def example_monitoring_agent():
    """Example: Service monitoring agent"""
    
    passphrase_file = "/run/media/admin1/1E1EC1FE1EC1CF49/to delete/TOKENSANDLOGINS/PRIVILEGED_PASSPHRASE.txt"
    
    try:
        with open(passphrase_file, 'r') as f:
            for line in f:
                if line.startswith('Passphrase:'):
                    passphrase = line.split('Passphrase:')[1].strip()
                    break
    except:
        print("❌ Could not load passphrase")
        return
    
    agent = PrivilegedAIAgent(
        base_url='http://localhost:8000',
        passphrase=passphrase,
        agent_id='service-monitor'
    )
    
    services = ['nginx', 'ssh', 'cron']
    
    print("\n🔍 Service Monitoring")
    print("="*60)
    
    for service in services:
        agent.service_health_check(service)
        time.sleep(1)  # Rate limiting
    
    print("\n" + "="*60)


def example_learning_agent():
    """Example: Agent that learns from network"""
    
    # No passphrase needed for learning (public API)
    base_url = 'http://localhost:8000'
    
    print("\n🧠 Learning from Network")
    print("="*60)
    
    # Get learning insights
    response = requests.get(f'{base_url}/api/privileged/learning')
    learning = response.json()
    
    print("\n📊 Command Patterns:")
    for cmd_type, pattern in learning.get('patterns', {}).items():
        print(f"\n   {cmd_type}:")
        print(f"      Executions: {pattern.get('executions', 0)}")
        print(f"      Success rate: {pattern.get('success_rate', 0)*100:.1f}%")
    
    print("\n\n🐛 Common Errors:")
    for error, info in list(learning.get('common_errors', {}).items())[:3]:
        print(f"\n   Error: {error[:50]}...")
        print(f"      Occurrences: {info.get('count', 0)}")
        if info.get('suggested_fix'):
            print(f"      Fix: {info['suggested_fix']}")
    
    print("\n\n💡 Optimization Suggestions:")
    response = requests.get(f'{base_url}/api/privileged/improvements')
    improvements = response.json().get('improvements', [])
    
    for imp in improvements[:5]:
        priority = imp.get('priority', 'unknown').upper()
        suggestion = imp.get('suggestion', 'No suggestion')
        print(f"\n   [{priority}] {suggestion}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║        PRIVILEGED AI AGENT - INTEGRATION EXAMPLE          ║
    ║                                                            ║
    ║  Demonstrates how AI agents can use privileged commands   ║
    ║  to maintain systems while learning and improving         ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("\nAvailable examples:")
    print("1. System Maintenance Agent")
    print("2. Service Monitoring Agent")
    print("3. Learning Agent (read-only)")
    
    choice = input("\nSelect example (1-3, or 'all'): ").strip()
    
    if choice == '1':
        example_system_maintenance()
    elif choice == '2':
        example_monitoring_agent()
    elif choice == '3':
        example_learning_agent()
    elif choice.lower() == 'all':
        example_learning_agent()
        time.sleep(2)
        example_monitoring_agent()
        time.sleep(2)
        example_system_maintenance()
    else:
        print("Invalid choice")
