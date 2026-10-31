"""Unit test verifying all required Docker configuration files exist."""

import os


def test_docker_files_exist():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    docker_compose = os.path.join(root_dir, "docker-compose.real.yml")
    backend_dockerfile = os.path.join(root_dir, "backend", "Dockerfile")
    frontend_dockerfile = os.path.join(root_dir, "frontend", "Dockerfile")
    env_real_example = os.path.join(root_dir, ".env.real.example")

    assert os.path.exists(docker_compose), f"Missing {docker_compose}"
    assert os.path.exists(backend_dockerfile), f"Missing {backend_dockerfile}"
    assert os.path.exists(frontend_dockerfile), f"Missing {frontend_dockerfile}"
    assert os.path.exists(env_real_example), f"Missing {env_real_example}"
