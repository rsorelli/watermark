from setuptools import setup, find_packages

setup(
    name="watermark",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "flask",
        "flask-limiter",
        "flask-caching",
        "pillow",
        "python-magic",
        "apscheduler",
    ],
    python_requires=">=3.8",
)