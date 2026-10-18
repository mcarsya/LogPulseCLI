from setuptools import setup, find_packages

setup(
    name="logpulse",
    version="1.0.0",
    author="Enterprise Engineering Guild",
    description="Enterprise SOP Static Site Generator & Memory-Managed Log Audit Engine",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "jinja2>=3.1.2",
        "rich>=13.0.0",
        "markdown-it-py>=3.0.0",
        "PyYAML>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "logpulse=src.core.cli:main",
        ],
    },
)
