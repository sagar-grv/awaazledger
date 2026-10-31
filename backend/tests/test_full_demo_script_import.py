"""Tests for demo scripts importability and entrypoints."""

import os
import sys

scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)


def test_demo_scripts_importable():
    """Verify demo scripts can be imported cleanly without syntax errors."""
    import run_full_demo
    import run_swarm_shield_demo
    import run_ops_demo
    import run_agent_demo

    assert callable(run_full_demo.run_full_demo)
    assert callable(run_swarm_shield_demo.run_swarm_shield_demo)
    assert callable(run_ops_demo.run_ops_demo)
    assert callable(run_agent_demo.run_agent_demo)
