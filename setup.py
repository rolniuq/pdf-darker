from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="darker-pdf",
    version="0.1.0",
    author="PDF Editor Team",
    author_email="team@pdfeditor.dev",
    description="A comprehensive PDF editing tool with dark mode conversion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/darker-pdf",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "darker-pdf=src.pdf_editor.cli.main:cli",
            "pdf-editor=src.pdf_editor.cli.main:cli",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
        ],
        "ocr": ["pytesseract>=0.3.10"],
        "gui": ["PyQt5>=5.15.0"],
    },
)