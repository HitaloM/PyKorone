#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import sys

from update_version import format_date_version, get_current_version, get_git_commit_date


def validate_version_against_commit() -> bool:
    current_version = get_current_version()
    if current_version is None:
        print("Error: Could not read current version from __init__.py")
        return False

    commit_date = get_git_commit_date()
    if commit_date is None:
        print("Error: Could not get last commit date")
        return False

    expected_version = format_date_version(commit_date)

    print(f"Current version: {current_version}")
    print(f"Last commit date: {commit_date.strftime('%Y-%m-%d')}")
    print(f"Expected version: {expected_version}")

    if current_version == expected_version:
        print("✓ Version matches last commit date")
        return True

    print("✗ Version does not match last commit date")
    print(f"  Expected: {expected_version}")
    print(f"  Found:    {current_version}")
    return False


def main() -> int:
    if not validate_version_against_commit():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
