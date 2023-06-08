from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='mangodm',
      version='0.1',
      description='lite async ODM',
      long_description=readme(),
      classifiers=[
          'License :: MIT License',
          'Programming Language :: Python :: 3',
          'Topic :: ODM :: MongoDB',
      ],
      url='http://github.com/Exillite/mangodm',
      author='Flying Circus',
      author_email='alexander.rodionov.space',
      license='MIT',
      packages=['mangodm'],
      install_requires=[
          'pydantic>=1.10.9',
          'motor>=3.1.2',
      ],
      include_package_data=True,)
