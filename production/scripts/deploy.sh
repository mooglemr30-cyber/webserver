#!/bin/bash
# Production deployment script
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
IMAGE_NAME="${IMAGE_NAME:-webserver}"
IMAGE_TAG="${IMAGE_TAG:-production}"
NAMESPACE="${NAMESPACE:-webserver-prod}"

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# Functions
check_requirements() {
    log "Checking system requirements..."
    
    local missing_tools=()
    
    # Check required tools
    for tool in docker kubectl helm; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    success "All requirements met"
}

build_image() {
    log "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build the production image
    docker build \
        -f production/docker/Dockerfile.production \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_NAME}:latest" \
        .
    
    success "Docker image built successfully"
}

push_image() {
    log "Pushing Docker image to registry..."
    
    # Tag for registry
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
    
    # Push to registry
    docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${DOCKER_REGISTRY}/${IMAGE_NAME}:latest"
    
    success "Docker image pushed successfully"
}

deploy_kubernetes() {
    log "Deploying to Kubernetes..."
    
    cd "$PROJECT_ROOT/production/k8s"
    
    # Create namespace if it doesn't exist
    kubectl get namespace "$NAMESPACE" &> /dev/null || kubectl create namespace "$NAMESPACE"
    
    # Apply configurations in order
    local manifests=(
        "namespace.yaml"
        "secrets.yaml"
        "configmap.yaml"
        "pvc.yaml"
        "deployment.yaml"
        "service.yaml"
        "ingress.yaml"
        "hpa.yaml"
    )
    
    for manifest in "${manifests[@]}"; do
        if [ -f "$manifest" ]; then
            log "Applying $manifest..."
            kubectl apply -f "$manifest"
        else
            warn "$manifest not found, skipping..."
        fi
    done
    
    success "Kubernetes deployment completed"
}

wait_for_deployment() {
    log "Waiting for deployment to be ready..."
    
    # Wait for webserver deployment
    kubectl wait --for=condition=available --timeout=300s deployment/webserver-deployment -n "$NAMESPACE"
    
    # Wait for redis deployment
    kubectl wait --for=condition=available --timeout=300s deployment/redis-deployment -n "$NAMESPACE"
    
    # Wait for nginx deployment
    kubectl wait --for=condition=available --timeout=300s deployment/nginx-deployment -n "$NAMESPACE"
    
    success "All deployments are ready"
}

run_health_check() {
    log "Running health checks..."
    
    # Get service URL
    local service_url
    if kubectl get service nginx-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' &> /dev/null; then
        service_url="http://$(kubectl get service nginx-service -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
    else
        # Use port-forward for local testing
        kubectl port-forward service/nginx-service 8080:80 -n "$NAMESPACE" &
        local port_forward_pid=$!
        sleep 5
        service_url="http://localhost:8080"
    fi
    
    # Health check
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "${service_url}/health" &> /dev/null; then
            success "Health check passed"
            [ -n "${port_forward_pid:-}" ] && kill $port_forward_pid &> /dev/null || true
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
    [ -n "${port_forward_pid:-}" ] && kill $port_forward_pid &> /dev/null || true
    return 1
}

cleanup() {
    log "Cleaning up temporary resources..."
    
    # Kill any background processes
    jobs -p | xargs -r kill &> /dev/null || true
    
    success "Cleanup completed"
}

rollback() {
    warn "Rolling back deployment..."
    
    # Rollback deployments
    kubectl rollout undo deployment/webserver-deployment -n "$NAMESPACE"
    kubectl rollout undo deployment/nginx-deployment -n "$NAMESPACE"
    
    # Wait for rollback
    kubectl rollout status deployment/webserver-deployment -n "$NAMESPACE"
    kubectl rollout status deployment/nginx-deployment -n "$NAMESPACE"
    
    success "Rollback completed"
}

show_status() {
    log "Deployment status:"
    
    echo "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    echo -e "\nServices:"
    kubectl get services -n "$NAMESPACE" -o wide
    
    echo -e "\nIngress:"
    kubectl get ingress -n "$NAMESPACE" -o wide
    
    echo -e "\nHPA:"
    kubectl get hpa -n "$NAMESPACE" -o wide
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS] COMMAND

Production deployment script for webserver

COMMANDS:
    build       Build Docker image
    push        Push Docker image to registry
    deploy      Deploy to Kubernetes
    full        Run full deployment (build + push + deploy)
    status      Show deployment status
    health      Run health check
    rollback    Rollback to previous version
    cleanup     Clean up resources

OPTIONS:
    -h, --help          Show this help message
    -n, --namespace     Kubernetes namespace (default: webserver-prod)
    -r, --registry      Docker registry (default: localhost:5000)
    -t, --tag           Image tag (default: production)
    --skip-checks       Skip requirement checks
    --no-push           Skip pushing to registry (for local deployments)

EXAMPLES:
    $0 full                                 # Full deployment
    $0 -n staging deploy                    # Deploy to staging namespace
    $0 -t v2.1.0 build push                # Build and push specific version
    $0 --no-push deploy                     # Local deployment without registry

EOF
}

# Parse command line arguments
SKIP_CHECKS=false
NO_PUSH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--registry)
            DOCKER_REGISTRY="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --no-push)
            NO_PUSH=true
            shift
            ;;
        build|push|deploy|full|status|health|rollback|cleanup)
            COMMAND="$1"
            shift
            break
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Set up trap for cleanup
trap cleanup EXIT

# Main execution
case "${COMMAND:-}" in
    build)
        [ "$SKIP_CHECKS" = false ] && check_requirements
        build_image
        ;;
    push)
        [ "$SKIP_CHECKS" = false ] && check_requirements
        push_image
        ;;
    deploy)
        [ "$SKIP_CHECKS" = false ] && check_requirements
        deploy_kubernetes
        wait_for_deployment
        run_health_check
        show_status
        ;;
    full)
        [ "$SKIP_CHECKS" = false ] && check_requirements
        build_image
        [ "$NO_PUSH" = false ] && push_image
        deploy_kubernetes
        wait_for_deployment
        run_health_check
        show_status
        ;;
    status)
        show_status
        ;;
    health)
        run_health_check
        ;;
    rollback)
        rollback
        ;;
    cleanup)
        log "Manual cleanup requested"
        ;;
    *)
        error "No command specified"
        usage
        exit 1
        ;;
esac

success "Operation completed successfully"