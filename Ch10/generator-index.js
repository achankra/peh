// generators/backend-service/index.js
// Yeoman generator for creating Node.js backend services
// Supports both interactive prompts and CLI options for automation

const Generator = require("yeoman-generator");
const path = require("path");

module.exports = class extends Generator {
  constructor(args, opts) {
    super(args, opts);

    // Command-line options for non-interactive usage
    this.option("name", {
      type: String,
      description: "Service name",
    });
    this.option("team", {
      type: String,
      description: "Team identifier",
    });
    this.option("database", {
      type: String,
      description: "Database type (none, postgresql, mongodb)",
      default: "none",
    });
  }

  async prompting() {
    // Skip prompts if options provided (CI/CD usage)
    if (this.options.name && this.options.team) {
      this.answers = {
        serviceName: this.options.name,
        team: this.options.team,
        database: this.options.database,
        description: this.options.description || "",
        port: this.options.port || 8080,
      };
      return;
    }

    this.answers = await this.prompt([
      {
        type: "input",
        name: "serviceName",
        message: "Service name:",
        validate: (input) =>
          /^[a-z][a-z0-9-]*$/.test(input) ||
          "Name must be lowercase alphanumeric with hyphens",
      },
      {
        type: "input",
        name: "team",
        message: "Team identifier:",
        validate: (input) =>
          /^[a-z][a-z0-9-]*$/.test(input) ||
          "Team must be lowercase alphanumeric with hyphens",
      },
      {
        type: "input",
        name: "description",
        message: "Service description:",
      },
      {
        type: "list",
        name: "database",
        message: "Database requirement:",
        choices: [
          { name: "None", value: "none" },
          { name: "PostgreSQL", value: "postgresql" },
          { name: "MongoDB", value: "mongodb" },
        ],
      },
      {
        type: "number",
        name: "port",
        message: "Service port:",
        default: 8080,
      },
    ]);
  }

  writing() {
    const templateData = {
      ...this.answers,
      year: new Date().getFullYear(),
      generatorVersion: require("./package.json").version,
    };

    // Copy all template files
    this.fs.copyTpl(
      this.templatePath("**/*"),
      this.destinationPath(this.answers.serviceName),
      templateData,
      {},
      { globOptions: { dot: true } }
    );

    // Conditionally add database configuration
    if (this.answers.database !== "none") {
      this.fs.copyTpl(
        this.templatePath(`database/${this.answers.database}/**/*`),
        this.destinationPath(`${this.answers.serviceName}/src/database`),
        templateData
      );

      // Add infrastructure claim
      this.fs.copyTpl(
        this.templatePath(`infrastructure/${this.answers.database}-claim.yaml`),
        this.destinationPath(
          `${this.answers.serviceName}/infrastructure/database.yaml`
        ),
        templateData
      );
    }
  }

  async install() {
    const destPath = this.destinationPath(this.answers.serviceName);

    this.log("Installing dependencies...");
    this.spawnSync("npm", ["install"], { cwd: destPath });

    this.log("Initializing git repository...");
    this.spawnSync("git", ["init"], { cwd: destPath });
    this.spawnSync("git", ["add", "."], { cwd: destPath });
    this.spawnSync(
      "git",
      ["commit", "-m", "Initial commit from starter kit"],
      { cwd: destPath }
    );
  }

  end() {
    this.log("");
    this.log("🚀 Service created successfully!");
    this.log("");
    this.log("Next steps:");
    this.log(`  cd ${this.answers.serviceName}`);
    this.log("  npm run dev          # Start local development");
    this.log("  npm test             # Run tests");
    this.log("  npm run build        # Build for production");
    this.log("");
    this.log("To deploy to the platform:");
    this.log("  git remote add origin <your-repo-url>");
    this.log("  git push -u origin main");
    this.log("");
  }
};
