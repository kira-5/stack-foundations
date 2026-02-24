# setup.py

from setuptools import find_packages, setup

setup(
    name="fastapi_core_base",
    version="2.1.12",
    description="FastAPI Core Base Project with Shared Infrastructure",
    author="Your Name",
    # 1. Point to the 'src' directory
    package_dir={"": "src"},
    # 2. Automatically find all packages inside 'src'
    packages=find_packages(where="src", exclude=["tests", "*.tests"]),
    python_requires=">=3.12",
    include_package_data=True,
    zip_safe=False,
    # Optional: If you want to make the app runnable via 'fastapi-core' command
    entry_points={
        "console_scripts": [
            "run-app=app.main:run", 
        ],
    },
)