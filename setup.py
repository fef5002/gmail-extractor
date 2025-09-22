from setuptools import setup, find_packages

setup(
    name="gmail-extractor",
    version="1.0.0",
    author="Gmail Extractor",
    description="A tool to extract Gmail emails from multiple accounts and export them as PDFs to Google Drive",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client==2.108.0",
        "google-auth-httplib2==0.1.1",
        "google-auth-oauthlib==1.1.0",
        "reportlab==4.0.4",
        "python-dateutil==2.8.2",
        "click==8.1.7",
        "pydrive2==1.17.0",
        "email-to==0.1.0",
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3",
    ],
    entry_points={
        "console_scripts": [
            "gmail-extractor=gmail_extractor.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)