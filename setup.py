from setuptools import setup, find_packages

setup(
    name='mass_ldtk_loader',
    version='0.1.0',
    description='Mass loader for LDtk projects from image tilesets',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    py_modules=['mass_ldtk_loader'],
    python_requires='>=3.6',
    install_requires=[],  # Add dependencies here if needed
    entry_points={
        'console_scripts': [
            'mass_ldtk_loader=mass_ldtk_loader:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
)
