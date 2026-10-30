#!/usr/bin/env python3
"""
Repository Clone Analyzer

Analyzes git repositories in a directory tree and categorizes them based on activity level.
Designed specifically for analyzing multiple clones of GitHub repositories organized by branch.

Categories:
- ACTIVE: Repositories that are currently being worked on
- ANCIENT: Repositories that are old and safe to delete locally
- UNSURE: Repositories that need manual review before deletion

Author: jalanb
"""

import os
import sys
import subprocess
import argparse
from datetime import (
    datetime, 
    timedelta,
)
from textwrap import dedent
from dataclasses import dataclass
from collections import defaultdict

from pysyte.cli import argumenta
from pyste.types.paths import (
    StrPath,
    NonePath,
    path,
)

@dataclass
class RepoInfo:
    """Information about a git repository."""
    path: StrPath
    name: str
    has_claude_md: bool
    has_uncommitted_changes: bool
    has_untracked_files: bool
    untracked_count: int
    has_remote: bool
    last_commit_date: datetime | None
    days_since_last_commit: int | None
    total_commits: int
    category: str
    reason: str
    suggested_command: str = ""


class RepositoryAnalyzer:
    """
    Analyzes git repositories and categorizes them based on activity.

    Rules for categorization:

    ACTIVE (keep these):
    - Has a CLAUDE.md file (indicates current AI assistance/development)
    - Has uncommitted changes (work in progress)
    - No remote configured but has commits/files (new local project not yet pushed)
    - Has recent commits (within last 365 days)
    - Has substantial untracked files (>5 files, indicates active development)

    ANCIENT (safe to delete locally):
    - Last commit is over 365 days old AND has fewer than 3 total commits
    - No commits at all AND no untracked files
    - Very old repositories (>2 years) with no recent activity

    UNSURE (needs manual review):
    - No commits but has untracked files (new project or abandoned work?)
    - Edge cases that don't fit clear patterns
    - Repositories with unusual characteristics
    """

    def __init__(self, root_dir: FilePath):
        """Initialize analyzer with root directory."""
        self.root_dir = Path(root_dir).expanduser().resolve()
        self.repos: list[RepoInfo] = []
        self.categories: dict[str, list[RepoInfo]] = defaultdict(list)

    def find_git_repositories(self) -> list[Path]:
        git_repos = []
        # Find all .git directories up to depth 3 to handle nested clones
        for git_dir in self.root_dir.rglob('.git'):
            if git_dir.is_dir():
                repo_path = git_dir.parent
                git_repos.append(repo_path)

        return sorted(git_repos)

    def run_git_command(self, repo_path: Path, command: list[str]) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False, ""

    def check_claude_md(self, repo_path: Path) -> bool:
        """Check if repository has a CLAUDE.md file."""
        claude_files = ['CLAUDE.md', 'claude.md', 'Claude.md']
        return any((repo_path / filename).exists() for filename in claude_files)

    def check_uncommitted_changes(self, repo_path: Path) -> bool:
        """Check if repository has uncommitted changes."""
        success, _ = self.run_git_command(repo_path, ['diff', '--cached', '--quiet'])
        if not success:
            return True
        success, _ = self.run_git_command(repo_path, ['diff', '--quiet'])
        return not success

    def check_untracked_files(self, repo_path: Path) -> tuple[bool, int]:
        success, output = self.run_git_command(
            repo_path,
            ['ls-files', '--others', '--exclude-standard']
        )
        if not success:
            return False, 0
        untracked_files = [line for line in output.split('\n') if line.strip()]
        return len(untracked_files) > 0, len(untracked_files)

    def check_has_remote(self, repo_path: Path) -> bool:
        """A repository without remotes is likely a new local project not yet pushed - strong ACTIVE indicator."""
        success, output = self.run_git_command(repo_path, ['remote'])
        if not success:
            return False
        remotes = [line.strip() for line in output.split('\n') if line.strip()]
        return len(remotes) > 0

    def get_last_commit_info(self, repo_path: Path) -> tuple[datetime | None, int]:
        success, count_output = self.run_git_command(repo_path, ['rev-list', '--count', 'HEAD'])
        total_commits = int(count_output) if success and count_output.isdigit() else 0
        if total_commits == 0:
            return None, 0
        success, date_output = self.run_git_command(
            repo_path,
            ['log', '-1', '--format=%ci']
        )
        if not success or not date_output:
            return None, total_commits
        try:
            # Parse git date format: "2024-06-30 19:04:23 +0100"
            date_str = date_output.split(' ')[0]  # Just the date part
            last_commit_date = datetime.strptime(date_str, '%Y-%m-%d')
            return last_commit_date, total_commits
        except ValueError:
            return None, total_commits

    def categorize_repository(self, repo_info: RepoInfo) -> tuple[str, str]:
        # ACTIVE criteria
        if repo_info.has_claude_md:
            return "ACTIVE", "Has CLAUDE.md file"
        if repo_info.has_uncommitted_changes:
            return "ACTIVE", "Has uncommitted changes"
        if not repo_info.has_remote and (repo_info.total_commits > 0 or repo_info.has_untracked_files):
            return "ACTIVE", "No remote configured - likely new local project"
        if (repo_info.days_since_last_commit is not None and
            repo_info.days_since_last_commit < 365):
            return "ACTIVE", f"Recent commits ({repo_info.days_since_last_commit} days ago)"
        if repo_info.untracked_count > 5:
            return "ACTIVE", f"Many untracked files ({repo_info.untracked_count} files)"
        if repo_info.total_commits == 0 and not repo_info.has_untracked_files:
            return "ANCIENT", "No commits and no untracked files"
        if (repo_info.days_since_last_commit is not None and
            repo_info.days_since_last_commit > 365 and
            repo_info.total_commits < 3):
            return "ANCIENT", f"Old ({repo_info.days_since_last_commit} days) with few commits ({repo_info.total_commits})"
        if (repo_info.days_since_last_commit is not None and
            repo_info.days_since_last_commit > 730):  # 2 years
            return "ANCIENT", f"Very old ({repo_info.days_since_last_commit} days ago)"
        if repo_info.total_commits == 0 and repo_info.has_untracked_files:
            return "UNSURE", f"No commits but has {repo_info.untracked_count} untracked files"
        if (repo_info.days_since_last_commit is not None and
            365 <= repo_info.days_since_last_commit <= 730 and
            repo_info.total_commits >= 3):
            return "UNSURE", f"Moderately old ({repo_info.days_since_last_commit} days) but substantial history"
        return "UNSURE", "Doesn't fit clear patterns - needs manual review"

    def generate_suggested_command(self, repo_info: RepoInfo) -> str:
        """Generate a suggested bash command for the repository."""
        repo_path_str = str(repo_info.path)
        if repo_info.category == "ANCIENT":
            return f"rm -rf {repo_path_str} # {repo_info.reason}"
        elif repo_info.has_uncommitted_changes:
            return f"cd {repo_path_str} && git status # {repo_info.reason}"
        elif not repo_info.has_remote:
            return f"cd {repo_path_str} && ls # {repo_info.reason}"
        else:
            # For active/unsure repos with remote and no uncommitted changes
            # Always pull --rebase for your own projects and external ones
            return f"cd {repo_path_str} && git pull --rebase # {repo_info.reason}"

    def analyze_repository(self, repo_path: Path) -> RepoInfo:
        """Analyze a single repository and return its information."""
        # Generate a readable name for the repository
        relative_path = repo_path.relative_to(self.root_dir)
        name = str(relative_path)
        # Gather repository information
        has_claude_md = self.check_claude_md(repo_path)
        has_uncommitted_changes = self.check_uncommitted_changes(repo_path)
        has_untracked_files, untracked_count = self.check_untracked_files(repo_path)
        has_remote = self.check_has_remote(repo_path)
        last_commit_date, total_commits = self.get_last_commit_info(repo_path)
        # Calculate days since last commit
        days_since_last_commit = None
        if last_commit_date:
            days_since_last_commit = (datetime.now() - last_commit_date).days
        # Create repo info object (with empty category and reason for now)
        repo_info = RepoInfo(
            path=repo_path,
            name=name,
            has_claude_md=has_claude_md,
            has_uncommitted_changes=has_uncommitted_changes,
            has_untracked_files=has_untracked_files,
            untracked_count=untracked_count,
            has_remote=has_remote,
            last_commit_date=last_commit_date,
            days_since_last_commit=days_since_last_commit,
            total_commits=total_commits,
            category="",
            reason="",
            suggested_command=""  # Initialize suggested_command
        )
        # Categorize the repository
        category, reason = self.categorize_repository(repo_info)
        repo_info.category = category
        repo_info.reason = reason
        # Generate suggested command after categorization
        repo_info.suggested_command = self.generate_suggested_command(repo_info)
        return repo_info

    def analyze_all_repositories(self, quiet: bool = False) -> None:
        """Analyze all repositories in the root directory."""
        if not quiet:
            print(f"Analyzing repositories in: {self.root_dir}")
            print("=" * 60)
        git_repos = self.find_git_repositories()
        if not quiet:
            print(f"Found {len(git_repos)} git repositories")
            print()
        for repo_path in git_repos:
            repo_info = self.analyze_repository(repo_path)
            self.repos.append(repo_info)
            self.categories[repo_info.category].append(repo_info)
            if not quiet:
                print(f"{repo_info.category:8} | {repo_info.name:40} | {repo_info.reason}")

    def print_summary(self) -> None:
        """Print a summary of the analysis results."""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for category in ["ACTIVE", "ANCIENT", "UNSURE"]:
            repos = self.categories[category]
            print(f"\n{category} REPOSITORIES ({len(repos)} repos):")
            if category == "ACTIVE":
                print("Keep these - they have recent activity or are being worked on")
            elif category == "ANCIENT":
                print("Safe to delete locally - old and inactive")
            elif category == "UNSURE":
                print("Need manual review before deletion")
            for repo in sorted(repos, key=lambda r: r.name):
                print(f"  • {repo.name:40} | {repo.reason}")
        print(f"\nTOTAL: {len(self.repos)} repositories analyzed")
        print(f"  - ACTIVE:  {len(self.categories['ACTIVE']):3} (keep)")
        print(f"  - ANCIENT: {len(self.categories['ANCIENT']):3} (can delete)")
        print(f"  - UNSURE:  {len(self.categories['UNSURE']):3} (review)")

    def save_detailed_report(self, output_file: FilePath, quiet: bool = False) -> None:
        """Save a detailed report to a file."""
        with output_file.open('w') as f:
            f.write("# Repository Analysis Report\n\n")
            f.write(f"Analysis performed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Root directory: {self.root_dir}\n")
            f.write(f"Total repositories: {len(self.repos)}\n\n")
            for category in ["ACTIVE", "ANCIENT", "UNSURE"]:
                repos = self.categories[category]
                f.write(f"## {category} REPOSITORIES ({len(repos)} repos)\n\n")
                for repo in sorted(repos, key=lambda r: r.name):
                    f.write(f"### {repo.name}\n")
                    f.write(f"- **Path**: `{repo.path}`\n")
                    f.write(f"- **Category**: {repo.category}\n")
                    f.write(f"- **Reason**: {repo.reason}\n")
                    f.write(f"- **Total commits**: {repo.total_commits}\n")
                    if repo.days_since_last_commit is not None:
                        f.write(f"- **Days since last commit**: {repo.days_since_last_commit}\n")
                    f.write(f"- **Has CLAUDE.md**: {repo.has_claude_md}\n")
                    f.write(f"- **Has uncommitted changes**: {repo.has_uncommitted_changes}\n")
                    f.write(f"- **Has remote configured**: {repo.has_remote}\n")
                    f.write(f"- **Untracked files**: {repo.untracked_count}\n")
                    f.write("\n")
        if not quiet:
            print(f"\nDetailed report saved to: {output_file}")

    def save_categorized_scripts(self, quiet: bool = False) -> None:
        """Save multiple bash scripts, one for each command type."""
        script_contents = defaultdict(list)
        generated_script_names = []
        command_to_script_name = {
            "rm -rf": "rm.sh",
            "cd ... && git status": "cd-status.sh",
            "cd ... && ls": "cd-ls.sh",
            "cd ... && git pull --rebase": "cd-pull.sh",
        }
        for repo in self.repos:
            command_type = ""
            if repo.suggested_command.startswith("rm -rf"):
                command_type = "rm -rf"
            elif "git status" in repo.suggested_command:
                command_type = "cd ... && git status"
            elif "git pull --rebase" in repo.suggested_command:
                command_type = "cd ... && git pull --rebase"
            elif "ls" in repo.suggested_command:
                command_type = "cd ... && ls"
            if command_type:
                script_name = command_to_script_name.get(command_type)
                if script_name:
                    script_contents[script_name].append(f"# {repo.name} ({repo.reason})\n{repo.suggested_command}\n")
        for script_name, commands in script_contents.items():
            with open(script_name, 'w') as f:
                f.write("#!/bin/bash\n\n")
                f.write(f"# This script was generated by clones.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("# Review this script carefully before executing!\n\n")
                for cmd in commands:
                    f.write(cmd)
            os.chmod(script_name, 0o755)
            generated_script_names.append(script_name)
            if not quiet:
                print(f"{script_name}")
        if quiet and generated_script_names:
            print("Generated scripts:")
            for name in generated_script_names:
                print(name)


def parse_args() -> arguments.AgumentsNameSpace:
    parser = arguments.parse(
        description="Analyze git repository clones and categorize by activity level",
        usage=dedent("""\
            Usage:
              %(prog)s                    # Analyze current directory
              %(prog)s ~/projects         # Analyze specific directory
              %(prog)s --report repos.md  # Save detailed report
              %(prog)s --scripts          # Generate multiple scripts
        """),
    )
    parser.positional('root_dir', nargs='?', default='~/jalanb/',
                      help='Root directory to analyze (default: ~/jalanb/)')
    parser.string('r', 'report', help='Save detailed report to specified file')
    parser.boolean('s', 'scripts', help='Generate multiple scripts with suggested actions')
    parser.boolean('q', 'quiet', help='Only show generated script filenames')
    args = parser.parse()
    path_to_root = path(args.root_dir)
    if not path_to_root.isdir():
        raise ValueError(f"Error: {root_dir} is not a directory")
    args.root_dir = path_to_root


def main() -> int:
    args = parse_args()
    analyzer = RepositoryAnalyzer(root_dir)
    analyzer.analyze_all_repositories(quiet=args.quiet)
    if not args.quiet:
        analyzer.print_summary()
    if args.report:
        report_file = path(args.report)
        analyzer.save_detailed_report(report_file, quiet=args.quiet)
    if args.scripts:
        analyzer.save_categorized_scripts(quiet=args.quiet)
    return os.EX_OK


if __name__ == '__main__':
    sys.exit(main())
