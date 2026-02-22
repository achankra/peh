#!/usr/bin/env python3
"""
Pipeline Composer - Generates GitHub Actions workflows from reusable components.

This tool reads a simple YAML configuration describing an application's CI/CD
needs and generates a complete GitHub Actions workflow that uses the reusable
workflow components (build-and-test.yaml, security-scan.yaml, deploy.yaml).

The configuration can specify:
- Build settings (language, version, custom commands)
- Security scanning options
- Deployment stages with strategies (canary, blue-green)
- Environment-specific variations

Usage:
    python pipeline-composer.py --config pipeline-config.yaml --output .github/workflows/main.yaml
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List
import json


class PipelineComposer:
    """Composes GitHub Actions workflows from reusable components."""

    def __init__(self):
        """Initialize the pipeline composer."""
        self.config: Dict[str, Any] = {}
        self.workflow: Dict[str, Any] = {}

    def load_config(self, config_path: str) -> None:
        """
        Load pipeline configuration from YAML file.
        
        Args:
            config_path: Path to pipeline configuration file
        """
        # Simple YAML-like parsing (would use PyYAML in production)
        config = {"name": "pipeline", "stages": []}
        
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                # Basic parsing for demonstration
                lines = content.strip().split('\n')
                current_section = None
                current_stage = None
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == 'name':
                            config['name'] = value
                        elif key == 'language':
                            config['language'] = value
                        elif key == 'image-registry':
                            config['image-registry'] = value
                        elif key == 'stages':
                            # Simplified handling
                            pass
                
                # Default stage setup if not specified
                if not config.get('stages'):
                    config['stages'] = [
                        {
                            'name': 'build',
                            'tasks': ['build-and-test', 'security-scan']
                        },
                        {
                            'name': 'deploy-staging',
                            'deploy-strategy': 'blue-green',
                            'environment': 'staging'
                        }
                    ]
            
            self.config = config
        except FileNotFoundError:
            print(f"Error: Configuration file not found: {config_path}")
            sys.exit(1)

    def create_workflow_structure(self) -> None:
        """Create the base GitHub Actions workflow structure."""
        self.workflow = {
            'name': f"{self.config.get('name', 'Pipeline')} CI/CD",
            'on': {
                'push': {
                    'branches': ['main', 'develop'],
                    'paths': ['src/**', 'tests/**', 'Dockerfile', 'requirements.txt']
                },
                'pull_request': {
                    'branches': ['main', 'develop']
                }
            },
            'env': {
                'REGISTRY': self.config.get('image-registry', 'ghcr.io'),
                'IMAGE_NAME': self.config.get('name', 'app')
            },
            'jobs': {}
        }

    def add_build_job(self) -> None:
        """Add build and test job to workflow."""
        language = self.config.get('language', 'python')
        language_version = self.config.get('language-version', 'latest')
        
        self.workflow['jobs']['build'] = {
            'name': 'Build and Test',
            'uses': './.github/workflows/reusable/build-and-test.yaml',
            'with': {
                'language': language,
                'language-version': language_version,
                'artifact-name': f'{self.config.get("name", "app")}-build'
            }
        }

    def add_security_job(self) -> None:
        """Add security scanning job to workflow."""
        self.workflow['jobs']['security'] = {
            'name': 'Security Scan',
            'needs': ['build'],
            'uses': './.github/workflows/reusable/security-scan.yaml',
            'with': {
                'scan-container': True,
                'scan-dependencies': True,
                'fail-on-critical': True
            }
        }

    def add_deployment_jobs(self) -> None:
        """Add deployment jobs based on stages in configuration."""
        stages = self.config.get('stages', [])
        previous_job = 'security'
        
        for i, stage in enumerate(stages):
            stage_name = stage.get('name', f'stage-{i}')
            
            # Skip if not a deployment stage
            if 'deploy-strategy' not in stage and 'tasks' in stage:
                continue
            
            environment = stage.get('environment', 'staging')
            strategy = stage.get('deploy-strategy', 'direct')
            
            job_name = f'deploy-{environment}'
            
            self.workflow['jobs'][job_name] = {
                'name': f'Deploy to {environment.title()}',
                'needs': [previous_job],
                'uses': './.github/workflows/reusable/deploy.yaml',
                'with': {
                    'environment': environment,
                    'deployment-strategy': strategy,
                    'image': f'${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ github.sha }}}}',
                    'namespace': f'{environment}'
                },
                'if': "github.event_name == 'push' && github.ref == 'refs/heads/main'"
            }
            
            previous_job = job_name

    def add_notifications(self) -> None:
        """Add notification job for pipeline completion."""
        self.workflow['jobs']['notify'] = {
            'name': 'Notify Pipeline Status',
            'needs': ['build', 'security'],
            'if': 'always()',
            'runs-on': 'ubuntu-latest',
            'steps': [
                {
                    'name': 'Pipeline Status',
                    'run': 'echo "Pipeline completed with status: ${{ job.status }}"'
                }
            ]
        }

    def compose(self) -> str:
        """
        Compose the complete workflow.
        
        Returns:
            YAML string representation of the workflow
        """
        self.create_workflow_structure()
        self.add_build_job()
        self.add_security_job()
        self.add_deployment_jobs()
        self.add_notifications()
        
        return self._workflow_to_yaml()

    def _workflow_to_yaml(self) -> str:
        """
        Convert workflow dictionary to YAML format.
        
        Returns:
            YAML string
        """
        lines = [
            "# This workflow was generated by pipeline-composer",
            "# Auto-generated - do not edit manually",
            "# Regenerate with: python pipeline-composer.py --config pipeline-config.yaml",
            "",
            f"name: {self.workflow['name']}",
            "",
            "on:"
        ]
        
        # Add trigger events
        on_section = self.workflow['on']
        for event, config in on_section.items():
            if isinstance(config, dict):
                lines.append(f"  {event}:")
                for key, value in config.items():
                    if isinstance(value, list):
                        lines.append(f"    {key}:")
                        for item in value:
                            lines.append(f"      - {item}")
                    else:
                        lines.append(f"    {key}: {value}")
            else:
                lines.append(f"  {event}: {config}")
        
        # Add environment variables
        lines.append("")
        lines.append("env:")
        for key, value in self.workflow['env'].items():
            lines.append(f"  {key}: {value}")
        
        # Add jobs
        lines.append("")
        lines.append("jobs:")
        
        for job_name, job_config in self.workflow['jobs'].items():
            lines.append(f"  {job_name}:")
            
            if 'uses' in job_config:
                lines.append(f"    uses: {job_config['uses']}")
                if 'name' in job_config:
                    lines.append(f"    name: {job_config['name']}")
                if 'needs' in job_config:
                    needs = job_config['needs']
                    if isinstance(needs, list):
                        lines.append(f"    needs: {json.dumps(needs)}")
                    else:
                        lines.append(f"    needs: {needs}")
                
                if 'with' in job_config:
                    lines.append("    with:")
                    for key, value in job_config['with'].items():
                        if isinstance(value, bool):
                            value = str(value).lower()
                        lines.append(f"      {key}: {value}")
                
                if 'if' in job_config:
                    lines.append(f"    if: {job_config['if']}")
            
            elif 'runs-on' in job_config:
                lines.append(f"    runs-on: {job_config['runs-on']}")
                
                if 'name' in job_config:
                    lines.append(f"    name: {job_config['name']}")
                
                if 'needs' in job_config:
                    needs = job_config['needs']
                    if isinstance(needs, list):
                        lines.append(f"    needs: {json.dumps(needs)}")
                    else:
                        lines.append(f"    needs: {needs}")
                
                if 'if' in job_config:
                    lines.append(f"    if: {job_config['if']}")
                
                if 'steps' in job_config:
                    lines.append("    steps:")
                    for step in job_config['steps']:
                        lines.append(f"      - name: {step['name']}")
                        if 'run' in step:
                            lines.append(f"        run: {step['run']}")
        
        return "\n".join(lines)

    def save_workflow(self, output_path: str) -> None:
        """
        Save the composed workflow to a file.
        
        Args:
            output_path: Path where workflow should be saved
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        workflow_yaml = self.compose()
        with open(output_path, 'w') as f:
            f.write(workflow_yaml)
        
        print(f"✓ Workflow generated: {output_path}")
        print(f"  Total jobs: {len(self.workflow['jobs'])}")
        print(f"  Configuration: {self.config.get('name', 'app')}")


def main():
    """Main entry point for the pipeline composer."""
    parser = argparse.ArgumentParser(
        description='Compose GitHub Actions workflows from reusable components'
    )
    parser.add_argument(
        '--config',
        required=True,
        help='Path to pipeline configuration file'
    )
    parser.add_argument(
        '--output',
        default='.github/workflows/generated.yaml',
        help='Output path for generated workflow'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print workflow without saving'
    )
    
    args = parser.parse_args()
    
    # Create and run composer
    composer = PipelineComposer()
    composer.load_config(args.config)
    
    if args.dry_run:
        print(composer.compose())
    else:
        composer.save_workflow(args.output)


if __name__ == '__main__':
    main()
