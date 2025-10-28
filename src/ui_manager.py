#!/usr/bin/env python3
"""
Advanced UI/UX management system.
Provides modern responsive interface components, themes, and user experience enhancements.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ThemeManager:
    """Manage UI themes and customization."""
    
    def __init__(self):
        self.themes = {
            'dark': {
                'name': 'Dark Theme',
                'primary_color': '#007acc',
                'secondary_color': '#2d2d2d',
                'background_color': '#1a1a1a',
                'surface_color': '#2d2d2d',
                'text_color': '#e0e0e0',
                'text_secondary': '#b0b0b0',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8',
                'border_color': '#444',
                'shadow': '0 2px 10px rgba(0, 0, 0, 0.3)',
                'border_radius': '8px'
            },
            'light': {
                'name': 'Light Theme',
                'primary_color': '#007acc',
                'secondary_color': '#6c757d',
                'background_color': '#ffffff',
                'surface_color': '#f8f9fa',
                'text_color': '#212529',
                'text_secondary': '#6c757d',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8',
                'border_color': '#dee2e6',
                'shadow': '0 2px 10px rgba(0, 0, 0, 0.1)',
                'border_radius': '8px'
            },
            'blue': {
                'name': 'Ocean Blue',
                'primary_color': '#0066cc',
                'secondary_color': '#004080',
                'background_color': '#0a1526',
                'surface_color': '#1a2f4a',
                'text_color': '#e6f2ff',
                'text_secondary': '#b3d9ff',
                'success_color': '#00cc66',
                'warning_color': '#ffaa00',
                'error_color': '#ff4444',
                'info_color': '#00aaff',
                'border_color': '#2a4f7a',
                'shadow': '0 2px 15px rgba(0, 102, 204, 0.2)',
                'border_radius': '10px'
            },
            'purple': {
                'name': 'Royal Purple',
                'primary_color': '#6a4c93',
                'secondary_color': '#4a3269',
                'background_color': '#1e1329',
                'surface_color': '#2d1b3d',
                'text_color': '#f0e6ff',
                'text_secondary': '#d1c2ff',
                'success_color': '#8bc34a',
                'warning_color': '#ff9800',
                'error_color': '#f44336',
                'info_color': '#2196f3',
                'border_color': '#3d2951',
                'shadow': '0 2px 15px rgba(106, 76, 147, 0.2)',
                'border_radius': '12px'
            }
        }
        
        self.current_theme = 'dark'
    
    def get_theme(self, theme_name: str = None) -> Dict[str, str]:
        """Get theme configuration."""
        theme_name = theme_name or self.current_theme
        return self.themes.get(theme_name, self.themes['dark'])
    
    def set_theme(self, theme_name: str) -> bool:
        """Set current theme."""
        if theme_name in self.themes:
            self.current_theme = theme_name
            return True
        return False
    
    def get_available_themes(self) -> List[Dict[str, str]]:
        """Get list of available themes."""
        return [
            {'id': theme_id, 'name': theme_data['name']}
            for theme_id, theme_data in self.themes.items()
        ]
    
    def generate_css_variables(self, theme_name: str = None) -> str:
        """Generate CSS custom properties for theme."""
        theme = self.get_theme(theme_name)
        
        css_vars = ":root {\n"
        for key, value in theme.items():
            css_var_name = f"--{key.replace('_', '-')}"
            css_vars += f"  {css_var_name}: {value};\n"
        css_vars += "}\n"
        
        return css_vars

class UIComponentManager:
    """Manage UI components and templates."""
    
    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
    
    def get_modern_ui_template(self) -> str:
        """Get modern responsive UI template."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Web Server</title>
    <link rel="icon" type="image/x-icon" href="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iOCIgZmlsbD0iIzAwN2FjYyIvPgo8cGF0aCBkPSJNOCAxMmg0djhIOHYtOHptNiAwaDR2OGgtNHYtOHptNiAwaDR2OGgtNHYtOHoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=">
    <style>
        {{ theme_css }}
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Header */
        .header {
            background: var(--surface-color);
            border-bottom: 1px solid var(--border-color);
            box-shadow: var(--shadow);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            height: 60px;
        }
        
        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            height: 100%;
            padding: 0 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .logo {
            display: flex;
            align-items: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-color);
            text-decoration: none;
        }
        
        .logo-icon {
            width: 32px;
            height: 32px;
            margin-right: 0.5rem;
            background: var(--primary-color);
            border-radius: var(--border-radius);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .header-controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .theme-selector {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem;
            border-radius: var(--border-radius);
            cursor: pointer;
        }
        
        .connection-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .connection-status.connected {
            background: rgba(40, 167, 69, 0.1);
            color: var(--success-color);
        }
        
        .connection-status.disconnected {
            background: rgba(220, 53, 69, 0.1);
            color: var(--error-color);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Main Layout */
        .main-container {
            display: flex;
            margin-top: 60px;
            min-height: calc(100vh - 60px);
        }
        
        .sidebar {
            width: 250px;
            background: var(--surface-color);
            border-right: 1px solid var(--border-color);
            padding: 1rem 0;
            position: fixed;
            height: calc(100vh - 60px);
            overflow-y: auto;
            transition: transform 0.3s ease;
        }
        
        .sidebar.collapsed {
            transform: translateX(-100%);
        }
        
        .sidebar-nav {
            list-style: none;
        }
        
        .sidebar-nav li {
            margin: 0.25rem 0;
        }
        
        .sidebar-nav a {
            display: flex;
            align-items: center;
            padding: 0.75rem 1.5rem;
            color: var(--text-color);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }
        
        .sidebar-nav a:hover,
        .sidebar-nav a.active {
            background: rgba(0, 122, 204, 0.1);
            border-left-color: var(--primary-color);
            color: var(--primary-color);
        }
        
        .sidebar-nav-icon {
            width: 20px;
            height: 20px;
            margin-right: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .content {
            flex: 1;
            margin-left: 250px;
            padding: 2rem;
            transition: margin-left 0.3s ease;
        }
        
        .content.expanded {
            margin-left: 0;
        }
        
        /* Cards */
        .card {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            margin-bottom: 2rem;
            overflow: hidden;
        }
        
        .card-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
        }
        
        .card-body {
            padding: 1.5rem;
        }
        
        .card-footer {
            padding: 1rem 1.5rem;
            background: rgba(0, 0, 0, 0.05);
            border-top: 1px solid var(--border-color);
        }
        
        /* Forms */
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: var(--text-color);
        }
        
        .form-control {
            width: 100%;
            padding: 0.75rem;
            background: var(--background-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            color: var(--text-color);
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.1);
        }
        
        .form-control:invalid {
            border-color: var(--error-color);
        }
        
        /* Buttons */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: var(--border-radius);
            font-size: 1rem;
            font-weight: 500;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            gap: 0.5rem;
            min-height: 44px;
        }
        
        .btn-primary {
            background: var(--primary-color);
            color: white;
        }
        
        .btn-primary:hover {
            background: color-mix(in srgb, var(--primary-color) 85%, black);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 122, 204, 0.3);
        }
        
        .btn-secondary {
            background: var(--secondary-color);
            color: white;
        }
        
        .btn-success {
            background: var(--success-color);
            color: white;
        }
        
        .btn-danger {
            background: var(--error-color);
            color: white;
        }
        
        .btn-outline {
            background: transparent;
            border: 1px solid var(--primary-color);
            color: var(--primary-color);
        }
        
        .btn-outline:hover {
            background: var(--primary-color);
            color: white;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }
        
        /* File Upload */
        .file-upload-area {
            border: 2px dashed var(--border-color);
            border-radius: var(--border-radius);
            padding: 3rem 2rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .file-upload-area:hover,
        .file-upload-area.dragover {
            border-color: var(--primary-color);
            background: rgba(0, 122, 204, 0.05);
        }
        
        .file-upload-icon {
            font-size: 3rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }
        
        .file-upload-text {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .file-upload-subtext {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        /* Progress Bar */
        .progress {
            width: 100%;
            height: 8px;
            background: var(--border-color);
            border-radius: 4px;
            overflow: hidden;
            margin: 1rem 0;
        }
        
        .progress-bar {
            height: 100%;
            background: var(--primary-color);
            transition: width 0.3s ease;
            position: relative;
        }
        
        .progress-bar.animated::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(45deg, 
                rgba(255,255,255,0.2) 25%, 
                transparent 25%, 
                transparent 50%, 
                rgba(255,255,255,0.2) 50%, 
                rgba(255,255,255,0.2) 75%, 
                transparent 75%, 
                transparent);
            background-size: 20px 20px;
            animation: progress-animation 1s linear infinite;
        }
        
        @keyframes progress-animation {
            0% { background-position: 0 0; }
            100% { background-position: 20px 0; }
        }
        
        /* Notifications */
        .notification-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 2000;
            max-width: 400px;
        }
        
        .notification {
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            padding: 1rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            animation: slideInRight 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .notification::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--primary-color);
        }
        
        .notification.success::before { background: var(--success-color); }
        .notification.warning::before { background: var(--warning-color); }
        .notification.error::before { background: var(--error-color); }
        .notification.info::before { background: var(--info-color); }
        
        .notification-icon {
            width: 20px;
            height: 20px;
            flex-shrink: 0;
            margin-top: 0.125rem;
        }
        
        .notification-content {
            flex: 1;
        }
        
        .notification-title {
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .notification-message {
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .notification-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        /* Modal */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 3000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }
        
        .modal-overlay.active {
            opacity: 1;
            visibility: visible;
        }
        
        .modal {
            background: var(--surface-color);
            border-radius: var(--border-radius);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }
        
        .modal-overlay.active .modal {
            transform: scale(1);
        }
        
        .modal-header {
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .modal-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            color: var(--text-secondary);
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.3s ease;
        }
        
        .modal-close:hover {
            background: var(--border-color);
        }
        
        .modal-body {
            padding: 1.5rem;
        }
        
        .modal-footer {
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border-color);
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
        }
        
        /* Table */
        .table-container {
            background: var(--surface-color);
            border-radius: var(--border-radius);
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        
        .table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .table th,
        .table td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        .table th {
            background: rgba(0, 0, 0, 0.05);
            font-weight: 600;
            color: var(--text-color);
        }
        
        .table tbody tr:hover {
            background: rgba(0, 122, 204, 0.05);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                z-index: 1500;
            }
            
            .sidebar.mobile-open {
                transform: translateX(0);
            }
            
            .content {
                margin-left: 0;
                padding: 1rem;
            }
            
            .header-content {
                padding: 0 1rem;
            }
            
            .card-body {
                padding: 1rem;
            }
            
            .modal {
                margin: 1rem;
                width: calc(100% - 2rem);
            }
        }
        
        /* Loading States */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-color);
            border-radius: 50%;
            border-top-color: var(--primary-color);
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .skeleton {
            background: linear-gradient(90deg, 
                var(--border-color) 25%, 
                rgba(var(--border-color), 0.5) 50%, 
                var(--border-color) 75%);
            background-size: 200% 100%;
            animation: skeleton-loading 1.5s infinite;
            border-radius: var(--border-radius);
        }
        
        @keyframes skeleton-loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        /* Accessibility */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        .focus-visible {
            outline: 2px solid var(--primary-color);
            outline-offset: 2px;
        }
        
        /* Dark mode specific adjustments */
        @media (prefers-color-scheme: dark) {
            .card-footer {
                background: rgba(255, 255, 255, 0.05);
            }
            
            .table th {
                background: rgba(255, 255, 255, 0.05);
            }
        }
    </style>
    
    <!-- Socket.IO for real-time updates -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="header-content">
            <a href="/" class="logo">
                <div class="logo-icon">W</div>
                WebServer
            </a>
            
            <div class="header-controls">
                <select class="theme-selector" id="themeSelector">
                    <option value="dark">Dark Theme</option>
                    <option value="light">Light Theme</option>
                    <option value="blue">Ocean Blue</option>
                    <option value="purple">Royal Purple</option>
                </select>
                
                <div class="connection-status" id="connectionStatus">
                    <div class="status-dot"></div>
                    <span>Connecting...</span>
                </div>
            </div>
        </div>
    </header>
    
    <!-- Main Container -->
    <div class="main-container">
        <!-- Sidebar -->
        <nav class="sidebar" id="sidebar">
            <ul class="sidebar-nav">
                <li><a href="#dashboard" class="nav-link active">
                    <span class="sidebar-nav-icon">📊</span>
                    Dashboard
                </a></li>
                <li><a href="#data" class="nav-link">
                    <span class="sidebar-nav-icon">💾</span>
                    Data Storage
                </a></li>
                <li><a href="#files" class="nav-link">
                    <span class="sidebar-nav-icon">📁</span>
                    File Manager
                </a></li>
                <li><a href="#programs" class="nav-link">
                    <span class="sidebar-nav-icon">⚙️</span>
                    Programs
                </a></li>
                <li><a href="#terminal" class="nav-link">
                    <span class="sidebar-nav-icon">💻</span>
                    Terminal
                </a></li>
                <li><a href="#tunnels" class="nav-link">
                    <span class="sidebar-nav-icon">🌐</span>
                    Tunnels
                </a></li>
                <li><a href="#monitoring" class="nav-link">
                    <span class="sidebar-nav-icon">📈</span>
                    Monitoring
                </a></li>
                <li><a href="#settings" class="nav-link">
                    <span class="sidebar-nav-icon">⚙️</span>
                    Settings
                </a></li>
            </ul>
        </nav>
        
        <!-- Content -->
        <main class="content" id="content">
            <!-- Content will be dynamically loaded here -->
            <div id="page-content">
                <!-- Dashboard content by default -->
            </div>
        </main>
    </div>
    
    <!-- Notification Container -->
    <div class="notification-container" id="notificationContainer"></div>
    
    <!-- Modal Container -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title" id="modalTitle">Modal Title</h3>
                <button class="modal-close" id="modalClose">&times;</button>
            </div>
            <div class="modal-body" id="modalBody">
                Modal content goes here
            </div>
            <div class="modal-footer" id="modalFooter">
                <button class="btn btn-secondary" id="modalCancel">Cancel</button>
                <button class="btn btn-primary" id="modalConfirm">Confirm</button>
            </div>
        </div>
    </div>
    
    <script>
        // Modern UI JavaScript functionality
        class EnhancedUI {
            constructor() {
                this.socket = null;
                this.currentTheme = localStorage.getItem('theme') || 'dark';
                this.currentPage = 'dashboard';
                this.notifications = [];
                
                this.init();
            }
            
            init() {
                this.setupTheme();
                this.setupNavigation();
                this.setupSocket();
                this.setupModals();
                this.setupFileUpload();
                this.loadPage('dashboard');
            }
            
            setupTheme() {
                const themeSelector = document.getElementById('themeSelector');
                themeSelector.value = this.currentTheme;
                
                themeSelector.addEventListener('change', (e) => {
                    this.setTheme(e.target.value);
                });
                
                this.setTheme(this.currentTheme);
            }
            
            setTheme(themeName) {
                this.currentTheme = themeName;
                localStorage.setItem('theme', themeName);
                
                // Apply theme by updating CSS custom properties
                fetch(`/api/theme/${themeName}`)
                    .then(response => response.json())
                    .then(theme => {
                        const root = document.documentElement;
                        Object.entries(theme).forEach(([key, value]) => {
                            root.style.setProperty(`--${key.replace('_', '-')}`, value);
                        });
                    })
                    .catch(error => {
                        console.error('Error loading theme:', error);
                    });
            }
            
            setupNavigation() {
                const navLinks = document.querySelectorAll('.nav-link');
                navLinks.forEach(link => {
                    link.addEventListener('click', (e) => {
                        e.preventDefault();
                        const page = link.getAttribute('href').substring(1);
                        this.loadPage(page);
                        
                        // Update active state
                        navLinks.forEach(l => l.classList.remove('active'));
                        link.classList.add('active');
                    });
                });
            }
            
            setupSocket() {
                this.socket = io();
                
                this.socket.on('connect', () => {
                    this.updateConnectionStatus(true);
                    this.showNotification('Connected to server', 'success');
                });
                
                this.socket.on('disconnect', () => {
                    this.updateConnectionStatus(false);
                    this.showNotification('Disconnected from server', 'error');
                });
                
                this.socket.on('notification', (data) => {
                    this.showNotification(data.message, data.type, data.title);
                });
                
                this.socket.on('progress', (data) => {
                    this.updateProgress(data.operation, data.progress, data.message);
                });
            }
            
            updateConnectionStatus(connected) {
                const status = document.getElementById('connectionStatus');
                if (connected) {
                    status.className = 'connection-status connected';
                    status.innerHTML = '<div class="status-dot"></div><span>Connected</span>';
                } else {
                    status.className = 'connection-status disconnected';
                    status.innerHTML = '<div class="status-dot"></div><span>Disconnected</span>';
                }
            }
            
            loadPage(page) {
                this.currentPage = page;
                const content = document.getElementById('page-content');
                
                // Show loading state
                content.innerHTML = '<div class="loading-container"><div class="loading"></div> Loading...</div>';
                
                // Load page content
                fetch(`/api/page/${page}`)
                    .then(response => response.text())
                    .then(html => {
                        content.innerHTML = html;
                        this.initializePageComponents(page);
                    })
                    .catch(error => {
                        console.error('Error loading page:', error);
                        content.innerHTML = '<div class="error-message">Error loading page content</div>';
                    });
            }
            
            initializePageComponents(page) {
                // Initialize page-specific components
                switch(page) {
                    case 'files':
                        this.setupFileUpload();
                        break;
                    case 'terminal':
                        this.setupTerminal();
                        break;
                    case 'monitoring':
                        this.setupMonitoring();
                        break;
                }
            }
            
            setupFileUpload() {
                const uploadAreas = document.querySelectorAll('.file-upload-area');
                uploadAreas.forEach(area => {
                    const input = area.querySelector('input[type="file"]');
                    
                    area.addEventListener('click', () => input.click());
                    
                    area.addEventListener('dragover', (e) => {
                        e.preventDefault();
                        area.classList.add('dragover');
                    });
                    
                    area.addEventListener('dragleave', () => {
                        area.classList.remove('dragover');
                    });
                    
                    area.addEventListener('drop', (e) => {
                        e.preventDefault();
                        area.classList.remove('dragover');
                        
                        const files = e.dataTransfer.files;
                        this.handleFileUpload(files);
                    });
                    
                    if (input) {
                        input.addEventListener('change', (e) => {
                            this.handleFileUpload(e.target.files);
                        });
                    }
                });
            }
            
            handleFileUpload(files) {
                Array.from(files).forEach(file => {
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const progressId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                    this.showProgress(progressId, 0, `Uploading ${file.name}...`);
                    
                    fetch('/api/files', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        this.hideProgress(progressId);
                        if (data.success) {
                            this.showNotification(`File "${file.name}" uploaded successfully`, 'success');
                        } else {
                            this.showNotification(`Upload failed: ${data.error}`, 'error');
                        }
                    })
                    .catch(error => {
                        this.hideProgress(progressId);
                        this.showNotification(`Upload failed: ${error.message}`, 'error');
                    });
                });
            }
            
            showNotification(message, type = 'info', title = null) {
                const container = document.getElementById('notificationContainer');
                const notification = document.createElement('div');
                notification.className = `notification ${type}`;
                
                const icons = {
                    success: '✅',
                    error: '❌',
                    warning: '⚠️',
                    info: 'ℹ️'
                };
                
                notification.innerHTML = `
                    <div class="notification-icon">${icons[type] || icons.info}</div>
                    <div class="notification-content">
                        ${title ? `<div class="notification-title">${title}</div>` : ''}
                        <div class="notification-message">${message}</div>
                    </div>
                    <button class="notification-close">&times;</button>
                `;
                
                const closeBtn = notification.querySelector('.notification-close');
                closeBtn.addEventListener('click', () => {
                    notification.remove();
                });
                
                container.appendChild(notification);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 5000);
            }
            
            showProgress(id, progress, message) {
                // Implementation for showing progress indicators
                console.log(`Progress ${id}: ${progress}% - ${message}`);
            }
            
            hideProgress(id) {
                // Implementation for hiding progress indicators
                console.log(`Hide progress: ${id}`);
            }
            
            setupModals() {
                const overlay = document.getElementById('modalOverlay');
                const closeBtn = document.getElementById('modalClose');
                const cancelBtn = document.getElementById('modalCancel');
                
                [closeBtn, cancelBtn].forEach(btn => {
                    btn.addEventListener('click', () => this.hideModal());
                });
                
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        this.hideModal();
                    }
                });
            }
            
            showModal(title, body, confirmText = 'Confirm', onConfirm = null) {
                const overlay = document.getElementById('modalOverlay');
                const titleEl = document.getElementById('modalTitle');
                const bodyEl = document.getElementById('modalBody');
                const confirmBtn = document.getElementById('modalConfirm');
                
                titleEl.textContent = title;
                bodyEl.innerHTML = body;
                confirmBtn.textContent = confirmText;
                
                if (onConfirm) {
                    confirmBtn.onclick = () => {
                        onConfirm();
                        this.hideModal();
                    };
                }
                
                overlay.classList.add('active');
            }
            
            hideModal() {
                const overlay = document.getElementById('modalOverlay');
                overlay.classList.remove('active');
            }
        }
        
        // Initialize the enhanced UI when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            window.enhancedUI = new EnhancedUI();
        });
    </script>
</body>
</html>
        """
    
    def get_dashboard_template(self) -> str:
        """Get dashboard page template."""
        return """
        <div class="dashboard">
            <div class="page-header">
                <h1>Dashboard</h1>
                <p>Welcome to your enhanced web server dashboard</p>
            </div>
            
            <div class="dashboard-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
                <!-- System Status Card -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">System Status</h3>
                    </div>
                    <div class="card-body">
                        <div class="status-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div class="status-item">
                                <div class="status-label">CPU Usage</div>
                                <div class="status-value" id="cpu-usage">--</div>
                            </div>
                            <div class="status-item">
                                <div class="status-label">Memory</div>
                                <div class="status-value" id="memory-usage">--</div>
                            </div>
                            <div class="status-item">
                                <div class="status-label">Disk Space</div>
                                <div class="status-value" id="disk-usage">--</div>
                            </div>
                            <div class="status-item">
                                <div class="status-label">Uptime</div>
                                <div class="status-value" id="uptime">--</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Actions Card -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Quick Actions</h3>
                    </div>
                    <div class="card-body">
                        <div class="quick-actions" style="display: grid; gap: 1rem;">
                            <button class="btn btn-primary" onclick="window.enhancedUI.loadPage('files')">
                                📁 Manage Files
                            </button>
                            <button class="btn btn-primary" onclick="window.enhancedUI.loadPage('terminal')">
                                💻 Open Terminal
                            </button>
                            <button class="btn btn-primary" onclick="window.enhancedUI.loadPage('tunnels')">
                                🌐 Start Tunnel
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Recent Activity Card -->
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Recent Activity</h3>
                    </div>
                    <div class="card-body">
                        <div class="activity-list" id="activity-list">
                            <div class="activity-item" style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                                <div class="activity-text">System started</div>
                                <div class="activity-time" style="font-size: 0.875rem; color: var(--text-secondary);">Just now</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Dashboard-specific functionality
            function updateDashboard() {
                fetch('/api/system/status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            document.getElementById('cpu-usage').textContent = data.cpu_usage + '%';
                            document.getElementById('memory-usage').textContent = data.memory_usage + '%';
                            document.getElementById('disk-usage').textContent = data.disk_usage + '%';
                            document.getElementById('uptime').textContent = data.uptime;
                        }
                    })
                    .catch(error => console.error('Error updating dashboard:', error));
            }
            
            // Update dashboard every 30 seconds
            setInterval(updateDashboard, 30000);
            updateDashboard();
        </script>
        """

class AccessibilityManager:
    """Manage accessibility features and WCAG compliance."""
    
    def __init__(self):
        self.accessibility_features = {
            'high_contrast': False,
            'large_text': False,
            'reduced_motion': False,
            'screen_reader_support': True,
            'keyboard_navigation': True,
            'focus_indicators': True
        }
    
    def get_accessibility_css(self) -> str:
        """Generate accessibility-specific CSS."""
        return """
        /* High Contrast Mode */
        @media (prefers-contrast: high), .high-contrast {
            :root {
                --primary-color: #0066ff;
                --background-color: #000000;
                --surface-color: #1a1a1a;
                --text-color: #ffffff;
                --border-color: #666666;
            }
            
            .btn {
                border: 2px solid currentColor;
            }
        }
        
        /* Reduced Motion */
        @media (prefers-reduced-motion: reduce), .reduced-motion {
            *, *::before, *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* Large Text */
        @media (prefers-font-size: large), .large-text {
            html {
                font-size: 1.25em;
            }
        }
        
        /* Focus Management */
        .focus-trap {
            position: relative;
        }
        
        .focus-trap::before,
        .focus-trap::after {
            content: '';
            position: absolute;
            width: 1px;
            height: 1px;
            opacity: 0;
            pointer-events: none;
        }
        
        /* Skip Links */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--primary-color);
            color: white;
            padding: 8px;
            text-decoration: none;
            z-index: 9999;
            border-radius: 4px;
        }
        
        .skip-link:focus {
            top: 6px;
        }
        
        /* ARIA Live Regions */
        .sr-live {
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        }
        """
    
    def get_accessibility_js(self) -> str:
        """Generate accessibility JavaScript utilities."""
        return """
        class AccessibilityManager {
            constructor() {
                this.setupKeyboardNavigation();
                this.setupFocusManagement();
                this.setupAriaLiveRegions();
            }
            
            setupKeyboardNavigation() {
                document.addEventListener('keydown', (e) => {
                    // Escape key handling
                    if (e.key === 'Escape') {
                        this.handleEscape();
                    }
                    
                    // Tab trapping for modals
                    if (e.key === 'Tab') {
                        this.handleTabTrapping(e);
                    }
                });
            }
            
            setupFocusManagement() {
                // Add focus indicators for keyboard users
                document.addEventListener('keydown', () => {
                    document.body.classList.add('keyboard-navigation');
                });
                
                document.addEventListener('mousedown', () => {
                    document.body.classList.remove('keyboard-navigation');
                });
            }
            
            setupAriaLiveRegions() {
                // Create ARIA live region for announcements
                const liveRegion = document.createElement('div');
                liveRegion.setAttribute('aria-live', 'polite');
                liveRegion.setAttribute('aria-atomic', 'true');
                liveRegion.className = 'sr-live';
                liveRegion.id = 'aria-live-region';
                document.body.appendChild(liveRegion);
            }
            
            announce(message, priority = 'polite') {
                const liveRegion = document.getElementById('aria-live-region');
                liveRegion.setAttribute('aria-live', priority);
                liveRegion.textContent = message;
                
                // Clear after announcement
                setTimeout(() => {
                    liveRegion.textContent = '';
                }, 1000);
            }
            
            handleEscape() {
                // Close modals, dropdowns, etc.
                const activeModal = document.querySelector('.modal-overlay.active');
                if (activeModal) {
                    window.enhancedUI.hideModal();
                }
            }
            
            handleTabTrapping(e) {
                const modal = document.querySelector('.modal-overlay.active .modal');
                if (!modal) return;
                
                const focusableElements = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                if (e.shiftKey && document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                } else if (!e.shiftKey && document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
        
        // Initialize accessibility manager
        document.addEventListener('DOMContentLoaded', () => {
            window.accessibilityManager = new AccessibilityManager();
        });
        """

# Global UI manager instance
ui_manager = None
theme_manager = None

def initialize_ui_system() -> UIComponentManager:
    """Initialize UI management system."""
    global ui_manager, theme_manager
    theme_manager = ThemeManager()
    ui_manager = UIComponentManager(theme_manager)
    return ui_manager

def get_ui_manager() -> Optional[UIComponentManager]:
    """Get global UI manager."""
    return ui_manager

def get_theme_manager() -> Optional[ThemeManager]:
    """Get global theme manager."""
    return theme_manager