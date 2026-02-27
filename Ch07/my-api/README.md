# my-api

RESTful API service

## Getting Started

### Prerequisites
- Docker
- Kubernetes 1.20+
- kubectl configured

### Local Development

```bash
# Clone the repository
git clone git@github.com:$TEAM/my-api.git
cd my-api

# Install dependencies
# (language-specific)

# Run locally
# (language-specific)
```

### Building and Testing

```bash
# Build Docker image
docker build -t my-api:latest .

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
kubectl get configmap my-api -n team-$TEAM_ID -o yaml
```

## Project Structure

```
my-api/
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
kubectl logs -f deployment/my-api -n team-$TEAM_ID

# Check resource usage
kubectl top pods -n team-$TEAM_ID
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is part of the platform engineering team.
