#!/usr/bin/env python3
"""
AI Memory Manager for PCAP Monitor System
Provides persistent storage and intelligence sharing across AI agents
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class AIMemoryManager:
    """Manages AI memory and knowledge base for PCAP monitoring system"""
    
    def __init__(self, storage_dir: str = None):
        """Initialize AI Memory Manager.
        Resolution order for storage directory:
        1. Explicit storage_dir argument
        2. Environment variable AIMEMORY_PATH (for dedicated memory mount)
        3. Environment variable AI_STORAGE_PATH (shared agent storage)
        4. Legacy default /home/admin1/Documents/AIAGENTSTORAGE
        Creates target directory if missing.
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            env_mem = os.getenv("AIMEMORY_PATH")
            env_shared = os.getenv("AI_STORAGE_PATH")
            base = env_mem or env_shared or "/home/admin1/Documents/AIAGENTSTORAGE"
            self.storage_dir = Path(base)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage paths
        self.shared_learnings = self.storage_dir / "shared_learnings"
        self.local_analysis = self.storage_dir / "local_analysis"
        self.kb_file = self.storage_dir / "ai_knowledge_base.json"
        self.insights_file = self.storage_dir / "ai_insights.json"
        
        # Session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log = []
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directory structure"""
        dirs = [
            self.storage_dir,
            self.shared_learnings,
            self.local_analysis,
            self.local_analysis / "ai_knowledge",
            self.local_analysis / "security_analysis",
            self.local_analysis / "enhanced_analysis",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def load_knowledge_base(self) -> Dict:
        """Load the AI knowledge base"""
        if not self.kb_file.exists():
            return self._create_empty_kb()
        
        try:
            with open(self.kb_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error loading knowledge base: {e}")
            return self._create_empty_kb()
    
    def save_knowledge_base(self, kb: Dict):
        """Save knowledge base to disk"""
        kb['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.kb_file, 'w') as f:
                json.dump(kb, f, indent=2)
            return True
        except IOError as e:
            print(f"❌ Error saving knowledge base: {e}")
            return False
    
    def _create_empty_kb(self) -> Dict:
        """Create empty knowledge base structure"""
        return {
            "total_analyses": 0,
            "device_profiles": {},
            "network_patterns": {},
            "security_events": [],
            "learned_behaviors": {},
            "system_metadata": {
                "created": datetime.now().isoformat(),
                "version": "2.0"
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def store_learning(self, topic: str, content: str, importance: int = 5, 
                      tags: List[str] = None) -> bool:
        """
        Store a learning in the knowledge base
        
        Args:
            topic: Learning topic/title
            content: Detailed learning content
            importance: 1-10 scale (10 = critical)
            tags: List of tags for categorization
        """
        kb = self.load_knowledge_base()
        
        learning_id = f"{self.session_id}_{len(kb.get('learnings', []))}"
        
        if 'learnings' not in kb:
            kb['learnings'] = []
        
        learning = {
            "id": learning_id,
            "topic": topic,
            "content": content,
            "importance": importance,
            "tags": tags or [],
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id
        }
        
        kb['learnings'].append(learning)
        
        # Also save to shared learnings
        self._save_to_shared_learnings(learning)
        
        self.session_log.append(f"Stored learning: {topic}")
        return self.save_knowledge_base(kb)
    
    def store_device_profile(self, ip: str, profile: Dict) -> bool:
        """Store or update device profile"""
        kb = self.load_knowledge_base()
        
        if ip not in kb['device_profiles']:
            kb['device_profiles'][ip] = {
                "first_seen": datetime.now().isoformat(),
                "vendors": [],
                "hostnames": [],
                "os_guesses": [],
                "ports_seen": set(),
                "behaviors": []
            }
        
        # Update profile
        device = kb['device_profiles'][ip]
        device['last_seen'] = datetime.now().isoformat()
        
        # Merge new data
        if 'vendor' in profile:
            if profile['vendor'] not in device['vendors']:
                device['vendors'].append(profile['vendor'])
        
        if 'hostname' in profile:
            if profile['hostname'] not in device['hostnames']:
                device['hostnames'].append(profile['hostname'])
        
        if 'os' in profile:
            if profile['os'] not in device['os_guesses']:
                device['os_guesses'].append(profile['os'])
        
        if 'ports' in profile:
            if isinstance(device['ports_seen'], set):
                device['ports_seen'] = list(device['ports_seen'])
            for port in profile['ports']:
                if port not in device['ports_seen']:
                    device['ports_seen'].append(port)
        
        if 'behavior' in profile:
            device['behaviors'].append({
                "timestamp": datetime.now().isoformat(),
                "behavior": profile['behavior']
            })
        
        self.session_log.append(f"Updated device profile: {ip}")
        return self.save_knowledge_base(kb)
    
    def store_security_event(self, event_type: str, description: str, 
                            severity: str = "info", metadata: Dict = None) -> bool:
        """Store a security event"""
        kb = self.load_knowledge_base()
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "description": description,
            "severity": severity,
            "metadata": metadata or {},
            "session_id": self.session_id
        }
        
        kb['security_events'].append(event)
        
        # Keep only last 1000 events
        if len(kb['security_events']) > 1000:
            kb['security_events'] = kb['security_events'][-1000:]
        
        self.session_log.append(f"Stored security event: {event_type}")
        return self.save_knowledge_base(kb)
    
    def store_network_pattern(self, pattern: str, pattern_type: str, 
                             confidence: float, metadata: Dict = None) -> bool:
        """Store a detected network pattern"""
        kb = self.load_knowledge_base()
        
        if pattern not in kb['network_patterns']:
            kb['network_patterns'][pattern] = {
                "pattern_type": pattern_type,
                "first_seen": datetime.now().isoformat(),
                "occurrences": 0,
                "confidence": confidence,
                "metadata": metadata or {}
            }
        
        # Update pattern
        kb['network_patterns'][pattern]['last_seen'] = datetime.now().isoformat()
        kb['network_patterns'][pattern]['occurrences'] += 1
        kb['network_patterns'][pattern]['confidence'] = max(
            kb['network_patterns'][pattern]['confidence'],
            confidence
        )
        
        self.session_log.append(f"Updated pattern: {pattern}")
        return self.save_knowledge_base(kb)
    
    def query_devices(self, vendor: str = None, os_type: str = None) -> List[Dict]:
        """Query device profiles with filters"""
        kb = self.load_knowledge_base()
        devices = kb.get('device_profiles', {})
        
        results = []
        for ip, profile in devices.items():
            # Apply filters
            if vendor:
                if not any(vendor.lower() in v.lower() for v in profile.get('vendors', [])):
                    continue
            
            if os_type:
                if not any(os_type.lower() in os.lower() for os in profile.get('os_guesses', [])):
                    continue
            
            results.append({'ip': ip, **profile})
        
        return results
    
    def query_security_events(self, event_type: str = None, severity: str = None, 
                             limit: int = 100) -> List[Dict]:
        """Query security events with filters"""
        kb = self.load_knowledge_base()
        events = kb.get('security_events', [])
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.get('type') == event_type]
        
        if severity:
            events = [e for e in events if e.get('severity') == severity]
        
        # Return most recent events
        return events[-limit:]
    
    def search_learnings(self, query: str = None, tag: str = None, 
                        min_importance: int = 0) -> List[Dict]:
        """Search stored learnings"""
        kb = self.load_knowledge_base()
        learnings = kb.get('learnings', [])
        
        results = []
        for learning in learnings:
            # Importance filter
            if learning.get('importance', 0) < min_importance:
                continue
            
            # Tag filter
            if tag and tag not in learning.get('tags', []):
                continue
            
            # Query filter
            if query:
                query_lower = query.lower()
                if query_lower not in learning.get('topic', '').lower() and \
                   query_lower not in learning.get('content', '').lower():
                    continue
            
            results.append(learning)
        
        # Sort by importance (descending)
        results.sort(key=lambda x: x.get('importance', 0), reverse=True)
        return results
    
    def get_statistics(self) -> Dict:
        """Get knowledge base statistics"""
        kb = self.load_knowledge_base()
        
        return {
            "total_analyses": kb.get('total_analyses', 0),
            "total_devices": len(kb.get('device_profiles', {})),
            "total_patterns": len(kb.get('network_patterns', {})),
            "total_security_events": len(kb.get('security_events', [])),
            "total_learnings": len(kb.get('learnings', [])),
            "last_updated": kb.get('last_updated', 'Never'),
            "session_events": len(self.session_log)
        }
    
    def _save_to_shared_learnings(self, learning: Dict):
        """Save learning to shared learnings directory"""
        collab_file = self.shared_learnings / "COLLABORATIVE_AI_KNOWLEDGE.md"
        
        # Append to collaborative knowledge file
        try:
            # Create header if file doesn't exist
            if not collab_file.exists():
                with open(collab_file, 'w') as f:
                    f.write("# Collaborative AI Knowledge\n\n")
                    f.write("## Shared learnings from PCAP Monitor AI agents\n\n")
            
            # Append learning
            with open(collab_file, 'a') as f:
                f.write(f"\n---\n\n")
                f.write(f"### {learning['topic']}\n\n")
                f.write(f"**Timestamp:** {learning['timestamp']}  \n")
                f.write(f"**Importance:** {learning['importance']}/10  \n")
                f.write(f"**Tags:** {', '.join(learning.get('tags', []))}  \n\n")
                f.write(f"{learning['content']}\n\n")
        except IOError as e:
            print(f"⚠️  Could not save to shared learnings: {e}")
    
    def export_session_log(self) -> str:
        """Export current session activity log"""
        log_content = [
            f"# Session Log: {self.session_id}",
            f"**Started:** {self.session_id}",
            f"**Events:** {len(self.session_log)}",
            "",
            "## Activities",
            ""
        ]
        
        for event in self.session_log:
            log_content.append(f"- {event}")
        
        return "\n".join(log_content)
    
    def create_memory_snapshot(self, name: str, data: Dict) -> bool:
        """Create a named memory snapshot"""
        snapshot_file = self.local_analysis / f"snapshot_{name}_{self.session_id}.json"
        
        snapshot = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "data": data
        }
        
        try:
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            self.session_log.append(f"Created snapshot: {name}")
            return True
        except IOError as e:
            print(f"❌ Error creating snapshot: {e}")
            return False
    
    def load_memory_snapshot(self, name: str) -> Optional[Dict]:
        """Load most recent snapshot with given name"""
        snapshots = list(self.local_analysis.glob(f"snapshot_{name}_*.json"))
        
        if not snapshots:
            return None
        
        # Get most recent
        latest = max(snapshots, key=lambda p: p.stat().st_mtime)
        
        try:
            with open(latest, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Error loading snapshot: {e}")
            return None


def get_ai_memory() -> AIMemoryManager:
    """Get AI Memory Manager instance (singleton pattern)"""
    return AIMemoryManager()


if __name__ == '__main__':
    # CLI interface
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Memory Manager CLI')
    parser.add_argument('command', choices=['stats', 'devices', 'events', 'learnings', 'patterns'])
    parser.add_argument('--vendor', help='Filter devices by vendor')
    parser.add_argument('--severity', help='Filter events by severity')
    parser.add_argument('--tag', help='Filter learnings by tag')
    parser.add_argument('--query', help='Search query')
    parser.add_argument('--limit', type=int, default=20, help='Result limit')
    
    args = parser.parse_args()
    
    memory = get_ai_memory()
    
    if args.command == 'stats':
        stats = memory.get_statistics()
        print("\n=== AI Memory Statistics ===\n")
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    elif args.command == 'devices':
        devices = memory.query_devices(vendor=args.vendor)
        print(f"\n=== Device Profiles ({len(devices)}) ===\n")
        for device in devices[:args.limit]:
            print(f"📱 {device['ip']}")
            print(f"   Vendors: {', '.join(device.get('vendors', []))}")
            if device.get('hostnames'):
                print(f"   Hostnames: {', '.join(device['hostnames'])}")
            print()
    
    elif args.command == 'events':
        events = memory.query_security_events(severity=args.severity, limit=args.limit)
        print(f"\n=== Security Events ({len(events)}) ===\n")
        for event in events:
            print(f"⚠️  {event.get('timestamp', 'N/A')}")
            print(f"   Type: {event.get('type', 'Unknown')}")
            print(f"   Severity: {event.get('severity', 'info')}")
            print(f"   {event.get('description', '')}")
            print()
    
    elif args.command == 'learnings':
        learnings = memory.search_learnings(query=args.query, tag=args.tag)
        print(f"\n=== Learnings ({len(learnings)}) ===\n")
        for learning in learnings[:args.limit]:
            print(f"📚 {learning.get('topic', 'Untitled')}")
            print(f"   Importance: {learning.get('importance', 0)}/10")
            print(f"   Tags: {', '.join(learning.get('tags', []))}")
            print(f"   {learning.get('content', '')[:200]}...")
            print()
    
    elif args.command == 'patterns':
        kb = memory.load_knowledge_base()
        patterns = kb.get('network_patterns', {})
        print(f"\n=== Network Patterns ({len(patterns)}) ===\n")
        
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: x[1].get('occurrences', 0),
            reverse=True
        )
        
        for pattern, data in sorted_patterns[:args.limit]:
            print(f"🔄 {pattern}")
            print(f"   Type: {data.get('pattern_type', 'unknown')}")
            print(f"   Occurrences: {data.get('occurrences', 0)}")
            print(f"   Confidence: {data.get('confidence', 0):.2f}")
            print()
