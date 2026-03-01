# Chapter 11: OPA Unit Tests for Require Tests Passed Policy
# ===========================================================
# Tests the require-tests-passed.rego policy using OPA's test framework
# Validates that deployments have test-results annotation set to "passed"
#
# Run tests with: opa test policies/ -v
#                 or: conftest test -p policies/ --namespace main

package requiretestspassed

import rego.v1

import data.requiretestspassed.deny
import data.requiretestspassed.allow

# =============================================================================
# TEST SUITE 1: Valid Cases (Should PASS - no violations)
# =============================================================================

# Test case: Deployment with passing tests should be allowed
test_deployment_with_passing_tests if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "web-api",
      "namespace": "production",
      "annotations": {
        "test-results": "passed"
      }
    }
  }

  # Should allow (no denials)
  count(deny) == 0 with input as deployment
}

# Test case: Deployment with passed result (capitalized)
test_deployment_with_capitalized_passed if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "backend-service",
      "namespace": "staging",
      "annotations": {
        "test-results": "passed"
      }
    }
  }

  # Should allow
  count(deny) == 0 with input as deployment
}

# Test case: Allow works as expected for valid deployment
test_allow_rule_for_valid_deployment if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "compliant-app",
      "namespace": "default",
      "annotations": {
        "test-results": "passed"
      }
    }
  }

  # Allow rule should be true
  allow with input as deployment
}

# =============================================================================
# TEST SUITE 2: Invalid Cases (Should FAIL - violations expected)
# =============================================================================

# Test case: Deployment with failing tests should be denied
test_deployment_with_failing_tests if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "broken-app",
      "namespace": "default",
      "annotations": {
        "test-results": "failed"
      }
    }
  }

  # Should deny
  count(deny) > 0 with input as deployment
}

# Test case: Deployment with pending tests should be denied
test_deployment_with_pending_tests if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "untested-app",
      "namespace": "default",
      "annotations": {
        "test-results": "pending"
      }
    }
  }

  # Should deny
  count(deny) > 0 with input as deployment
}

# Test case: Deployment missing test-results annotation should be denied
test_deployment_missing_annotation if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "no-tests-app",
      "namespace": "default",
      "annotations": {}
    }
  }

  # Should deny
  count(deny) > 0 with input as deployment
}

# Test case: Deployment with no annotations object should be denied
test_deployment_with_no_annotations_object if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "minimal-app",
      "namespace": "default"
    }
  }

  # Should deny
  count(deny) > 0 with input as deployment
}

# Test case: Deployment with empty string test-results should be denied
test_deployment_with_empty_test_results if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "empty-results-app",
      "namespace": "default",
      "annotations": {
        "test-results": ""
      }
    }
  }

  # Should deny
  count(deny) > 0 with input as deployment
}

# =============================================================================
# TEST SUITE 3: Edge Cases and Special Scenarios
# =============================================================================

# Test case: Only Deployments are checked (other kinds are ignored)
test_pod_with_missing_annotation_should_pass if {
  pod := {
    "kind": "Pod",
    "metadata": {
      "name": "test-pod",
      "namespace": "default",
      "annotations": {}
    }
  }

  # Policy only applies to Deployments, so Pod should pass
  count(deny) == 0 with input as pod
}

# Test case: StatefulSet without annotation should pass (policy specific to Deployment)
test_statefulset_should_pass if {
  statefulset := {
    "kind": "StatefulSet",
    "metadata": {
      "name": "database",
      "namespace": "default",
      "annotations": {}
    }
  }

  # Policy only applies to Deployments
  count(deny) == 0 with input as statefulset
}

# Test case: Deployment with test-results and other annotations
test_deployment_with_multiple_annotations if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "complex-app",
      "namespace": "production",
      "annotations": {
        "test-results": "passed",
        "version": "1.2.3",
        "owner": "platform-team",
        "description": "Multi-tier application"
      }
    }
  }

  # Should allow even with other annotations
  count(deny) == 0 with input as deployment
}

# Test case: Case-sensitive check (PASSED != passed)
test_deployment_with_uppercase_passed if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "case-test-app",
      "namespace": "default",
      "annotations": {
        "test-results": "PASSED"
      }
    }
  }

  # Should deny because "PASSED" != "passed" (case-sensitive)
  count(deny) > 0 with input as deployment
}

# Test case: Deployment with "pass" (singular) should be denied
test_deployment_with_pass_not_passed if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "singular-app",
      "namespace": "default",
      "annotations": {
        "test-results": "pass"
      }
    }
  }

  # Should deny because "pass" != "passed"
  count(deny) > 0 with input as deployment
}

# Test case: Deployment across multiple namespaces
test_deployment_in_different_namespaces if {
  deployment_prod := {
    "kind": "Deployment",
    "metadata": {
      "name": "app",
      "namespace": "production",
      "annotations": {
        "test-results": "passed"
      }
    }
  }

  deployment_dev := {
    "kind": "Deployment",
    "metadata": {
      "name": "app",
      "namespace": "development",
      "annotations": {
        "test-results": "passed"
      }
    }
  }

  # Both should pass
  count(deny) == 0 with input as deployment_prod
  count(deny) == 0 with input as deployment_dev
}

# =============================================================================
# TEST SUITE 4: Error Message Validation
# =============================================================================

# Test case: Verify error message for missing annotation
test_error_message_missing_annotation if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "test-app",
      "namespace": "default",
      "annotations": {}
    }
  }

  violations := deny with input as deployment
  # Should have at least one violation
  count(violations) > 0
}

# Test case: Verify error message for wrong test result value
test_error_message_wrong_test_result if {
  deployment := {
    "kind": "Deployment",
    "metadata": {
      "name": "test-app",
      "namespace": "default",
      "annotations": {
        "test-results": "failed"
      }
    }
  }

  violations := deny with input as deployment
  # Should have at least one violation
  count(violations) > 0
}
