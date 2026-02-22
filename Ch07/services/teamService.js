const k8s = require("@kubernetes/client-node");
const { Octokit } = require("@octokit/rest");

const kc = new k8s.KubeConfig();
kc.loadFromDefault();

const k8sApi = kc.makeApiClient(k8s.CoreV1Api);
const k8sAppsApi = kc.makeApiClient(k8s.AppsV1Api);
const k8sRbacApi = kc.makeApiClient(k8s.RbacAuthorizationV1Api);

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

/**
 * Create a new team in the platform
 * Creates:
 * 1. Kubernetes namespace with team labels
 * 2. RBAC RoleBinding for team members
 * 3. ResourceQuota for the namespace
 * 4. GitHub repository for the team
 *
 * @param {Object} teamConfig - Team configuration
 * @param {string} teamConfig.name - Team name (alphanumeric, lowercase)
 * @param {string} teamConfig.displayName - Display name for the team
 * @param {string} teamConfig.costCenter - Cost center for billing
 * @param {string} teamConfig.tier - Resource tier (starter, standard, enterprise)
 * @param {Array<string>} teamConfig.members - GitHub usernames
 * @param {Object} teamConfig.github - GitHub configuration
 * @returns {Promise<Object>} Team creation result
 */
async function createTeam(teamConfig) {
  const {
    name,
    displayName,
    costCenter,
    tier,
    members,
    github = {},
  } = teamConfig;

  try {
    // Validate inputs
    if (!name || !/^[a-z0-9][a-z0-9-]*[a-z0-9]$/.test(name)) {
      throw new Error(
        "Invalid team name. Must be alphanumeric lowercase with hyphens."
      );
    }

    if (!["starter", "standard", "enterprise"].includes(tier)) {
      throw new Error("Invalid tier. Must be starter, standard, or enterprise.");
    }

    // Check if namespace already exists (idempotency)
    let namespaceExists = false;
    try {
      await k8sApi.readNamespace(name);
      namespaceExists = true;
      console.log(`Namespace ${name} already exists.`);
    } catch (error) {
      if (error.statusCode !== 404) {
        throw error;
      }
    }

    // Create namespace if it doesn't exist
    if (!namespaceExists) {
      const namespace = {
        apiVersion: "v1",
        kind: "Namespace",
        metadata: {
          name: name,
          labels: {
            team: name,
            "cost-center": costCenter,
            tier: tier,
            "managed-by": "platform-onboarding",
          },
        },
      };

      await k8sApi.createNamespace(namespace);
      console.log(`Created namespace: ${name}`);
    }

    // Create RBAC RoleBinding for team members
    const roleBinding = {
      apiVersion: "rbac.authorization.k8s.io/v1",
      kind: "RoleBinding",
      metadata: {
        name: `${name}-team-role-binding`,
        namespace: name,
      },
      roleRef: {
        apiGroup: "rbac.authorization.k8s.io",
        kind: "Role",
        name: `${name}-team-role`,
      },
      subjects: members.map((member) => ({
        kind: "User",
        name: `${member}@company.com`,
        apiGroup: "rbac.authorization.k8s.io",
      })),
    };

    try {
      await k8sRbacApi.readNamespacedRoleBinding(
        `${name}-team-role-binding`,
        name
      );
      console.log(`RoleBinding for ${name} already exists.`);
    } catch (error) {
      if (error.statusCode === 404) {
        await k8sRbacApi.createNamespacedRoleBinding(name, roleBinding);
        console.log(`Created RoleBinding for team: ${name}`);
      } else {
        throw error;
      }
    }

    // Create Resource Quota
    const quotaLimits = {
      starter: {
        "requests.cpu": "2",
        "requests.memory": "4Gi",
        pods: "10",
      },
      standard: {
        "requests.cpu": "8",
        "requests.memory": "16Gi",
        pods: "50",
      },
      enterprise: {
        "requests.cpu": "32",
        "requests.memory": "64Gi",
        pods: "200",
      },
    };

    const resourceQuota = {
      apiVersion: "v1",
      kind: "ResourceQuota",
      metadata: {
        name: `${name}-quota`,
        namespace: name,
      },
      spec: {
        hard: quotaLimits[tier],
      },
    };

    try {
      await k8sApi.readNamespacedResourceQuota(`${name}-quota`, name);
      console.log(`ResourceQuota for ${name} already exists.`);
    } catch (error) {
      if (error.statusCode === 404) {
        await k8sApi.createNamespacedResourceQuota(name, resourceQuota);
        console.log(`Created ResourceQuota for team: ${name}`);
      } else {
        throw error;
      }
    }

    // Create GitHub repository
    if (github.owner && github.repoName) {
      try {
        await octokit.repos.get({
          owner: github.owner,
          repo: github.repoName,
        });
        console.log(
          `GitHub repository ${github.owner}/${github.repoName} already exists.`
        );
      } catch (error) {
        if (error.status === 404) {
          await octokit.repos.createInOrg({
            org: github.owner,
            name: github.repoName,
            description: `Repository for team: ${displayName}`,
            private: true,
            has_issues: true,
            has_projects: true,
            has_wiki: true,
          });
          console.log(
            `Created GitHub repository: ${github.owner}/${github.repoName}`
          );
        } else {
          throw error;
        }
      }
    }

    return {
      success: true,
      team: {
        name: name,
        displayName: displayName,
        tier: tier,
        costCenter: costCenter,
        members: members,
        namespace: name,
        quota: quotaLimits[tier],
        github: github.owner ? `${github.owner}/${github.repoName}` : null,
      },
    };
  } catch (error) {
    console.error(`Error creating team ${name}:`, error.message);
    return {
      success: false,
      error: error.message,
    };
  }
}

module.exports = {
  createTeam,
};
