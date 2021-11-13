from setuptools import setup, find_packages

if __name__ == '__main__':
    setup(
        name='daxis_amm',
        version='0.0.1',
        description='Daxis Automatic Market Marker',
        author='William Harris',
        author_email='william.allen.harris@outlook.com',
        packages=find_packages(),  # include all packages under src
        install_requires=[],  # external packages as dependencies
        include_package_data=True
    )
