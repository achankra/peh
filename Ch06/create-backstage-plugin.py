#!/usr/bin/env python3
"""
Backstage Plugin Scaffolding Tool

Generates a complete Backstage plugin structure with TypeScript files,
configuration, and build setup. Supports both frontend and backend plugins.

Usage:
    python3 create-backstage-plugin.py --name my-plugin
    python3 create-backstage-plugin.py --name company-api --type backend --output-dir ./plugins
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional


class BackstagePluginScaffold:
    """
    Scaffolds Backstage plugin directory structure and files.
    
    Attributes:
        name: Plugin name (kebab-case)
        description: Plugin description
        plugin_type: Type of plugin ('frontend', 'backend', or 'full')
        output_dir: Root directory for plugin output
    """
    
    def __init__(
        self,
        name: str,
        description: str = "",
        plugin_type: str = "frontend",
        output_dir: str = "."
    ):
        """
        Initialize plugin scaffolder.
        
        Args:
            name: Plugin name in kebab-case
            description: Plugin description
            plugin_type: Type of plugin ('frontend', 'backend', 'full')
            output_dir: Root directory for output
        """
        self.name = name
        self.description = description or f"{name} Backstage plugin"
        self.plugin_type = plugin_type
        self.output_dir = Path(output_dir)
        self.plugin_dir = self.output_dir / name
        
        # Convert kebab-case to camelCase
        self.camel_name = self._to_camel_case(name)
        self.pascal_name = self._to_pascal_case(name)
    
    @staticmethod
    def _to_camel_case(name: str) -> str:
        """Convert kebab-case to camelCase."""
        parts = name.split('-')
        return parts[0] + ''.join(p.capitalize() for p in parts[1:])
    
    @staticmethod
    def _to_pascal_case(name: str) -> str:
        """Convert kebab-case to PascalCase."""
        return ''.join(p.capitalize() for p in name.split('-'))
    
    def create_directory_structure(self) -> None:
        """Create the directory structure for the plugin."""
        if self.plugin_dir.exists():
            print(f"Warning: Directory {self.plugin_dir} already exists")
            return
        
        # Create base directories
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        if self.plugin_type in ['frontend', 'full']:
            (self.plugin_dir / 'src' / 'components').mkdir(parents=True, exist_ok=True)
            (self.plugin_dir / 'src' / 'hooks').mkdir(parents=True, exist_ok=True)
            (self.plugin_dir / 'src' / 'plugin.ts').parent.mkdir(parents=True, exist_ok=True)
        
        if self.plugin_type in ['backend', 'full']:
            (self.plugin_dir / 'src' / 'plugin.ts').parent.mkdir(parents=True, exist_ok=True)
            (self.plugin_dir / 'src' / 'service').mkdir(parents=True, exist_ok=True)
            (self.plugin_dir / 'src' / 'routes').mkdir(parents=True, exist_ok=True)
        
        (self.plugin_dir / 'dist').mkdir(exist_ok=True)
        
        print(f"Created directory structure in {self.plugin_dir}")
    
    def create_package_json(self) -> None:
        """Create package.json file."""
        package_data = {
            "name": f"@backstage/plugin-{self.name}",
            "version": "0.1.0",
            "description": self.description,
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "tsc",
                "test": "jest",
                "start": "backstage-cli repo server",
                "dev": "yarn build && yarn workspace @backstage/app serve"
            },
            "dependencies": {
                "@backstage/core-plugin-api": "^1.0.0",
                "@backstage/plugin-catalog-react": "^1.0.0",
                "react": "^17.0.0",
                "react-dom": "^17.0.0"
            },
            "peerDependencies": {
                "@backstage/core-app-api": "*",
                "@backstage/core-plugin-api": "*"
            },
            "devDependencies": {
                "@backstage/cli": "^0.22.0",
                "@types/node": "^16.0.0",
                "@types/react": "^17.0.0",
                "typescript": "^4.0.0"
            },
            "publishConfig": {
                "access": "public",
                "main": "dist/index.js",
                "types": "dist/index.d.ts"
            }
        }
        
        package_file = self.plugin_dir / 'package.json'
        with open(package_file, 'w') as f:
            json.dump(package_data, f, indent=2)
        
        print(f"Created {package_file.name}")
    
    def create_tsconfig(self) -> None:
        """Create TypeScript configuration."""
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs",
                "lib": ["ES2020", "DOM"],
                "outDir": "./dist",
                "rootDir": "./src",
                "declaration": True,
                "declarationMap": True,
                "sourceMap": True,
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True,
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist", "**/*.test.ts"]
        }
        
        tsconfig_file = self.plugin_dir / 'tsconfig.json'
        with open(tsconfig_file, 'w') as f:
            json.dump(tsconfig, f, indent=2)
        
        print(f"Created {tsconfig_file.name}")
    
    def create_plugin_manifest(self) -> None:
        """Create Backstage plugin manifest file."""
        manifest = {
            "name": f"@backstage/plugin-{self.name}",
            "version": "0.1.0",
            "description": self.description,
            "author": "Your Organization",
            "repository": f"https://github.com/your-org/backstage-plugins/tree/main/{self.name}",
            "bugs": f"https://github.com/your-org/backstage-plugins/issues",
            "keywords": ["backstage", "plugin"],
            "backstage": {
                "role": "plugin",
                "support": {
                    "platform": "general"
                }
            }
        }
        
        manifest_file = self.plugin_dir / 'manifest.json'
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Created {manifest_file.name}")
    
    def create_frontend_plugin(self) -> None:
        """Create frontend plugin TypeScript files."""
        # Main plugin file
        plugin_ts = f'''// {self.name} Backstage Plugin
// Main plugin configuration and export

import {{
  createPlugin,
  createPageExtension,
  createComponentExtension,
}} from '@backstage/core-plugin-api';

export const {self.camel_name}Plugin = createPlugin({{
  id: '{self.name}',
  routes: {{
    root: createPageExtension({{
      defaultPath: '/{self.name}',
      defaultTitle: '{self.pascal_name}',
      component: () => import('./components/Root').then(m => m.Root),
    }}),
  }},
}});

export const {self.pascal_name}Page = {self.camel_name}Plugin.provide(
  createPageExtension({{
    defaultPath: '/{self.name}',
    component: () => import('./components/Root').then(m => m.Root),
  }})
);
'''
        
        plugin_file = self.plugin_dir / 'src' / 'plugin.ts'
        with open(plugin_file, 'w') as f:
            f.write(plugin_ts)
        
        # Root component
        root_component = f'''// Root component for {self.name} plugin

import React from 'react';
import {{
  Header,
  Page,
  Content,
  ContentHeader,
}} from '@backstage/core-components';

export const Root = () => (
  <Page themeId="tool">
    <Header title="{self.pascal_name}" />
    <Content>
      <ContentHeader title="Welcome">
        <p>Welcome to the {self.pascal_name} plugin!</p>
      </ContentHeader>
      <p>
        This is a basic {self.name} Backstage plugin. 
        Customize this component to add your plugin functionality.
      </p>
    </Content>
  </Page>
);
'''
        
        components_dir = self.plugin_dir / 'src' / 'components'
        components_dir.mkdir(parents=True, exist_ok=True)
        root_file = components_dir / 'Root.tsx'
        with open(root_file, 'w') as f:
            f.write(root_component)
        
        # Index file
        index_ts = f'''// {self.name} Plugin Exports

export {{ {self.pascal_name}Page, {self.camel_name}Plugin }} from './plugin';
'''
        
        index_file = self.plugin_dir / 'src' / 'index.ts'
        with open(index_file, 'w') as f:
            f.write(index_ts)
        
        print(f"Created frontend plugin files")
    
    def create_backend_plugin(self) -> None:
        """Create backend plugin TypeScript files."""
        # Main plugin file
        plugin_ts = f'''// {self.name} Backend Plugin
// Main plugin configuration and service setup

import {{
  coreServices,
  createBackendPlugin,
}} from '@backstage/backend-plugin-api';
import {{ createRouter }} from './router';

export const {self.camel_name}Plugin = createBackendPlugin({{
  pluginId: '{self.name}',
  register(env) {{
    env.http.use(
      createRouter({{
        logger: env.logger,
        config: env.config,
      }})
    );
  }},
}});
'''
        
        plugin_file = self.plugin_dir / 'src' / 'plugin.ts'
        with open(plugin_file, 'w') as f:
            f.write(plugin_ts)
        
        # Router file
        router_ts = f'''// {self.name} Backend Routes

import {{ Router }} from 'express';
import {{ Logger }} from 'winston';
import {{ Config }} from '@backstage/config';

export interface RouterOptions {{
  logger: Logger;
  config: Config;
}}

export function createRouter(options: RouterOptions): Router {{
  const {{ logger, config }} = options;
  const router = Router();

  router.get('/health', (req, res) => {{
    res.json({{ status: 'ok' }});
  }});

  router.get('/info', (req, res) => {{
    res.json({{
      name: '{self.name}',
      version: '0.1.0',
    }});
  }});

  return router;
}}
'''
        
        routes_dir = self.plugin_dir / 'src' / 'routes'
        routes_dir.mkdir(parents=True, exist_ok=True)
        router_file = routes_dir.parent / 'router.ts'
        with open(router_file, 'w') as f:
            f.write(router_ts)
        
        # Index file
        index_ts = f'''// {self.name} Backend Plugin Exports

export {{ {self.camel_name}Plugin }} from './plugin';
export {{ createRouter }} from './router';
'''
        
        index_file = self.plugin_dir / 'src' / 'index.ts'
        with open(index_file, 'w') as f:
            f.write(index_ts)
        
        print(f"Created backend plugin files")
    
    def create_readme(self) -> None:
        """Create README.md file."""
        readme = f'''# {self.pascal_name} Backstage Plugin

{self.description}

## Installation

```bash
yarn add --workspace @backstage/app @backstage/plugin-{self.name}
```

## Configuration

Add to your Backstage app-config.yaml:

```yaml
{self.camel_name}:
  # Plugin configuration here
```

## Usage

Import and use the plugin in your Backstage app:

```typescript
import {{ {self.pascal_name}Page }} from '@backstage/plugin-{self.name}';

// Add to your routes
<Route path="/{self.name}" element={{<{self.pascal_name}Page />}} />
```

## Development

```bash
# Build the plugin
yarn build

# Run tests
yarn test

# Start development server
yarn dev
```

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## License

MIT
'''
        
        readme_file = self.plugin_dir / 'README.md'
        with open(readme_file, 'w') as f:
            f.write(readme)
        
        print(f"Created README.md")
    
    def create_test_file(self) -> None:
        """Create a test template file."""
        test_content = f'''// {self.name} Plugin Tests

describe('{self.pascal_name} Plugin', () => {{
  it('should initialize', () => {{
    expect(true).toBe(true);
  }});

  it('should have correct name', () => {{
    const pluginName = '{self.name}';
    expect(pluginName).toBeDefined();
  }});
}});
'''
        
        src_dir = self.plugin_dir / 'src'
        test_file = src_dir / 'index.test.ts'
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        print(f"Created test template")
    
    def create_plugin(self) -> bool:
        """
        Create complete plugin structure.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"\nScaffolding {self.plugin_type} plugin: {self.name}")
            print("=" * 60)
            
            # Create directory structure
            self.create_directory_structure()
            
            # Create common files
            self.create_package_json()
            self.create_tsconfig()
            self.create_plugin_manifest()
            self.create_readme()
            self.create_test_file()
            
            # Create plugin-specific files
            if self.plugin_type in ['frontend', 'full']:
                self.create_frontend_plugin()
            
            if self.plugin_type in ['backend', 'full']:
                self.create_backend_plugin()
            
            print("=" * 60)
            print(f"\nSuccessfully created {self.name} plugin!")
            print(f"Plugin directory: {self.plugin_dir}")
            print("\nNext steps:")
            print(f"  1. cd {self.plugin_dir}")
            print("  2. yarn install")
            print("  3. yarn build")
            print("  4. yarn dev")
            print()
            
            return True
            
        except Exception as e:
            print(f"Error creating plugin: {e}")
            return False


def main():
    """Main entry point for the scaffolding tool."""
    parser = argparse.ArgumentParser(
        description='Create a new Backstage plugin'
    )
    parser.add_argument(
        '--name',
        required=True,
        help='Plugin name in kebab-case (e.g., my-plugin)'
    )
    parser.add_argument(
        '--description',
        help='Plugin description'
    )
    parser.add_argument(
        '--type',
        choices=['frontend', 'backend', 'full'],
        default='frontend',
        help='Type of plugin to create'
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Output directory for plugin'
    )
    
    args = parser.parse_args()
    
    # Validate plugin name format
    if not all(c.isalnum() or c == '-' for c in args.name):
        print("Error: Plugin name must contain only alphanumeric characters and hyphens")
        sys.exit(1)
    
    # Create scaffolder
    scaffolder = BackstagePluginScaffold(
        name=args.name,
        description=args.description,
        plugin_type=args.type,
        output_dir=args.output_dir
    )
    
    # Generate plugin
    success = scaffolder.create_plugin()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

