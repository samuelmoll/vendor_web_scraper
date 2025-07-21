#!/usr/bin/env python3
"""Test file for formatting."""

import os, sys


def test_function():
    """Test function with bad formatting."""
    if True:
        x = 1 + 2
        print(f"Result: {x}")


def another_function():
    """Another test function."""
    data = ["a", "b", "c"]
    return data


if __name__ == "__main__":
    test_function()
    print("Done")
