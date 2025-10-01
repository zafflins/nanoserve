import setuptools

version = [0, 1, 0]

setuptools.setup(
    name='nanoserve',
    version=f"{version[0]}.{version[1]}.{version[2]}-7",
    description='A small RPC network programming lib',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Izaiyah Stokes',
    author_email='zafflins@gmail.com',
    url='https://github.com/zafflins/nanoserve',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ], include_package_data=True
)
