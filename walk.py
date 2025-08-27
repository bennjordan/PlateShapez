import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class DirectoryMapper:
    def __init__(
        self,
        ignore_patterns: Optional[List[str]] = None,
        max_depth: int = 10,
        include_content: bool = False,
        content_extensions: Optional[List[str]] = None,
        ignore_hidden: bool = True,
    ):
        self.ignore_patterns = ignore_patterns or [
            "node_modules",
            ".git",
            "dist",
            "build",
            "__pycache__",
        ]
        self.max_depth = max_depth
        self.include_content = include_content
        self.content_extensions = content_extensions  # Allow None to include all extensions
        self.ignore_hidden = ignore_hidden

    def should_ignore(self, name: str) -> bool:
        """Check if a file or directory should be ignored."""
        if self.ignore_hidden and name.startswith("."):
            return True
        return any(pattern in name for pattern in self.ignore_patterns)

    def create_file_node(self, file_path: str) -> Dict:
        """Create a node representing a file."""
        stats = os.stat(file_path)
        node = {
            "type": "file",
            "name": os.path.basename(file_path),
            "path": file_path,
            "size": stats.st_size,
            "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        }

        if self.include_content:
            file_ext = os.path.splitext(file_path)[1].lower()  # Get the file extension
            if self.content_extensions is None or file_ext in self.content_extensions:
                print(f"Reading content for: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        node["content"] = content
                        print(f"Successfully read {len(content)} bytes from {file_path}")
                except Exception as e:
                    print(f"Warning: Could not read content of {file_path}: {e}")
            else:
                print(f"Skipping content for {file_path} - extension not in allowed list")

        return node

    def map_directory(self, dir_path: str, depth: int = 0) -> Dict:
        """Recursively map a directory structure."""
        if depth >= self.max_depth:
            return {
                "type": "directory",
                "name": os.path.basename(dir_path),
                "path": dir_path,
                "children": {"[MAX_DEPTH_REACHED]": {"type": "file", "name": "", "path": ""}},
            }

        result: Dict[str, Any] = {
            "type": "directory",
            "name": os.path.basename(dir_path),
            "path": dir_path,
            "children": {},
        }

        try:
            for entry in os.listdir(dir_path):
                if self.should_ignore(entry):
                    continue

                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    result["children"][entry] = self.map_directory(full_path, depth + 1)
                else:
                    result["children"][entry] = self.create_file_node(full_path)
        except Exception as e:
            print(f"Error mapping directory {dir_path}: {e}")

        return result

    def generate_markdown(self, node: Dict, level: int = 0) -> str:
        """Generate a markdown representation of the directory structure with file contents."""
        indent = "  " * level
        output = ""

        if node["type"] == "directory":
            output += f"{indent}- 📁 **{node['name']}/**\n"
            if "children" in node:
                for child in sorted(node["children"].values(), key=lambda x: x["name"]):
                    output += self.generate_markdown(child, level + 1)
        else:
            output += f"{indent}- 📄 **{node['name']}**\n"
            if self.include_content and "content" in node:
                file_path = node["path"]
                content = node["content"]
                # Escape backticks in content
                content = content.replace("```", "```")
                output += f"\n{indent}  📄 *File Path*: `{file_path}`\n\n"
                output += f"{indent}  ```\n"
                output += f"{indent}  {content}\n"
                output += f"{indent}  ```\n\n"

        return output

    def save_map(self, node: Dict[str, Any], output_path: str, file_format: str = "json") -> None:
        """Save the directory map to a file."""
        if file_format == "markdown":
            content = "# Directory Structure\n\n" + self.generate_markdown(node)
        else:
            content = json.dumps(node, indent=2)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Map a directory structure")
    parser.add_argument("directory", help="Directory to map")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--max-depth", type=int, default=10, help="Maximum depth to traverse (default: 10)"
    )
    parser.add_argument(
        "--include-content", action="store_true", help="Include file contents in the map"
    )
    parser.add_argument(
        "--no-ignore-hidden", action="store_true", help="Do not ignore hidden files"
    )
    parser.add_argument(
        "--content-extensions",
        nargs="*",
        help="File extensions to include content from "
        "(default: all files if --include-content is used)",
    )

    args = parser.parse_args()

    # Debug: Print arguments
    print("Arguments received:")
    print(f"  Directory: {args.directory}")
    print(f"  Output: {args.output}")
    print(f"  Format: {args.format}")
    print(f"  Include content: {args.include_content}")
    print(f"  Max depth: {args.max_depth}")
    print(f"  Ignore hidden: {not args.no_ignore_hidden}")
    print(f"  Content extensions: {args.content_extensions}")

    if args.include_content and args.content_extensions is None:
        # Include content from all files
        content_extensions = None
    else:
        content_extensions = args.content_extensions

    mapper = DirectoryMapper(
        max_depth=args.max_depth,
        include_content=args.include_content,
        content_extensions=content_extensions,
        ignore_hidden=not args.no_ignore_hidden,
    )

    print(f"\nMapping directory: {args.directory}")
    dir_map = mapper.map_directory(args.directory)
    first_child = None
    # Debug: Print a sample of the map structure
    print("\nMap structure sample:")
    if "children" in dir_map:
        first_child = next(iter(dir_map["children"].values()), None)
    if first_child:
        print(f"Sample child node: {json.dumps(first_child, indent=2)[:200]}...")

    mapper.save_map(dir_map, args.output, args.format)
    print(f"\nMap saved to: {args.output}")


if __name__ == "__main__":
    main()
