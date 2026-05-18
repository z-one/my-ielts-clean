#!/bin/bash

# IELTS vocabulary app build helper.
#
# Default behavior does not build Docker images. Use:
#   bash build.sh image [production|dev]
# when you really want to run docker compose build.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="$ROOT_DIR/docker"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_DIR="$ROOT_DIR/backend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat <<'EOF'
Usage:
  bash build.sh [all] [docker|local|production]
                                      Build frontend and check backend. No Docker image is built by default.
  bash build.sh frontend [docker|local|production]
                                      Build frontend only.
  bash build.sh backend                Check backend only.
  bash build.sh image [production|dev] Build frontend/backend, then build Docker images.

Hint:
  Default frontend build mode is "docker", so generated dist uses same-origin /api.
  local mode writes http://localhost:8000 at build time for local preview/static testing.
  production mode also uses same-origin /api for the Docker nginx proxy.
  Default command is "all"; it will not run docker-compose build.
  Use "image" explicitly if you need Docker image packaging.
EOF
}

print_no_image_hint() {
    print_warn "Default/non-image build finished. Docker images were not built."
    print_info "To package images, run: bash build.sh image [production|dev]"
}

select_python() {
    if command -v "${PYTHON_BIN:-python}" >/dev/null 2>&1; then
        echo "${PYTHON_BIN:-python}"
        return
    fi

    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
        return
    fi

    print_error "Python was not found. Install Python or set PYTHON_BIN=/path/to/python."
    exit 1
}

resolve_frontend_build_script() {
    local mode="${1:-docker}"

    case "$mode" in
        docker)
            echo "build:docker"
            ;;
        local|development|dev|test)
            echo "build:local"
            ;;
        production|prod)
            echo "build:prod"
            ;;
        *)
            print_error "Unknown frontend build mode: $mode"
            print_info "Supported frontend build modes: docker, local, production"
            exit 1
            ;;
    esac
}

build_frontend() {
    local build_mode="${1:-docker}"
    local build_script

    build_script="$(resolve_frontend_build_script "$build_mode")"
    print_info "Building frontend with mode: $build_mode"
    cd "$FRONTEND_DIR"

    if command -v pnpm >/dev/null 2>&1; then
        print_info "Using pnpm run $build_script"
        pnpm run "$build_script"
    else
        print_warn "pnpm was not found; falling back to npm run $build_script"
        npm run "$build_script"
    fi

    if [ ! -d "$FRONTEND_DIR/dist" ]; then
        print_error "Frontend build output does not exist: $FRONTEND_DIR/dist"
        exit 1
    fi

    print_info "Copying frontend dist into docker/frontend..."
    mkdir -p "$DOCKER_DIR/frontend"
    rm -rf "$DOCKER_DIR/frontend/dist"
    cp -r "$FRONTEND_DIR/dist" "$DOCKER_DIR/frontend/"
}

build_backend() {
    print_info "Checking backend Python files..."
    local python_bin
    python_bin="$(select_python)"

    cd "$BACKEND_DIR"
    "$python_bin" -m compileall -q app
}

resolve_compose_file() {
    local env_name="${1:-production}"

    case "$env_name" in
        production|prod)
            echo "$DOCKER_DIR/docker-compose.yml"
            ;;
        development|dev)
            echo "$DOCKER_DIR/docker-compose.dev.yml"
            ;;
        *)
            print_error "Unknown environment: $env_name"
            print_info "Supported environments: production, dev"
            exit 1
            ;;
    esac
}

select_compose_cmd() {
    if command -v docker-compose >/dev/null 2>&1; then
        echo "docker-compose"
        return
    fi

    if docker compose version >/dev/null 2>&1; then
        echo "docker compose"
        return
    fi

    print_error "Docker Compose was not found. Install docker-compose or Docker Compose v2."
    exit 1
}

build_images() {
    local env_name="${1:-production}"
    local compose_file
    local compose_cmd

    print_warn "Docker image packaging requested explicitly."

    if ! command -v docker >/dev/null 2>&1; then
        print_error "Docker was not found. Install Docker first."
        exit 1
    fi

    compose_file="$(resolve_compose_file "$env_name")"
    if [ ! -f "$compose_file" ]; then
        print_error "Compose file does not exist: $compose_file"
        exit 1
    fi

    compose_cmd="$(select_compose_cmd)"
    print_info "Using compose file: $compose_file"
    print_info "Building Docker images..."
    cd "$DOCKER_DIR"
    $compose_cmd -f "$compose_file" build

    print_info "Docker image build finished."
    print_info "Start command: $compose_cmd -f $compose_file up -d"
}

run_all_without_images() {
    local frontend_mode="${1:-docker}"
    print_info "Default build: frontend build + backend check only."
    print_warn "Docker image packaging is skipped by default."
    build_frontend "$frontend_mode"
    build_backend
    print_no_image_hint
}

COMMAND="${1:-all}"
ENV_NAME="${2:-docker}"

case "$COMMAND" in
    all|"")
        run_all_without_images "$ENV_NAME"
        ;;
    frontend|front|fe)
        build_frontend "$ENV_NAME"
        print_no_image_hint
        ;;
    backend|back|be)
        build_backend
        print_no_image_hint
        ;;
    image|images|docker)
        build_frontend docker
        build_backend
        build_images "${2:-production}"
        ;;
    production|prod|development|dev)
        print_warn "Environment-only usage no longer builds Docker images by default."
        print_info "Running app build/check only. Use: bash build.sh image $COMMAND"
        run_all_without_images "$COMMAND"
        ;;
    help|-h|--help)
        usage
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
