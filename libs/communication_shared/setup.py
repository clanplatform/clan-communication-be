from setuptools import setup, find_packages

setup(
    name="communication_shared",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "redis[hiredis]>=5.0",
        "sqlalchemy>=2.0",
    ],
)
