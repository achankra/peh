#!/usr/bin/env python3
"""
Local scaffolder — simulates Backstage's fetch:template action.

Copies the skeleton directory, substitutes ${{ values.xxx }} variables,
processes Nunjucks conditionals ({%- if %}...{%- endif %}), and removes
database/infrastructure files that don't match the selected database.

This lets you test the template locally without a running Backstage instance.

Usage:
    python3 scaffold.py                          # interactive prompts
    python3 scaffold.py --name order-service     # with defaults
    python3 scaffold.py --name order-service --team team-alpha --database postgresql
"""

import argparse
import re
import shutil
import sys
from pathlib import Path


TEMPLATES_DIR = Path(__file__).parent / "templates"


def substitute_variables(project_path: Path, values: dict):
    """Replace ${{ values.xxx }} placeholders in all text files."""
    count = 0
    for file_path in project_path.rglob("*"):
        if file_path.is_file():
            try:
                content = file_path.read_text()
                original = content
                for key, value in values.items():
                    content = content.replace(f"${{{{ values.{key} }}}}", str(value))
                if content != original:
                    file_path.write_text(content)
                    count += 1
            except UnicodeDecodeError:
                pass  # Skip binary files
    return count


def process_conditionals(project_path: Path, values: dict):
    """Process Nunjucks-style {%- if %} / {%- endif %} blocks."""
    for file_path in project_path.rglob("*"):
        if file_path.is_file():
            try:
                content = file_path.read_text()
                if "{%-" not in content:
                    continue

                # Process each conditional block
                # Pattern: {%- if values.xxx == 'yyy' %} ... {%- endif %}
                def eval_condition(match):
                    condition = match.group(1).strip()
                    body = match.group(2)

                    # Parse: values.key == 'value' or values.key !== 'value'
                    m = re.match(
                        r"values\.(\w+)\s*(===?|!==?)\s*['\"]([^'\"]*)['\"]",
                        condition
                    )
                    if not m:
                        return body  # Can't parse — keep content

                    key, op, expected = m.group(1), m.group(2), m.group(3)
                    actual = values.get(key, "")

                    if op in ("==", "==="):
                        return body if actual == expected else ""
                    elif op in ("!=", "!=="):
                        return body if actual != expected else ""
                    return body

                content = re.sub(
                    r"\{%-?\s*if\s+(.+?)\s*%\}(.*?)\{%-?\s*endif\s*%\}",
                    eval_condition,
                    content,
                    flags=re.DOTALL,
                )
                file_path.write_text(content)
            except UnicodeDecodeError:
                pass


def remove_unused_database_files(project_path: Path, database: str):
    """Remove database and infrastructure files that don't match the selection."""
    db_dir = project_path / "database"
    infra_dir = project_path / "infrastructure"

    if database == "none":
        # Remove all database and infrastructure files
        if db_dir.exists():
            shutil.rmtree(db_dir)
        if infra_dir.exists():
            shutil.rmtree(infra_dir)
    else:
        # Keep only the selected database
        if db_dir.exists():
            for child in db_dir.iterdir():
                if child.is_dir() and child.name != database:
                    shutil.rmtree(child)
        if infra_dir.exists():
            for child in infra_dir.iterdir():
                if child.is_file() and database not in child.name:
                    child.unlink()


def scaffold(template_name: str, version: str, values: dict, output_dir: Path):
    """Scaffold a new project from a template."""
    template_path = TEMPLATES_DIR / template_name / version
    skeleton_path = template_path / "skeleton"

    if not skeleton_path.exists():
        print(f"Error: skeleton not found at {skeleton_path}")
        return False

    if output_dir.exists():
        print(f"Error: {output_dir} already exists. Remove it first or choose a different name.")
        return False

    # Step 1: Copy skeleton
    print(f"Scaffolding {values['serviceName']} from {template_name}/{version}...")
    shutil.copytree(skeleton_path, output_dir)

    # Step 2: Substitute variables
    files_modified = substitute_variables(output_dir, values)
    print(f"  Substituted variables in {files_modified} files")

    # Step 3: Process conditionals
    process_conditionals(output_dir, values)
    print("  Processed conditional blocks")

    # Step 4: Remove unused database/infra files
    remove_unused_database_files(output_dir, values.get("database", "none"))
    print(f"  Database: {values.get('database', 'none')}")

    print(f"\nProject scaffolded at ./{output_dir.name}/")
    print(f"\nNext steps:")
    print(f"  cd {output_dir.name}")
    print(f"  python3 dev.py validate")
    print(f"  npm install && npm test")
    return True


def main():
    parser = argparse.ArgumentParser(description="Scaffold a project from a template")
    parser.add_argument("--name", help="Service name (lowercase, hyphens)")
    parser.add_argument("--team", default="team-alpha", help="Team name (default: team-alpha)")
    parser.add_argument("--description", default="", help="Service description")
    parser.add_argument("--database", choices=["none", "postgresql", "mongodb"],
                        default="postgresql", help="Database (default: postgresql)")
    parser.add_argument("--port", type=int, default=8080, help="Service port (default: 8080)")
    parser.add_argument("--template", default="backend-service", help="Template name")
    parser.add_argument("--version", default="v1", help="Template version")

    args = parser.parse_args()

    # Interactive prompts if --name not provided
    if not args.name:
        args.name = input("Service name [order-service]: ").strip() or "order-service"
        team_input = input(f"Team [{args.team}]: ").strip()
        if team_input:
            args.team = team_input
        desc_input = input("Description [A backend service]: ").strip()
        args.description = desc_input or "A backend service"
        db_input = input(f"Database (none/postgresql/mongodb) [{args.database}]: ").strip()
        if db_input in ("none", "postgresql", "mongodb"):
            args.database = db_input
        port_input = input(f"Port [{args.port}]: ").strip()
        if port_input.isdigit():
            args.port = int(port_input)

    if not args.description:
        args.description = f"{args.name} service"

    values = {
        "serviceName": args.name,
        "team": args.team,
        "description": args.description,
        "database": args.database,
        "port": str(args.port),
        "templateVersion": "1.0.0",
        "year": "2025",
    }

    output_dir = Path(args.name)
    success = scaffold(args.template, args.version, values, output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
