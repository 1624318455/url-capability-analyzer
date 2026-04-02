from setuptools import setup, find_packages

setup(
    name="url-capability-analyzer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "scikit-learn>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "analyze-url=scripts.analyze:main",
        ],
    },
    author="Your Name",
    description="Analyze MCP/Skill URLs against local capabilities",
    license="MIT",
)