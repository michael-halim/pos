from setuptools import setup, find_packages

setup(
    name="pos-system",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'altgraph==0.17.4',
        'packaging==24.2',
        'pefile==2023.2.7',
        'pyinstaller==6.12.0',
        'pyinstaller-hooks-contrib==2025.1',
        'PyQt6==6.8.0',
        'PyQt6-Qt6==6.8.1',
        'PyQt6_sip==13.9.1',
        'pywin32-ctypes==0.2.3',
    ],
    package_data={
        '': ['ui/*.ui', 'db/*.db'],  # Include UI and database files
    },
    entry_points={
        'console_scripts': [
            'pos-system=main:main',  # Replace with your entry point
        ],
    },
    author="Your Name",
    description="POS System Application",
) 