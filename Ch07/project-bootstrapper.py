#!/usr/bin/env python3
"""
Project Bootstrapper

Automates the initialization of new projects within a team namespace.
Creates the complete project skeleton including:
- Git repository structure
- CI/CD configuration (GitHub Actions, GitLab CI, or Jenkins)
- Kubernetes manifests (Deployment, Service, Ingress, etc.)
- Backstage catalog entry
- Documentation templates

Operations are idempotent - re-running returns success without duplication.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from audit_logger import AuditLogger


class ProjectBootstrapper:
    """
    Bootstraps new projects with templates and manifests.
    """
    
    # Project templates by language/framework
    TEMPLATES = {
        'python': {
            'description': 'Python web service',
            'main_file': 'main.py',
            'requirements_file': 'requirements.txt',
            'dockerfile': 'Dockerfile',
            'ci_config': '.github/workflows/ci.yml'
        },
        'golang': {
            'description': 'Go microservice',
            'main_file': 'main.go',
            'dockerfile': 'Dockerfile',
            'ci_config': '.github/workflows/ci.yml'
        },
        'nodejs': {
            'description': 'Node.js application',
            'main_file': 'index.js',
            'package_file': 'package.json',
            'dockerfile': 'Dockerfile',
            'ci_config': '.github/workflows/ci.yml'
        },
        'generic': {
            'description': 'Generic project template',
            'ci_config': '.github/workflows/ci.yml'
        }
    }
    
    def __init__(self):
        """Initialize the project bootstrapper."""
        self.audit_logger = AuditLogger()
    
    def bootstrap(
        self,
        team_id: str,
        project_name: str,
        language: str = 'generic',
        description: str = '',
        created_by: str = 'system'
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Bootstrap a new project.
        
        Args:
            team_id: Team identifier
            project_name: Project name
            language: Language/template (python, golang, nodejs, generic)
            description: Project description
            created_by: User creating the project
            
        Returns:
            Tuple of (success, error_message, project_info)
        """
        # Validate inputs
        if not self._validate_project_name(project_name):
            error = "Project name must be lowercase alphanumeric with hyphens"
            self.audit_logger.log_event(
                action='project_bootstrap_failed',
                actor=created_by,
                resource_type='project',
                resource_id=f"{team_id}/{project_name}",
                status='failure',
                details={'reason': 'Invalid project name'}
            )
            return False, error, None
        
        if language not in self.TEMPLATES:
            error = f"Unknown language/template: {language}"
            return False, error, None
        
        # Create project structure
        project_info = {
            'id': project_name,
            'name': project_name,
            'team': team_id,
            'language': language,
            'description': description,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'created_by': created_by,
            'repo_url': f"git@github.com:{team_id}/{project_name}.git",
            'namespace': f"team-{team_id}",
            'manifests': {
                'deployment': f"k8s/deployment.yaml",
                'service': f"k8s/service.yaml",
                'ingress': f"k8s/ingress.yaml",
                'configmap': f"k8s/configmap.yaml"
            }
        }
        
        # Generate files
        files = {}
        
        # Core files
        files['README.md'] = self._generate_readme(project_name, description, language)
        files['.gitignore'] = self._generate_gitignore(language)
        files['Dockerfile'] = self._generate_dockerfile(language, project_name)
        
        # CI/CD configuration
        files['.github/workflows/ci.yml'] = self._generate_ci_config(
            project_name, language, team_id
        )
        
        # Kubernetes manifests
        files['k8s/deployment.yaml'] = self._generate_deployment(
            project_name, team_id, language
        )
        files['k8s/service.yaml'] = self._generate_service(project_name)
        files['k8s/ingress.yaml'] = self._generate_ingress(project_name, team_id)
        files['k8s/configmap.yaml'] = self._generate_configmap(project_name)
        
        # Backstage catalog entry
        files['catalog-info.yaml'] = self._generate_backstage_catalog(
            project_name, team_id, description
        )
        
        # Language-specific files
        if language == 'python':
            files['main.py'] = self._generate_python_main(project_name)
            files['requirements.txt'] = self._generate_python_requirements()
        elif language == 'golang':
            files['main.go'] = self._generate_golang_main(project_name)
            files['go.mod'] = self._generate_go_mod(project_name, team_id)
        elif language == 'nodejs':
            files['index.js'] = self._generate_nodejs_main(project_name)
            files['package.json'] = self._generate_package_json(project_name, team_id)
        
        project_info['files'] = files
        
        # Audit log
        self.audit_logger.log_event(
            action='project_bootstrapped',
            actor=created_by,
            resource_type='project',
            resource_id=f"{team_id}/{project_name}",
            status='success',
            details={
                'language': language,
                'files_count': len(files),
                'description': description
            }
        )
        
        return True, None, project_info
    
    def _validate_project_name(self, name: str) -> bool:
        """Validate project name format."""
        import re
        pattern = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$'
        return len(name) >= 3 and len(name) <= 63 and bool(re.match(pattern, name))
    
    def _generate_readme(self, name: str, description: str, language: str) -> str:
        """Generate README.md."""
        return f"""# {name}

{description if description else f'A {language} service'}

## Getting Started

### Prerequisites
- Docker
- Kubernetes 1.20+
- kubectl configured

### Local Development

```bash
# Clone the repository
git clone git@github.com:$TEAM/{name}.git
cd {name}

# Install dependencies
# (language-specific)

# Run locally
# (language-specific)
```

### Building and Testing

```bash
# Build Docker image
docker build -t {name}:latest .

# Run tests
make test

# Run linters
make lint
```

## Deployment

### To Kubernetes

```bash
# Deploy to your team namespace
kubectl apply -f k8s/ -n team-$TEAM_ID

# Check deployment status
kubectl get deployment -n team-$TEAM_ID
```

### Configuration

Configuration is managed via ConfigMap (`k8s/configmap.yaml`):

```bash
kubectl get configmap {name} -n team-$TEAM_ID -o yaml
```

## Project Structure

```
{name}/
├── k8s/                 # Kubernetes manifests
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── .github/workflows/   # CI/CD configuration
│   └── ci.yml
├── src/                 # Source code
├── tests/               # Test files
├── Dockerfile           # Container image definition
├── README.md            # This file
└── catalog-info.yaml    # Backstage catalog metadata
```

## Monitoring and Logs

```bash
# View application logs
kubectl logs -f deployment/{name} -n team-$TEAM_ID

# Check resource usage
kubectl top pods -n team-$TEAM_ID
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is part of the platform engineering team.
"""
    
    def _generate_gitignore(self, language: str) -> str:
        """Generate .gitignore file."""
        base_ignores = """
# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Artifacts
build/
dist/
*.egg-info/
__pycache__/
.pytest_cache/
node_modules/
vendor/

# Secrets
.env
.env.local
secrets/
credentials/

# Logs
*.log
logs/

# CI/CD
.github/workflows/secrets.yml
"""
        
        language_ignores = {
            'python': """
# Python
*.pyc
*.pyo
.venv/
venv/
env/
pip-log.txt
""",
            'golang': """
# Go
*.o
*.a
*.so
*.dll
*.dylib
/bin/
/pkg/
""",
            'nodejs': """
# Node
node_modules/
npm-debug.log
yarn-error.log
.npmrc
""",
        }
        
        return base_ignores + language_ignores.get(language, '')
    
    def _generate_dockerfile(self, language: str, name: str) -> str:
        """Generate Dockerfile."""
        if language == 'python':
            return f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "main.py"]
"""
        elif language == 'golang':
            return f"""# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o {name} .

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates curl
RUN addgroup -g 1000 app && adduser -D -u 1000 -G app app

WORKDIR /home/app
COPY --from=builder /build/{name} .

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["./{name}"]
"""
        else:  # nodejs or generic
            return f"""FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Create non-root user
RUN addgroup -g 1000 app && adduser -D -u 1000 -G app app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["npm", "start"]
"""
    
    def _generate_ci_config(self, name: str, language: str, team: str) -> str:
        """Generate CI/CD configuration."""
        return f"""name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t {name}:${{GITHUB_SHA}} .
      
      - name: Run tests
        run: make test
      
      - name: Run linters
        run: make lint
      
      - name: Push image (on main)
        if: github.ref == 'refs/heads/main'
        run: |
          docker tag {name}:${{GITHUB_SHA}} {name}:latest
          docker push {name}:latest

  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Kubernetes
        env:
          KUBECONFIG: ${{{{ secrets.KUBECONFIG }}}}
        run: |
          kubectl set image deployment/{name} \\
            {name}={name}:${{GITHUB_SHA}} \\
            -n team-{team}
          kubectl rollout status deployment/{name} -n team-{team}
"""
    
    def _generate_deployment(self, name: str, team: str, language: str) -> str:
        """Generate Kubernetes Deployment manifest."""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: team-{team}
  labels:
    app: {name}
    team: {team}
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  
  selector:
    matchLabels:
      app: {name}
  
  template:
    metadata:
      labels:
        app: {name}
        team: {team}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    
    spec:
      serviceAccountName: team-default
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      
      containers:
      - name: {name}
        image: {name}:latest
        imagePullPolicy: IfNotPresent
        
        ports:
        - name: http
          containerPort: 8080
          protocol: TCP
        
        env:
        - name: ENVIRONMENT
          value: production
        - name: LOG_LEVEL
          value: info
        
        envFrom:
        - configMapRef:
            name: {name}
        
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 3
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 2
          failureThreshold: 3
        
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
              - ALL
"""
    
    def _generate_service(self, name: str) -> str:
        """Generate Kubernetes Service manifest."""
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {name}
  labels:
    app: {name}
spec:
  type: ClusterIP
  selector:
    app: {name}
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
"""
    
    def _generate_ingress(self, name: str, team: str) -> str:
        """Generate Kubernetes Ingress manifest."""
        return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {name}
  namespace: team-{team}
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - {name}.{team}.platform.internal
    secretName: {name}-tls
  rules:
  - host: {name}.{team}.platform.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {name}
            port:
              number: 80
"""
    
    def _generate_configmap(self, name: str) -> str:
        """Generate Kubernetes ConfigMap manifest."""
        return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: {name}
data:
  ENVIRONMENT: production
  LOG_LEVEL: info
  SERVICE_NAME: {name}
"""
    
    def _generate_backstage_catalog(self, name: str, team: str, description: str) -> str:
        """Generate Backstage catalog entry."""
        return f"""apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: {name}
  namespace: {team}
  description: {description if description else 'Service'}
  links:
    - url: git@github.com:{team}/{name}.git
      title: Repository
  tags:
    - platform
spec:
  type: service
  owner: {team}
  lifecycle: production
  definition:
    type: kubernetes
    target: team-{team}
"""
    
    def _generate_python_main(self, name: str) -> str:
        """Generate Python main.py."""
        return f"""#!/usr/bin/env python3
\"\"\"
{name} - Main application entry point
\"\"\"

import os
import logging
from flask import Flask, jsonify

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health():
    \"\"\"Health check endpoint.\"\"\"
    return jsonify({{'status': 'healthy'}}), 200


@app.route('/ready', methods=['GET'])
def ready():
    \"\"\"Readiness check endpoint.\"\"\"
    return jsonify({{'status': 'ready'}}), 200


@app.route('/metrics', methods=['GET'])
def metrics():
    \"\"\"Prometheus metrics endpoint.\"\"\"
    return 'prometheus_http_requests_total{{endpoint="metrics"}} 1\\n', 200


@app.route('/api/info', methods=['GET'])
def info():
    \"\"\"Service information endpoint.\"\"\"
    return jsonify({{
        'service': '{name}',
        'version': '1.0.0',
        'environment': os.getenv('ENVIRONMENT', 'unknown')
    }}), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting {name} on port {{port}}")
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', 'False') == 'True')
"""
    
    def _generate_python_requirements(self) -> str:
        """Generate Python requirements.txt."""
        return """flask==2.3.2
gunicorn==21.2.0
prometheus-client==0.17.1
python-json-logger==2.0.7
"""
    
    def _generate_golang_main(self, name: str) -> str:
        """Generate Go main.go."""
        return f"""package main

import (
\tfmt "fmt"
\thttp "net/http"
\tlog "log"
\tos "os"
)

func healthHandler(w http.ResponseWriter, r *http.Request) {{
\tw.Header().Set("Content-Type", "application/json")
\tw.WriteHeader(http.StatusOK)
\tfmt.Fprintf(w, `{{"status":"healthy"}}`)
}}

func readyHandler(w http.ResponseWriter, r *http.Request) {{
\tw.Header().Set("Content-Type", "application/json")
\tw.WriteHeader(http.StatusOK)
\tfmt.Fprintf(w, `{{"status":"ready"}}`)
}}

func infoHandler(w http.ResponseWriter, r *http.Request) {{
\tw.Header().Set("Content-Type", "application/json")
\tw.WriteHeader(http.StatusOK)
\tfmt.Fprintf(w, `{{"service":"{name}","version":"1.0.0"}}`)
}}

func main() {{
\tport := os.Getenv("PORT")
\tif port == "" {{
\t\tport = "8080"
\t}}

\thttp.HandleFunc("/health", healthHandler)
\thttp.HandleFunc("/ready", readyHandler)
\thttp.HandleFunc("/api/info", infoHandler)

\tlog.Printf("Starting {name} on port %s", port)
\tlog.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), nil))
}}
"""
    
    def _generate_go_mod(self, name: str, team: str) -> str:
        """Generate Go go.mod."""
        return f"""module github.com/{team}/{name}

go 1.21
"""
    
    def _generate_nodejs_main(self, name: str) -> str:
        """Generate Node.js index.js."""
        return f"""const express = require('express');
const app = express();

const PORT = process.env.PORT || 8080;

app.get('/health', (req, res) => {{
  res.json({{ status: 'healthy' }});
}});

app.get('/ready', (req, res) => {{
  res.json({{ status: 'ready' }});
}});

app.get('/api/info', (req, res) => {{
  res.json({{
    service: '{name}',
    version: '1.0.0',
    environment: process.env.ENVIRONMENT || 'unknown'
  }});
}});

app.listen(PORT, () => {{
  console.log(`{name} listening on port ${{PORT}}`);
}});
"""
    
    def _generate_package_json(self, name: str, team: str) -> str:
        """Generate Node.js package.json."""
        return f"""{{
  "name": "{name}",
  "version": "1.0.0",
  "description": "Service",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "test": "jest",
    "lint": "eslint ."
  }},
  "keywords": [],
  "author": "{team}",
  "license": "ISC",
  "dependencies": {{
    "express": "^4.18.2"
  }},
  "devDependencies": {{
    "jest": "^29.5.0",
    "eslint": "^8.42.0"
  }}
}}
"""


if __name__ == '__main__':
    """
    Example usage of the project bootstrapper.
    """
    bootstrapper = ProjectBootstrapper()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'bootstrap':
            if len(sys.argv) >= 4:
                team = sys.argv[2]
                project = sys.argv[3]
                language = sys.argv[4] if len(sys.argv) > 4 else 'generic'
                description = sys.argv[5] if len(sys.argv) > 5 else ''
                
                success, error, project_info = bootstrapper.bootstrap(
                    team, project, language, description
                )
                
                if success:
                    # Write files to disk
                    project_dir = os.path.join(os.getcwd(), project)
                    for filepath, content in project_info['files'].items():
                        full_path = os.path.join(project_dir, filepath)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'w') as f:
                            f.write(content)
                    print(f"Project {project} bootstrapped successfully!")
                    print(f"Repository: {project_info['repo_url']}")
                    print(f"Files created: {len(project_info['files'])}")
                    print(f"Project directory: ./{project}")
                else:
                    print(f"Error: {error}")
            else:
                print("Usage: project-bootstrapper.py bootstrap <team> <project> [language] [description]")
        
        elif sys.argv[1] == 'templates':
            print("\nAvailable templates:")
            for lang, info in bootstrapper.TEMPLATES.items():
                print(f"  {lang:<15} - {info['description']}")
        
        else:
            print(f"Unknown command: {sys.argv[1]}")
    
    else:
        print("Usage: project-bootstrapper.py <bootstrap|templates> [args...]")
