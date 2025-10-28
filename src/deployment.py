#!/usr/bin/env python3
"""
Advanced deployment and containerization system.
Provides Docker containerization, Kubernetes deployment, and automated deployment pipelines.
"""

import os
import yaml
import json
import subprocess
import shutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class DockerManager:
    """Manage Docker containerization."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.dockerfile_path = self.project_root / "Dockerfile"
        self.dockerignore_path = self.project_root / ".dockerignore"
        self.compose_path = self.project_root / "docker-compose.yml"
    
    def generate_dockerfile(self, python_version: str = "3.11") -> str:
        """Generate optimized Dockerfile."""
        dockerfile_content = f"""# Multi-stage build for production optimization
FROM python:{python_version}-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:{python_version}-slim as production

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    procps \\
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY requirements.txt ./

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/backups /app/data/files /app/data/programs && \\
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "src/enhanced_app.py"]
"""
        return dockerfile_content
    
    def generate_dockerignore(self) -> str:
        """Generate .dockerignore file."""
        dockerignore_content = """# Development files
.git
.gitignore
.env
.venv
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Logs and temporary files
*.log
logs/
tmp/
temp/

# Test files
tests/
test_*.py
*_test.py

# Documentation
docs/
*.md
!README.md

# Build artifacts
dist/
build/
*.egg-info/

# Coverage reports
htmlcov/
.coverage
.pytest_cache/

# Backup files
backups/
*.backup
*.bak

# Large files
*.iso
*.dmg
*.gz
*.zip
*.tar
"""
        return dockerignore_content
    
    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml for development and production."""
        compose_content = """version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - PYTHONPATH=/app/src
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - webserver_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - webserver_network
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - webserver_network

volumes:
  redis_data:

networks:
  webserver_network:
    driver: bridge
"""
        return compose_content
    
    def generate_nginx_config(self) -> str:
        """Generate nginx configuration for reverse proxy."""
        nginx_content = """events {
    worker_connections 1024;
}

http {
    upstream webserver {
        server web:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=1r/s;

    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    server {
        listen 80;
        server_name localhost;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/ssl/certs/server.crt;
        ssl_certificate_key /etc/ssl/certs/server.key;

        # Security configurations
        client_max_body_size 100M;
        client_body_timeout 60s;
        client_header_timeout 60s;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://webserver;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # File upload endpoints
        location ~ ^/(upload|files)/ {
            limit_req zone=upload burst=5 nodelay;
            proxy_pass http://webserver;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_request_buffering off;
        }

        # WebSocket support
        location /socket.io/ {
            proxy_pass http://webserver;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Main application
        location / {
            proxy_pass http://webserver;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files (if served by nginx)
        location /static/ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
"""
        return nginx_content
    
    def create_deployment_files(self):
        """Create all Docker deployment files."""
        try:
            # Create Dockerfile
            with open(self.dockerfile_path, 'w') as f:
                f.write(self.generate_dockerfile())
            logger.info("Created Dockerfile")
            
            # Create .dockerignore
            with open(self.dockerignore_path, 'w') as f:
                f.write(self.generate_dockerignore())
            logger.info("Created .dockerignore")
            
            # Create docker-compose.yml
            with open(self.compose_path, 'w') as f:
                f.write(self.generate_docker_compose())
            logger.info("Created docker-compose.yml")
            
            # Create nginx configuration
            nginx_path = self.project_root / "nginx.conf"
            with open(nginx_path, 'w') as f:
                f.write(self.generate_nginx_config())
            logger.info("Created nginx.conf")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating deployment files: {e}")
            return False
    
    def build_image(self, tag: str = "webserver:latest") -> bool:
        """Build Docker image."""
        try:
            cmd = ["docker", "build", "-t", tag, "."]
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully built Docker image: {tag}")
                return True
            else:
                logger.error(f"Docker build failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error building Docker image: {e}")
            return False
    
    def run_container(self, tag: str = "webserver:latest", port: int = 8000) -> bool:
        """Run Docker container."""
        try:
            cmd = [
                "docker", "run", "-d",
                "-p", f"{port}:8000",
                "-v", f"{self.project_root}/data:/app/data",
                "-v", f"{self.project_root}/logs:/app/logs",
                "--name", "webserver",
                tag
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully started container on port {port}")
                return True
            else:
                logger.error(f"Failed to run container: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error running container: {e}")
            return False

class KubernetesManager:
    """Manage Kubernetes deployment."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.k8s_dir = self.project_root / "k8s"
    
    def create_k8s_manifests(self):
        """Create Kubernetes deployment manifests."""
        try:
            self.k8s_dir.mkdir(exist_ok=True)
            
            # Namespace
            self._create_namespace()
            
            # ConfigMap
            self._create_configmap()
            
            # Secret
            self._create_secret()
            
            # Deployment
            self._create_deployment()
            
            # Service
            self._create_service()
            
            # Ingress
            self._create_ingress()
            
            # HorizontalPodAutoscaler
            self._create_hpa()
            
            # Redis deployment
            self._create_redis_deployment()
            
            logger.info("Created Kubernetes manifests")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Kubernetes manifests: {e}")
            return False
    
    def _create_namespace(self):
        """Create namespace manifest."""
        namespace = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": "webserver",
                "labels": {
                    "name": "webserver"
                }
            }
        }
        
        with open(self.k8s_dir / "namespace.yaml", 'w') as f:
            yaml.dump(namespace, f, default_flow_style=False)
    
    def _create_configmap(self):
        """Create ConfigMap manifest."""
        configmap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": "webserver-config",
                "namespace": "webserver"
            },
            "data": {
                "FLASK_ENV": "production",
                "PYTHONPATH": "/app/src",
                "REDIS_URL": "redis://redis-service:6379/0",
                "LOG_LEVEL": "INFO"
            }
        }
        
        with open(self.k8s_dir / "configmap.yaml", 'w') as f:
            yaml.dump(configmap, f, default_flow_style=False)
    
    def _create_secret(self):
        """Create Secret manifest."""
        secret = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": "webserver-secret",
                "namespace": "webserver"
            },
            "type": "Opaque",
            "data": {
                # Base64 encoded values (these should be properly encoded in real deployment)
                "SECRET_KEY": "Y2hhbmdlLW1lLWluLXByb2R1Y3Rpb24=",  # change-me-in-production
                "DATABASE_URL": "c3FsaXRlOi8vL2FwcC9kYXRhL2RhdGFiYXNlLmRi"  # sqlite:///app/data/database.db
            }
        }
        
        with open(self.k8s_dir / "secret.yaml", 'w') as f:
            yaml.dump(secret, f, default_flow_style=False)
    
    def _create_deployment(self):
        """Create Deployment manifest."""
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "webserver",
                "namespace": "webserver",
                "labels": {
                    "app": "webserver"
                }
            },
            "spec": {
                "replicas": 3,
                "selector": {
                    "matchLabels": {
                        "app": "webserver"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "webserver"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "webserver",
                            "image": "webserver:latest",
                            "ports": [{
                                "containerPort": 8000
                            }],
                            "envFrom": [{
                                "configMapRef": {
                                    "name": "webserver-config"
                                }
                            }, {
                                "secretRef": {
                                    "name": "webserver-secret"
                                }
                            }],
                            "resources": {
                                "requests": {
                                    "memory": "256Mi",
                                    "cpu": "250m"
                                },
                                "limits": {
                                    "memory": "512Mi",
                                    "cpu": "500m"
                                }
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": 8000
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/health",
                                    "port": 8000
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            },
                            "volumeMounts": [{
                                "name": "data-volume",
                                "mountPath": "/app/data"
                            }, {
                                "name": "logs-volume",
                                "mountPath": "/app/logs"
                            }]
                        }],
                        "volumes": [{
                            "name": "data-volume",
                            "persistentVolumeClaim": {
                                "claimName": "webserver-data-pvc"
                            }
                        }, {
                            "name": "logs-volume",
                            "persistentVolumeClaim": {
                                "claimName": "webserver-logs-pvc"
                            }
                        }]
                    }
                }
            }
        }
        
        with open(self.k8s_dir / "deployment.yaml", 'w') as f:
            yaml.dump(deployment, f, default_flow_style=False)
    
    def _create_service(self):
        """Create Service manifest."""
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "webserver-service",
                "namespace": "webserver"
            },
            "spec": {
                "selector": {
                    "app": "webserver"
                },
                "ports": [{
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 8000
                }],
                "type": "ClusterIP"
            }
        }
        
        with open(self.k8s_dir / "service.yaml", 'w') as f:
            yaml.dump(service, f, default_flow_style=False)
    
    def _create_ingress(self):
        """Create Ingress manifest."""
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "webserver-ingress",
                "namespace": "webserver",
                "annotations": {
                    "nginx.ingress.kubernetes.io/rewrite-target": "/",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                    "nginx.ingress.kubernetes.io/rate-limit": "100",
                    "nginx.ingress.kubernetes.io/rate-limit-window": "1m"
                }
            },
            "spec": {
                "tls": [{
                    "hosts": ["webserver.local"],
                    "secretName": "webserver-tls"
                }],
                "rules": [{
                    "host": "webserver.local",
                    "http": {
                        "paths": [{
                            "path": "/",
                            "pathType": "Prefix",
                            "backend": {
                                "service": {
                                    "name": "webserver-service",
                                    "port": {
                                        "number": 80
                                    }
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        with open(self.k8s_dir / "ingress.yaml", 'w') as f:
            yaml.dump(ingress, f, default_flow_style=False)
    
    def _create_hpa(self):
        """Create HorizontalPodAutoscaler manifest."""
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "webserver-hpa",
                "namespace": "webserver"
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "webserver"
                },
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": 70
                        }
                    }
                }, {
                    "type": "Resource",
                    "resource": {
                        "name": "memory",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": 80
                        }
                    }
                }]
            }
        }
        
        with open(self.k8s_dir / "hpa.yaml", 'w') as f:
            yaml.dump(hpa, f, default_flow_style=False)
    
    def _create_redis_deployment(self):
        """Create Redis deployment manifest."""
        redis_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "redis",
                "namespace": "webserver"
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": "redis"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "redis"
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "redis",
                            "image": "redis:7-alpine",
                            "ports": [{
                                "containerPort": 6379
                            }],
                            "resources": {
                                "requests": {
                                    "memory": "128Mi",
                                    "cpu": "100m"
                                },
                                "limits": {
                                    "memory": "256Mi",
                                    "cpu": "200m"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        redis_service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "redis-service",
                "namespace": "webserver"
            },
            "spec": {
                "selector": {
                    "app": "redis"
                },
                "ports": [{
                    "protocol": "TCP",
                    "port": 6379,
                    "targetPort": 6379
                }]
            }
        }
        
        with open(self.k8s_dir / "redis.yaml", 'w') as f:
            yaml.dump_all([redis_deployment, redis_service], f, default_flow_style=False)

class DeploymentManager:
    """Main deployment management system."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.docker_manager = DockerManager(project_root)
        self.k8s_manager = KubernetesManager(project_root)
    
    def create_deployment_package(self, deployment_type: str = "docker") -> bool:
        """Create complete deployment package."""
        try:
            logger.info(f"Creating {deployment_type} deployment package...")
            
            if deployment_type == "docker":
                success = self.docker_manager.create_deployment_files()
                if success:
                    # Create additional scripts
                    self._create_docker_scripts()
                    
            elif deployment_type == "kubernetes":
                success = self.k8s_manager.create_k8s_manifests()
                if success:
                    # Create additional scripts
                    self._create_k8s_scripts()
                    
            elif deployment_type == "both":
                docker_success = self.docker_manager.create_deployment_files()
                k8s_success = self.k8s_manager.create_k8s_manifests()
                success = docker_success and k8s_success
                
                if success:
                    self._create_docker_scripts()
                    self._create_k8s_scripts()
            else:
                logger.error(f"Unknown deployment type: {deployment_type}")
                return False
            
            if success:
                self._create_deployment_docs()
                logger.info("Deployment package created successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating deployment package: {e}")
            return False
    
    def _create_docker_scripts(self):
        """Create Docker deployment scripts."""
        # Build script
        build_script = """#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t webserver:latest .

echo "Tagging image..."
docker tag webserver:latest webserver:$(date +%Y%m%d-%H%M%S)

echo "Build completed successfully!"
"""
        
        # Deploy script
        deploy_script = """#!/bin/bash
set -e

echo "Deploying with Docker Compose..."
docker-compose down
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Checking service health..."
docker-compose ps

echo "Deployment completed successfully!"
echo "Access the application at: http://localhost:8000"
"""
        
        # Update script
        update_script = """#!/bin/bash
set -e

echo "Updating deployment..."
docker-compose pull
docker-compose down
docker-compose up -d

echo "Update completed successfully!"
"""
        
        scripts = {
            "build.sh": build_script,
            "deploy.sh": deploy_script,
            "update.sh": update_script
        }
        
        for script_name, content in scripts.items():
            script_path = self.project_root / script_name
            with open(script_path, 'w') as f:
                f.write(content)
            script_path.chmod(0o755)
    
    def _create_k8s_scripts(self):
        """Create Kubernetes deployment scripts."""
        # Deploy script
        deploy_script = """#!/bin/bash
set -e

echo "Deploying to Kubernetes..."
kubectl apply -f k8s/

echo "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/webserver -n webserver

echo "Checking pod status..."
kubectl get pods -n webserver

echo "Deployment completed successfully!"
echo "Access the application using the ingress configuration"
"""
        
        # Update script
        update_script = """#!/bin/bash
set -e

echo "Updating Kubernetes deployment..."
kubectl set image deployment/webserver webserver=webserver:latest -n webserver

echo "Waiting for rollout to complete..."
kubectl rollout status deployment/webserver -n webserver

echo "Update completed successfully!"
"""
        
        # Cleanup script
        cleanup_script = """#!/bin/bash
set -e

echo "Cleaning up Kubernetes resources..."
kubectl delete -f k8s/ || true

echo "Cleanup completed!"
"""
        
        scripts = {
            "k8s-deploy.sh": deploy_script,
            "k8s-update.sh": update_script,
            "k8s-cleanup.sh": cleanup_script
        }
        
        for script_name, content in scripts.items():
            script_path = self.project_root / script_name
            with open(script_path, 'w') as f:
                f.write(content)
            script_path.chmod(0o755)
    
    def _create_deployment_docs(self):
        """Create deployment documentation."""
        docs = f"""# Deployment Guide

## Prerequisites

### Docker Deployment
- Docker Engine 20.10+
- Docker Compose 2.0+

### Kubernetes Deployment
- Kubernetes 1.20+
- kubectl configured
- Helm 3.0+ (optional)

## Quick Start

### Docker Deployment
```bash
# Build and deploy
./build.sh
./deploy.sh

# Access the application
open http://localhost:8000
```

### Kubernetes Deployment
```bash
# Deploy to Kubernetes
./k8s-deploy.sh

# Check status
kubectl get pods -n webserver
```

## Configuration

### Environment Variables
- `FLASK_ENV`: Application environment (development/production)
- `SECRET_KEY`: Flask secret key
- `REDIS_URL`: Redis connection URL
- `LOG_LEVEL`: Logging level

### Security
- SSL/TLS certificates should be mounted in production
- Update default secrets and passwords
- Configure proper CORS origins
- Set up proper authentication

### Monitoring
- Health check endpoint: `/health`
- Metrics endpoint: `/metrics`
- Logs are available in `/app/logs`

## Scaling

### Docker
Use Docker Compose scaling:
```bash
docker-compose up -d --scale web=3
```

### Kubernetes
Horizontal Pod Autoscaler is configured to scale based on CPU/memory usage.
Manual scaling:
```bash
kubectl scale deployment webserver --replicas=5 -n webserver
```

## Troubleshooting

### Common Issues
1. Port conflicts: Change port mappings in docker-compose.yml
2. Permission issues: Check file ownership and container user
3. Database issues: Verify volume mounts and permissions

### Logs
```bash
# Docker
docker-compose logs -f web

# Kubernetes
kubectl logs -f deployment/webserver -n webserver
```

## Security Considerations

1. **Secrets Management**: Use proper secret management in production
2. **Network Security**: Configure firewalls and network policies
3. **Container Security**: Run containers as non-root user
4. **Image Security**: Regularly update base images and scan for vulnerabilities
5. **Data Protection**: Encrypt data at rest and in transit

## Backup and Recovery

### Data Backup
```bash
# Docker
docker run --rm -v webserver_data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Kubernetes
kubectl exec -n webserver deployment/webserver -- tar czf - /app/data > backup.tar.gz
```

### Restore
```bash
# Docker
docker run --rm -v webserver_data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /

# Kubernetes
kubectl exec -n webserver deployment/webserver -- tar xzf - -C / < backup.tar.gz
```

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(self.project_root / "DEPLOYMENT.md", 'w') as f:
            f.write(docs)

# Global deployment manager
deployment_manager = None

def initialize_deployment(project_root: str = ".") -> DeploymentManager:
    """Initialize deployment system."""
    global deployment_manager
    deployment_manager = DeploymentManager(project_root)
    return deployment_manager

def get_deployment_manager() -> Optional[DeploymentManager]:
    """Get global deployment manager."""
    return deployment_manager