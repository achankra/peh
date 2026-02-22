# conftest Rego Policies for Shift-Left Validation
# These policies validate Kubernetes manifests before deployment
# Run with: conftest test -p policy.rego *.yaml

package main

# Require resource limits on all containers
deny[msg] {
    container := input.spec.containers[_]
    not container.resources.limits.cpu
    msg := sprintf("Container '%v' missing CPU limits", [container.name])
}

deny[msg] {
    container := input.spec.containers[_]
    not container.resources.limits.memory
    msg := sprintf("Container '%v' missing memory limits", [container.name])
}

deny[msg] {
    container := input.spec.containers[_]
    not container.resources.requests.cpu
    msg := sprintf("Container '%v' missing CPU requests", [container.name])
}

deny[msg] {
    container := input.spec.containers[_]
    not container.resources.requests.memory
    msg := sprintf("Container '%v' missing memory requests", [container.name])
}

# Warn on latest image tag (better: use specific versions)
warn[msg] {
    container := input.spec.containers[_]
    endswith(container.image, ":latest")
    msg := sprintf("Container '%v' uses ':latest' tag (use specific versions)", [container.name])
}

# Deny privileged containers
deny[msg] {
    container := input.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container '%v' cannot run in privileged mode", [container.name])
}

# Require non-root user
deny[msg] {
    container := input.spec.containers[_]
    container.securityContext.runAsUser == 0
    msg := sprintf("Container '%v' cannot run as root (UID 0)", [container.name])
}

# Require readOnlyRootFilesystem for security
warn[msg] {
    container := input.spec.containers[_]
    container.securityContext.readOnlyRootFilesystem != true
    msg := sprintf("Container '%v' should set readOnlyRootFilesystem to true", [container.name])
}

# Require allowPrivilegeEscalation disabled
deny[msg] {
    container := input.spec.containers[_]
    container.securityContext.allowPrivilegeEscalation != false
    msg := sprintf("Container '%v' must set allowPrivilegeEscalation to false", [container.name])
}

# Require specific image registries
deny[msg] {
    container := input.spec.containers[_]
    not allowed_registry(container.image)
    msg := sprintf("Container '%v' image not from allowed registry: %v", [container.name, container.image])
}

allowed_registry(image) {
    registries := ["gcr.io/", "quay.io/", "docker.io/library/", "k8s.gcr.io/"]
    startswith(image, registries[_])
}

# Require mandatory labels
deny[msg] {
    not input.metadata.labels.team
    msg := "Deployment missing 'team' label"
}

deny[msg] {
    not input.metadata.labels.owner
    msg := "Deployment missing 'owner' label"
}

deny[msg] {
    not input.metadata.labels["cost-center"]
    msg := "Deployment missing 'cost-center' label"
}

# Warn on missing resource limits at pod level
warn[msg] {
    input.apiVersion
    not input.spec.containers
    msg := "Pod spec missing containers"
}

# Rego rules that pass (no deny/warn)
pass_basic {
    input.apiVersion
    input.kind
    input.metadata.name
}
