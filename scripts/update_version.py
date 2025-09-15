#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_git_commit_date() -> datetime | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_date_str = result.stdout.strip()
        # Parse git date format: "2025-09-15 10:30:45 -0300"
        date_part = commit_date_str.split()[0]
        return datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=UTC)
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return None


def get_current_version() -> str | None:
    init_file = Path("src/korone/__init__.py")
    if not init_file.exists():
        return None

    content = init_file.read_text(encoding="utf-8")
    match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
    return match.group(1) if match else None


def update_version_in_file(new_version: str) -> bool:
    init_file = Path("src/korone/__init__.py")
    if not init_file.exists():
        print(f"Error: {init_file} not found")
        return False

    content = init_file.read_text(encoding="utf-8")
    pattern = r'(__version__ = ["\'])([^"\']+)(["\'])'

    def replace_version(match):
        return f"{match.group(1)}{new_version}{match.group(3)}"

    new_content = re.sub(pattern, replace_version, content)

    if new_content == content:
        print("Warning: Version pattern not found in __init__.py")
        return False

    init_file.write_text(new_content, encoding="utf-8")
    print(f"Updated version to {new_version}")
    return True


def format_date_version(date: datetime) -> str:
    return date.strftime("%Y.%m.%d")


def main() -> int:
    parser = argparse.ArgumentParser(description="Update version based on date")
    parser.add_argument(
        "--use-commit-date",
        action="store_true",
        help="Use the date of the latest commit instead of current date",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if version matches date, don't update",
    )
    parser.add_argument(
        "--force-current-date", action="store_true", help="Force update to current date"
    )

    args = parser.parse_args()

    # Determine which date to use
    if args.use_commit_date:
        target_date = get_git_commit_date()
        if target_date is None:
            print("Error: Could not get commit date")
            return 1
        print(f"Using commit date: {target_date.strftime('%Y-%m-%d')}")
    else:
        target_date = datetime.now(tz=UTC)
        print(f"Using current date: {target_date.strftime('%Y-%m-%d')}")

    new_version = format_date_version(target_date)
    current_version = get_current_version()

    if current_version is None:
        print("Error: Could not read current version")
        return 1

    print(f"Current version: {current_version}")
    print(f"Target version: {new_version}")

    if args.check_only:
        if current_version == new_version:
            print("✓ Version is up to date")
            return 0

        print("✗ Version is outdated")
        return 1

    if current_version == new_version and not args.force_current_date:
        print("Version is already up to date")
        return 0

    if update_version_in_file(new_version):
        print("✓ Version updated successfully")
        return 0

    print("✗ Failed to update version")
    return 1


if __name__ == "__main__":
    sys.exit(main())
