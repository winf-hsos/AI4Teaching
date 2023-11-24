from setuptools import setup, find_packages

setup(
    name='ai4teaching',
    version='0.1',
    packages=find_packages(),
    description='API for useful AI tool in learning and teaching scenarios.',
    author='Nicolas Meseth',
    author_email='n.meseth@hs-osnabrueck.de',
    url='https://github.com/winf-hsos/AI4Teaching',
    install_requires=[
        'openai',
        'chromadb',
        'pytube',
        'moviepy',
        'streamlit',
        'colorama'
    ],
    license='CC BY-NC-SA 4.0'    
)