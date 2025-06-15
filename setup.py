from setuptools import setup, find_packages

setup(
    name="BookLLM",
    version="1.0.0",
    packages=find_packages(include=['BookLLM', 'BookLLM.*']),
    python_requires=">=3.10",
    install_requires=[
        # Dependencies will be installed via requirements.txt
    ],
    package_data={
        'BookLLM': ['config.yaml'],
    },
)