package requiretestspassed

import data.requiretestspassed.deny
import data.requiretestspassed.allow

# Test case: Deployment with passing tests should be allowed
test_deployment_with_passing_tests {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "app",
      "namespace": "default",
      "annotations": {
        "test-results": "passed"
      }
    }
  }
  
  # Should allow (no denials)
  count(deny) == 0 with input as deployment
}

# Test case: Deployment with failing tests should be denied
test_deployment_with_failing_tests {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "app",
      "namespace": "default",
      "annotations": {
        "test-results": "failed"
      }
    }
  }
  
  # Should deny
  count(deny) > 0 with input as deployment
}

# Test case: Deployment missing test-results annotation should be denied
test_deployment_missing_annotation {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "app",
      "namespace": "default",
      "annotations": {}
    }
  }
  
  # Should deny
  count(deny) > 0 with input as deployment
}
