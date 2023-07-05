from setuptools import setup, find_packages

setup(
    name='gptfunctionutil',
    version='0.1',
    license='MIT',
    author='Crosswave Omega',
    author_email='xtream2pro@gmail.com',
    description='A simple package for the purpose of providing a set of utilities that make it easier to invoke python methods and discord.py commands with the OpenAI Function Calling API',
    keywords='discord.py, OpenAI, Function Calling API',
    url='',
    packages=find_packages(exclude=['tests', 'docs']),
    python_requires='>=3.10',
    install_requires=[
        'discord.py'
    ]
)
