"""
Academic Intelligence Module

This module contains design specifications and academic features
for the Lumina Academic learning platform.
"""

import json
from pathlib import Path


class DesignConfig:
    """Load and manage design configuration."""
    
    def __init__(self):
        self.design_file = Path(__file__).parent / "DESIGN.md"
        self.colors = self._load_colors()
    
    def _load_colors(self) -> dict:
        """Load color scheme from DESIGN.md."""
        if self.design_file.exists():
            with open(self.design_file, 'r') as f:
                # Parse YAML frontmatter
                content = f.read()
                if content.startswith('---'):
                    lines = content.split('\n')
                    colors_dict = {}
                    in_colors = False
                    for line in lines[1:]:
                        if line.startswith('---'):
                            break
                        if line.startswith('colors:'):
                            in_colors = True
                            continue
                        if in_colors and line.startswith('  '):
                            key, value = line.strip().split(': ')
                            colors_dict[key] = value.strip("'\"")
                    return colors_dict
        return {}
    
    def get_color(self, name: str) -> str:
        """Get a color by name."""
        return self.colors.get(name, "#000000")
    
    def get_all_colors(self) -> dict:
        """Get all colors."""
        return self.colors.copy()


# Create global design instance
design = DesignConfig()


__all__ = ["DesignConfig", "design"]
