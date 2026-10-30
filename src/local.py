#!/usr/bin/env python3
"""Roll clones.md up into local.md: one entry per project, not per clone."""

import re
import sys
from collections import defaultdict

from pysyte.types.paths import makepath

clone_pattern = re.compile(
    r"^### (?P<name>.+?)\n"
    r"- \*\*Path\*\*: `(?P<path>.+?)`\n"
    r"- \*\*Category\*\*: (?P<category>\w+)\n",
    re.MULTILINE,
)
project_pattern = re.compile(r"^## (?P<key>\S+)\n(?P<body>(?:^(?!## ).*\n?)*)", re.MULTILINE)
field_pattern = re.compile(r"^(\w+): ?(.*)$", re.MULTILINE)
status_rank = {"ACTIVE": 0, "UNSURE": 1, "ANCIENT": 2}
status_name = {"ACTIVE": "active", "UNSURE": "unsure", "ANCIENT": "ancient"}
default_fields = ["name", "status", "path", "keywords", "one_liner", "clones"]


def group_key(clone_name: str) -> str:
    """The mechanical grouping key for a clone name: parent dir, or itself.

    >>> assert group_key("pysyse/__main__") == "pysyse"
    >>> assert group_key("chats") == "chats"
    """
    return clone_name.split("/", 1)[0]


def preferred_path(paths: list[str]) -> str:
    """Prefer __main__, else the shortest path, else the first.

    >>> assert preferred_path(["/a/code", "/a/__main__"]) == "/a/__main__"
    >>> assert preferred_path(["/a/trees", "/a/code"]) == "/a/code"
    """
    for path in paths:
        if path.endswith("/__main__"):
            return path
    return sorted(paths, key=len)[0]


def parse_existing(local_md: str) -> dict[str, dict[str, str]]:
    """Read curated name/keywords/one_liner fields back from an existing local.md.

    >>> assert parse_existing("## a\\nname: A\\n") == {"a": {"name": "A", "keywords": "TODO", "one_liner": "TODO"}}
    """
    curated = {}
    for match in project_pattern.finditer(local_md):
        fields = dict(field_pattern.findall(match["body"]))
        curated[match["key"]] = {
            "name": fields.get("name", match["key"]),
            "keywords": fields.get("keywords", "TODO"),
            "one_liner": fields.get("one_liner", "TODO"),
        }
    return curated


def build_projects(clones_md: str, curated: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Group clones by project, rolling up the most-active status.

    >>> report = "### a/x\\n- **Path**: `/a/x`\\n- **Category**: ACTIVE\\n"
    >>> assert build_projects(report, {})["a"]["status"] == "active"
    >>> assert build_projects(report, {})["a"]["clones"] == "x"
    """
    by_group = defaultdict(list)
    for match in clone_pattern.finditer(clones_md):
        by_group[group_key(match["name"])].append((match["name"], match["path"], match["category"]))
    projects = {}
    for key, clones in sorted(by_group.items()):
        best_category = min((category for _, _, category in clones), key=lambda category: status_rank[category])
        curated_entry = curated.get(key, {"name": key, "keywords": "TODO", "one_liner": "TODO"})
        projects[key] = curated_entry | {
            "status": status_name[best_category],
            "path": preferred_path([path for _, path, _ in clones]),
            "clones": ", ".join(name.split("/", 1)[1] if "/" in name else name for name, _, _ in clones),
        }
    return projects


def render(projects: dict[str, dict[str, str]]) -> str:
    """Render project records back to local.md's `## key` / `field: value` format.

    >>> fields = {"name": "A", "status": "s", "path": "p", "keywords": "k", "one_liner": "o", "clones": "c"}
    >>> text = render({"a": fields})
    >>> assert text.startswith("## a\\nname: A\\n")
    >>> assert text.endswith("clones: c\\n")
    """
    sections = [
        "\n".join([f"## {key}"] + [f"{field}: {fields[field]}" for field in default_fields])
        for key, fields in projects.items()
    ]
    return "\n\n".join(sections) + "\n"


def regenerate(clones_md: str, existing_local_md: str) -> str:
    """The full clones.md -> local.md transform, as one pure function main() can call."""
    return render(build_projects(clones_md, parse_existing(existing_local_md)))


def main() -> int:
    src_dir = makepath(__file__).parent
    clones_md = (src_dir / "clones.md").text()
    local_path = src_dir / "local.md"
    existing_local_md = local_path.text() if local_path.exists() else ""
    local_path.write_text(regenerate(clones_md, existing_local_md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
