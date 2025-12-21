from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="apt",
    version="1.0.0",
    author="APT Contributors",
    author_email="apt@swattoolchain.com",
    description="APT - Allied Performance Testing: Multi-tool performance testing framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swattoolchain/apt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pytest>=7.4.0",
        "pytest-asyncio>=0.23.0",
        "pytest-xdist>=3.5.0",
        "pytest-html>=4.1.1",
        "playwright>=1.40.0",
        "aiohttp>=3.9.0",
        "pandas>=2.1.0",
        "numpy>=1.26.0",
        "jinja2>=3.1.2",
        "PyYAML>=6.0.1",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
        "allure": [
            "allure-pytest>=2.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "apt-perf=performance.cli:main",
        ],
    },
)
