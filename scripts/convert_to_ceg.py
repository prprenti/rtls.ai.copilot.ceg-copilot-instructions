#!/usr/bin/env python3
"""
Convert CEG Copilot Instructions repository to CEG variant.

This script performs the bulk rebranding from CEG to CEG while preserving
all functionality and structure. It handles:
- Plugin name updates in plugin.json files
- Agent file updates
- Skill file updates  
- MCP configuration updates
- MCP server code updates
- Documentation updates
- Test file updates

Usage:
    python scripts/convert_to_ceg.py --source <ddg-repo> --target <ceg-repo>
    
    # Dry run (preview changes only)
    python scripts/convert_to_ceg.py --source <ddg-repo> --target <ceg-repo> --dry-run
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class CEGConverter:
    """Convert CEG repository to CEG variant."""
    
    # Text replacements to apply
    REPLACEMENTS = {
        # Plugin names
        'ceg-access': 'ceg-access',
        'ceg-block-diagram': 'ceg-block-diagram',
        'ceg-build-run': 'ceg-build-run',
        'ceg-fe-setup': 'ceg-fe-setup',
        'ceg-hsd': 'ceg-hsd',
        'ceg-ip-management': 'ceg-ip-management',
        'ceg-rtl-design': 'ceg-rtl-design',
        'ceg-runfv': 'ceg-runfv',
        'ceg-turnin': 'ceg-turnin',
        'ceg-validation': 'ceg-validation',
        
        # File names
        'ceg_repos.yml': 'ceg_repos.yml',
        'ceg_repos': 'ceg_repos',
        
        # Logger names
        'ceg-mcp': 'ceg-mcp',
        'cegMCP': 'cegMCP',
        
        # Organization names
        'CEG': 'CEG',
        'Central Engineering Group': 'Central Engineering Group',
        
        # Repository references
        'rtls.ai.copilot.ceg-copilot-instructions': 'rtls.ai.copilot.ceg-copilot-instructions',
        'ceg-copilot-instructions': 'ceg-copilot-instructions',
    }
    
    # MCP server name mappings (without ddg-/ceg- prefix)
    MCP_SERVER_NAMES = {
        'build-run': 'ceg-build-run',
        'access': 'ceg-access',
        'hsd': 'ceg-hsd',
        'runfv': 'ceg-runfv',
        'turnin': 'ceg-turnin',
        'validation': 'ceg-validation',
        'fe-setup': 'ceg-fe-setup',
    }
    
    def __init__(self, source_dir: Path, target_dir: Path, dry_run: bool = False):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self.dry_run = dry_run
        self.changes: List[Tuple[str, str]] = []
        
    def log_change(self, description: str, detail: str = ""):
        """Log a change that will be made."""
        self.changes.append((description, detail))
        if self.dry_run:
            print(f"[DRY RUN] {description}")
            if detail:
                print(f"  {detail}")
        else:
            print(f"✓ {description}")
            
    def apply_text_replacements(self, text: str, filepath: str = "") -> str:
        """Apply text replacements to content."""
        original = text
        for old, new in self.REPLACEMENTS.items():
            text = text.replace(old, new)
        
        if text != original and filepath:
            self.log_change(f"Applied text replacements", filepath)
        
        return text
    
    def update_plugin_json(self, plugin_dir: Path) -> None:
        """Update plugin.json file in a plugin directory."""
        plugin_json_path = plugin_dir / "plugin.json"
        if not plugin_json_path.exists():
            return
            
        with open(plugin_json_path, 'r') as f:
            data = json.load(f)
        
        original_name = data.get('name', '')
        
        # Update name field
        if data.get('name', '').startswith('ddg-'):
            data['name'] = data['name'].replace('ddg-', 'ceg-')
            self.log_change(f"Updated plugin name: {original_name} → {data['name']}", 
                          str(plugin_json_path.relative_to(self.source_dir)))
        
        # Add 'ceg' to keywords if not present
        if 'keywords' in data and 'ceg' not in data['keywords']:
            data['keywords'].append('ceg')
            self.log_change(f"Added 'ceg' to keywords", 
                          str(plugin_json_path.relative_to(self.source_dir)))
        
        if not self.dry_run:
            target_path = self.target_dir / plugin_json_path.relative_to(self.source_dir)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w') as f:
                json.dump(data, f, indent=2)
                f.write('\n')
    
    def update_mcp_json(self, plugin_dir: Path) -> None:
        """Update .mcp.json file in a plugin directory."""
        mcp_json_path = plugin_dir / ".mcp.json"
        if not mcp_json_path.exists():
            return
            
        with open(mcp_json_path, 'r') as f:
            data = json.load(f)
        
        # Update server names in mcpServers
        if 'mcpServers' in data:
            new_servers = {}
            for server_name, config in data['mcpServers'].items():
                # Check if this is a known MCP server that needs renaming
                if server_name in self.MCP_SERVER_NAMES:
                    new_name = self.MCP_SERVER_NAMES[server_name]
                    new_servers[new_name] = config
                    self.log_change(f"Updated MCP server name: {server_name} → {new_name}",
                                  str(mcp_json_path.relative_to(self.source_dir)))
                else:
                    new_servers[server_name] = config
            
            data['mcpServers'] = new_servers
        
        if not self.dry_run:
            target_path = self.target_dir / mcp_json_path.relative_to(self.source_dir)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w') as f:
                json.dump(data, f, indent=2)
                f.write('\n')
    
    def update_mcp_server_code(self, plugin_dir: Path) -> None:
        """Update MCP server Python files."""
        mcp_server_dir = plugin_dir / "mcp-server"
        if not mcp_server_dir.exists():
            return
        
        for py_file in mcp_server_dir.glob("server_*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
            
            original = content
            
            # Update FastMCP registration names
            for old_name, new_name in self.MCP_SERVER_NAMES.items():
                pattern = f'FastMCP\\("{old_name}"\\)'
                replacement = f'FastMCP("{new_name}")'
                content = re.sub(pattern, replacement, content)
            
            if content != original:
                self.log_change(f"Updated FastMCP registration",
                              str(py_file.relative_to(self.source_dir)))
                
                if not self.dry_run:
                    target_path = self.target_dir / py_file.relative_to(self.source_dir)
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'w') as f:
                        f.write(content)
    
    def update_yaml_frontmatter(self, file_path: Path) -> None:
        """Update YAML frontmatter in agent or skill files."""
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file has YAML frontmatter
        if not content.startswith('---\n'):
            return
        
        original = content
        
        # Add 'ceg' to keywords if not present
        # This is a simple regex-based approach
        if 'keywords:' in content:
            # Check if 'ceg' is already in keywords
            if 'ceg' not in content.split('keywords:')[1].split('\n')[0]:
                # Add ceg to keywords array
                content = re.sub(
                    r'(keywords:\s*\[)([^\]]+)(\])',
                    lambda m: f"{m.group(1)}{m.group(2)}, ceg{m.group(3)}",
                    content
                )
        
        # Apply general text replacements
        content = self.apply_text_replacements(content, "")
        
        if content != original:
            self.log_change(f"Updated YAML frontmatter",
                          str(file_path.relative_to(self.source_dir)))
            
            if not self.dry_run:
                target_path = self.target_dir / file_path.relative_to(self.source_dir)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, 'w') as f:
                    f.write(content)
    
    def process_text_file(self, file_path: Path) -> None:
        """Process a text file with replacements."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            return
        
        new_content = self.apply_text_replacements(content, str(file_path.relative_to(self.source_dir)))
        
        # Always write the file, even if no changes (to ensure all files are copied)
        if not self.dry_run:
            target_path = self.target_dir / file_path.relative_to(self.source_dir)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w') as f:
                f.write(new_content)
    
    def copy_file(self, file_path: Path) -> None:
        """Copy a file without modifications."""
        if not self.dry_run:
            target_path = self.target_dir / file_path.relative_to(self.source_dir)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_path)
    
    def convert(self) -> None:
        """Perform the full conversion."""
        print(f"Converting CEG repository to CEG...")
        print(f"Source: {self.source_dir}")
        print(f"Target: {self.target_dir}")
        if self.dry_run:
            print("DRY RUN MODE - No files will be modified")
        print()
        
        if not self.source_dir.exists():
            print(f"Error: Source directory does not exist: {self.source_dir}")
            sys.exit(1)
        
        if not self.dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process plugins
        plugins_dir = self.source_dir / "plugins"
        if plugins_dir.exists():
            print("Processing plugins...")
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    print(f"\n  Plugin: {plugin_dir.name}")
                    
                    # Update plugin.json
                    self.update_plugin_json(plugin_dir)
                    
                    # Update .mcp.json
                    self.update_mcp_json(plugin_dir)
                    
                    # Update MCP server code
                    self.update_mcp_server_code(plugin_dir)
                    
                    # Update agent files
                    for agent_file in plugin_dir.glob("*.agent.md"):
                        self.update_yaml_frontmatter(agent_file)
                    
                    # Update skill files
                    skills_dir = plugin_dir / "skills"
                    if skills_dir.exists():
                        for skill_dir in skills_dir.iterdir():
                            if skill_dir.is_dir():
                                skill_file = skill_dir / "SKILL.md"
                                if skill_file.exists():
                                    self.update_yaml_frontmatter(skill_file)
                    
                    # Copy and rename ceg_repos.yml to ceg_repos.yml if it exists
                    ceg_repos_file = plugin_dir / "ceg_repos.yml"
                    if ceg_repos_file.exists():
                        with open(ceg_repos_file, 'r') as f:
                            content = f.read()
                        
                        # Apply replacements (but keep infrastructure names like ddgcth, ddgip)
                        content = content.replace('CEG', 'CEG').replace('Central Engineering Group', 'Central Engineering Group')
                        
                        target_path = self.target_dir / ceg_repos_file.relative_to(self.source_dir)
                        target_path = target_path.parent / "ceg_repos.yml"
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if not self.dry_run:
                            with open(target_path, 'w') as f:
                                f.write(content)
                        
                        self.log_change(f"Renamed ceg_repos.yml → ceg_repos.yml", 
                                      str(ceg_repos_file.relative_to(self.source_dir)))
                    
                    # Copy/process all other files
                    for file_path in plugin_dir.rglob("*"):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(self.source_dir)
                            
                            # Skip files we've already processed
                            if file_path.name in ['plugin.json', '.mcp.json', 'ceg_repos.yml'] or \
                               file_path.name.endswith('.agent.md') or \
                               file_path.name == 'SKILL.md':
                                continue
                            
                            # Process text files with replacements
                            if file_path.suffix in ['.md', '.py', '.sh', '.txt', '.yaml', '.yml', '.json']:
                                self.process_text_file(file_path)
                            else:
                                # Copy binary files as-is
                                self.copy_file(file_path)
        
        # Process documentation
        print("\n\nProcessing documentation...")
        for doc_file in ['README.md', 'copy-me-to-copilot-instructions.md']:
            doc_path = self.source_dir / doc_file
            if doc_path.exists():
                self.process_text_file(doc_path)
        
        # Process .github/copilot-instructions.md
        copilot_inst = self.source_dir / ".github" / "copilot-instructions.md"
        if copilot_inst.exists():
            self.process_text_file(copilot_inst)
        
        # Process docs directory
        docs_dir = self.source_dir / "docs"
        if docs_dir.exists():
            for doc_file in docs_dir.rglob("*.md"):
                self.process_text_file(doc_file)
        
        # Copy scripts directory
        print("\nProcessing scripts...")
        scripts_dir = self.source_dir / "scripts"
        if scripts_dir.exists():
            for script_file in scripts_dir.rglob("*"):
                if script_file.is_file():
                    self.process_text_file(script_file)
        
        # Copy tests directory
        print("\nProcessing tests...")
        tests_dir = self.source_dir / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.rglob("*.py"):
                self.process_text_file(test_file)
        
        # Copy other files
        print("\nCopying additional files...")
        for item in ['pyproject.toml', 'uv.lock', 'Makefile', '.gitignore']:
            source_path = self.source_dir / item
            if source_path.exists():
                if source_path.is_file():
                    self.process_text_file(source_path)
        
        # Copy code_review directory
        code_review_dir = self.source_dir / "code_review"
        if code_review_dir.exists():
            for review_file in code_review_dir.rglob("*"):
                if review_file.is_file():
                    self.process_text_file(review_file)
        
        # Copy personal_skills directory
        print("\nProcessing personal_skills...")
        personal_skills_dir = self.source_dir / "personal_skills"
        if personal_skills_dir.exists():
            for skill_file in personal_skills_dir.rglob("*"):
                if skill_file.is_file():
                    self.process_text_file(skill_file)
        
        # Copy uncommon_repo_instructions directory
        print("\nProcessing uncommon_repo_instructions...")
        uncommon_dir = self.source_dir / "uncommon_repo_instructions"
        if uncommon_dir.exists():
            for inst_file in uncommon_dir.rglob("*"):
                if inst_file.is_file():
                    self.process_text_file(inst_file)
        
        # Copy shell scripts at root
        print("\nCopying shell scripts...")
        for script in ['bulk_install.sh', 'force_deploy_plugins.sh', 'setup_home_symlinks.sh']:
            script_path = self.source_dir / script
            if script_path.exists():
                self.process_text_file(script_path)
        
        print("\n" + "="*60)
        print(f"Conversion complete!")
        print(f"Total changes: {len(self.changes)}")
        
        if self.dry_run:
            print("\nThis was a dry run. No files were modified.")
            print("Run without --dry-run to apply changes.")
        else:
            print(f"\nCEG repository created at: {self.target_dir}")
            print("\nNext steps:")
            print("1. Review the changes")
            print("2. Run validation: make validate")
            print("3. Test plugin installation")
            print("4. Commit and push to CEG repository")


def main():
    parser = argparse.ArgumentParser(
        description="Convert CEG Copilot Instructions repository to CEG variant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview changes)
  python scripts/convert_to_ceg.py --source . --target ../ceg-copilot-instructions --dry-run
  
  # Perform conversion
  python scripts/convert_to_ceg.py --source . --target ../ceg-copilot-instructions
        """
    )
    
    parser.add_argument('--source', required=True, 
                       help='Path to source CEG repository')
    parser.add_argument('--target', required=True,
                       help='Path to target CEG repository (will be created)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without modifying files')
    
    args = parser.parse_args()
    
    converter = CEGConverter(args.source, args.target, args.dry_run)
    converter.convert()


if __name__ == '__main__':
    main()
