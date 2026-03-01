package requiretestspassed

import rego.v1

# Deny deployments that don't have test results annotation or test-results != "passed"
deny contains msg if {
  input.kind == "Deployment"
  not input.metadata.annotations["test-results"]
  msg := sprintf(
    "Deployment %v/%v must have 'test-results' annotation",
    [input.metadata.namespace, input.metadata.name]
  )
}

deny contains msg if {
  input.kind == "Deployment"
  test_results := input.metadata.annotations["test-results"]
  test_results != "passed"
  msg := sprintf(
    "Deployment %v/%v has test-results=%v, but must be 'passed'",
    [input.metadata.namespace, input.metadata.name, test_results]
  )
}

# Allow if annotation exists and is set to "passed"
allow if {
  input.kind == "Deployment"
  input.metadata.annotations["test-results"] == "passed"
}
