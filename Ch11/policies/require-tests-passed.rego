package requiretestspassed

# Deny deployments that don't have test results annotation or test-results != "passed"
deny[msg] {
  input.kind == "Deployment"
  not input.metadata.annotations["test-results"]
  msg := sprintf(
    "Deployment %v/%v must have 'test-results' annotation",
    [input.metadata.namespace, input.metadata.name]
  )
}

deny[msg] {
  input.kind == "Deployment"
  test_results := input.metadata.annotations["test-results"]
  test_results != "passed"
  msg := sprintf(
    "Deployment %v/%v has test-results=%v, but must be 'passed'",
    [input.metadata.namespace, input.metadata.name, test_results]
  )
}

# Allow if annotation exists and is set to "passed"
allow {
  input.kind == "Deployment"
  input.metadata.annotations["test-results"] == "passed"
}
