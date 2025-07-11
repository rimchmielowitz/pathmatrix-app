#!/usr/bin/env python3
"""
Auto-generate FUNCTION_REFERENCE.md from source code docstrings.

This script extracts all function docstrings, signatures, and metadata
to create a comprehensive function reference document.
"""

import ast
import inspect
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util


class FunctionDocExtractor(ast.NodeVisitor):
    """Extract function documentation from Python AST."""
    
    def __init__(self, source_code: str):
        """Initialize with source code."""
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.functions: List[Dict[str, Any]] = []
        self.classes: List[Dict[str, Any]] = []
        self.module_docstring: str = ""
        self.current_class: Optional[str] = None
    
    def visit_Module(self, node: ast.Module) -> None:
        """Extract module docstring."""
        if (node.body and isinstance(node.body[0], ast.Expr) 
            and isinstance(node.body[0].value, ast.Constant)):
            self.module_docstring = node.body[0].value.value
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Extract class information."""
        old_class = self.current_class
        self.current_class = node.name
        
        docstring = ast.get_docstring(node)
        if docstring:
            self.classes.append({
                'name': node.name,
                'docstring': docstring,
                'lineno': node.lineno,
                'bases': [self._get_name(base) for base in node.bases]
            })
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Extract function information."""
        docstring = ast.get_docstring(node)
        
        # Skip private functions (unless they have docstrings)
        if node.name.startswith('_') and not docstring:
            return
            
        if docstring:
            function_info = {
                'name': node.name,
                'docstring': docstring,
                'lineno': node.lineno,
                'signature': self._get_signature(node),
                'args': self._get_args(node),
                'returns': self._get_return_annotation(node),
                'class': self.current_class,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'decorators': [self._get_name(dec) for dec in node.decorator_list]
            }
            self.functions.append(function_info)
        
        self.generic_visit(node)
    
    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Generate function signature string."""
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_annotation_string(arg.annotation)}"
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {self._get_annotation_string(node.args.vararg.annotation)}"
            args.append(vararg)
        
        # **kwargs
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {self._get_annotation_string(node.args.kwarg.annotation)}"
            args.append(kwarg)
        
        # Return annotation
        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {self._get_annotation_string(node.returns)}"
        
        signature = f"def {node.name}({', '.join(args)}){return_annotation}"
        return signature
    
    def _get_args(self, node: ast.FunctionDef) -> List[Dict[str, str]]:
        """Extract argument information."""
        args = []
        for arg in node.args.args:
            arg_info = {
                'name': arg.arg,
                'type': self._get_annotation_string(arg.annotation) if arg.annotation else 'Any'
            }
            args.append(arg_info)
        return args
    
    def _get_return_annotation(self, node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation."""
        if node.returns:
            return self._get_annotation_string(node.returns)
        return None
    
    def _get_annotation_string(self, annotation) -> str:
        """Convert annotation AST node to string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        elif isinstance(annotation, ast.Attribute):
            return f"{self._get_annotation_string(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.Subscript):
            value = self._get_annotation_string(annotation.value)
            slice_val = self._get_annotation_string(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Tuple):
            elements = [self._get_annotation_string(elt) for elt in annotation.elts]
            return f"({', '.join(elements)})"
        else:
            # Fallback to source code extraction
            try:
                start_line = annotation.lineno - 1
                start_col = annotation.col_offset
                end_line = annotation.end_lineno - 1 if annotation.end_lineno else start_line
                end_col = annotation.end_col_offset if annotation.end_col_offset else len(self.source_lines[start_line])
                
                if start_line == end_line:
                    return self.source_lines[start_line][start_col:end_col]
                else:
                    lines = []
                    lines.append(self.source_lines[start_line][start_col:])
                    for i in range(start_line + 1, end_line):
                        lines.append(self.source_lines[i])
                    lines.append(self.source_lines[end_line][:end_col])
                    return ''.join(lines)
            except (AttributeError, IndexError):
                return "Any"
    
    def _get_name(self, node) -> str:
        """Get name from various AST node types."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)


def load_module_from_path(file_path: Path):
    """Dynamically load a Python module from file path."""
    try:
        spec = importlib.util.spec_from_file_location("target_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"Warning: Could not import module {file_path}: {e}")
        return None


def get_git_version() -> str:
    """Get current git version/commit."""
    try:
        import subprocess
        result = subprocess.run(['git', 'describe', '--tags', '--always'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # Fallback to commit hash
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def generate_markdown_docs(extractor: FunctionDocExtractor, version: str) -> str:
    """Generate markdown documentation from extracted data."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    
    md_content = f"""# PathMatrix Optimizer - Function Reference

> **Auto-generated from source code docstrings**  
> Version: `{version}` | Last updated: `{timestamp}`

This document contains the complete function reference extracted from the source code. For a developer-friendly guide, see [API_REFERENCE.md](API_REFERENCE.md).

## Table of Contents

"""
    
    # Generate table of contents
    if extractor.classes:
        md_content += "- [Classes](#classes)\n"
    if extractor.functions:
        md_content += "- [Functions](#functions)\n"
        
        # Group functions by category
        categories = {}
        for func in extractor.functions:
            if func['class']:
                category = f"Class: {func['class']}"
            elif 'render' in func['name']:
                category = "UI Functions"
            elif func['name'] in ['call_solver_api', 'get_package_distribution', 'create_demand_map']:
                category = "Core Functions"
            elif 'on_' in func['name'] or func['name'] in ['initialize_session_state']:
                category = "Utility Functions"
            else:
                category = "Other Functions"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(func)
        
        for category in sorted(categories.keys()):
            md_content += f"  - [{category}](#{category.lower().replace(' ', '-').replace(':', '')})\n"
    
    md_content += "\n---\n\n"
    
    # Module docstring
    if extractor.module_docstring:
        md_content += f"## Module Description\n\n{extractor.module_docstring}\n\n---\n\n"
    
    # Classes
    if extractor.classes:
        md_content += "## Classes\n\n"
        for cls in extractor.classes:
            md_content += f"### `{cls['name']}`\n\n"
            md_content += f"**File:** `app.py` | **Line:** {cls['lineno']}\n\n"
            
            if cls['bases']:
                bases_str = ', '.join(cls['bases'])
                md_content += f"**Inherits from:** {bases_str}\n\n"
            
            md_content += f"**Description:**\n{cls['docstring']}\n\n"
            md_content += "---\n\n"
    
    # Functions by category
    if extractor.functions:
        md_content += "## Functions\n\n"
        
        # Group functions by category
        categories = {}
        for func in extractor.functions:
            if func['class']:
                category = f"Class: {func['class']}"
            elif 'render' in func['name']:
                category = "UI Functions"
            elif func['name'] in ['call_solver_api', 'get_package_distribution', 'create_demand_map']:
                category = "Core Functions"
            elif 'on_' in func['name'] or func['name'] in ['initialize_session_state']:
                category = "Utility Functions"
            else:
                category = "Other Functions"
            
            if category not in categories:
                categories[category] = []
            categories[category].append(func)
        
        for category in sorted(categories.keys()):
            md_content += f"### {category}\n\n"
            
            for func in sorted(categories[category], key=lambda x: x['name']):
                md_content += f"#### `{func['name']}`\n\n"
                md_content += f"**File:** `app.py` | **Line:** {func['lineno']}\n\n"
                
                # Function signature
                md_content += "```python\n"
                md_content += func['signature']
                md_content += "\n```\n\n"
                
                # Description
                md_content += f"**Description:**\n{func['docstring']}\n\n"
                
                # Arguments
                if func['args']:
                    md_content += "**Arguments:**\n"
                    for arg in func['args']:
                        md_content += f"- `{arg['name']}` ({arg['type']})\n"
                    md_content += "\n"
                
                # Return type
                if func['returns']:
                    md_content += f"**Returns:**\n- `{func['returns']}`\n\n"
                
                # Decorators
                if func['decorators']:
                    decorators_str = ', '.join(func['decorators'])
                    md_content += f"**Decorators:** {decorators_str}\n\n"
                
                # Async function
                if func['is_async']:
                    md_content += "**Note:** This is an async function.\n\n"
                
                md_content += "---\n\n"
    
    # Footer
    md_content += f"""
*This documentation was automatically generated from source code docstrings.*  
*For questions or corrections, please see the [API Reference](API_REFERENCE.md) or [open an issue](https://github.com/your-username/pathmatrix-optimizer/issues).*

**Generation Info:**
- Source: `app.py`
- Version: `{version}`
- Generated: `{timestamp}`
- Python: `{sys.version.split()[0]}`
"""
    
    return md_content


def main():
    """Main function to generate function documentation."""
    # Define paths
    project_root = Path(__file__).parent.parent
    source_file = project_root / "app.py"
    output_file = project_root / "docs" / "FUNCTION_REFERENCE.md"
    
    # Check if source file exists
    if not source_file.exists():
        print(f"Error: Source file {source_file} not found!")
        sys.exit(1)
    
    # Create docs directory if it doesn't exist
    output_file.parent.mkdir(exist_ok=True)
    
    # Read source code
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
    except Exception as e:
        print(f"Error reading source file: {e}")
        sys.exit(1)
    
    # Parse AST and extract documentation
    try:
        tree = ast.parse(source_code)
        extractor = FunctionDocExtractor(source_code)
        extractor.visit(tree)
    except Exception as e:
        print(f"Error parsing source code: {e}")
        sys.exit(1)
    
    # Get version info
    version = get_git_version()
    
    # Generate markdown
    try:
        markdown_content = generate_markdown_docs(extractor, version)
    except Exception as e:
        print(f"Error generating markdown: {e}")
        sys.exit(1)
    
    # Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✅ Successfully generated {output_file}")
        print(f"📊 Functions documented: {len(extractor.functions)}")
        print(f"📊 Classes documented: {len(extractor.classes)}")
        print(f"🔖 Version: {version}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()