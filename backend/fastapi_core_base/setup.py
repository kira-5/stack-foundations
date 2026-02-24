# setup.py

from setuptools import find_packages, setup

setup(
    name="fastapi_core_base",
    version="2.1.12",
    description="FastAPI Core Base",
    # Why this is better:
    # 1. Names should use hyphens, not spaces
    # 2. Excludes 'tests' folder so it doesn't get installed as a global package
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    # This tells setuptools that the "root" package is in the current directory.
    # It allows you to import 'app' as a top-level package.
    package_dir={"": "."},
    python_requires=">=3.12",
    include_package_data=True,  # Includes files from MANIFEST.in
    zip_safe=False,  # Recommended for modern packages
)
