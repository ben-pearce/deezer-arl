from setuptools import setup, find_packages

setup(
    name='deezer-arl',
    version='1.0',
    description='Deezer ARL Scraper',
    author='Ben Pearce',
    author_email='me@benpearce.io',
    license='MIT',
    url='https://www.github.com/ben-pearce/deezer-arl/',
    packages=find_packages(include=['deezer_arl', 'deezer_arl.*']),
    install_requires=[
        'telethon==1.34.0', 
        'aiohttp==3.9.3', 
        'deezer-py==1.3.7'
    ]
)
