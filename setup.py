
from setuptools import setup, find_packages
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def main():
    setup(
        name='grony',
        version='0.2',
        description='An utility to schedule git-related actions using crontab expressions.',
        long_description=read('README.md'),
        long_description_content_type="text/markdown",
        keywords='git, automation, cron, crontab',

        author='Luis Medel',
        author_email='luis@luismedel.com',
        url='https://github.com/luismedel/grony',

        classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Console',
            'Intended Audience :: Developers',
            'Operating System :: Unix',
            'Topic :: Software Development :: Version Control',
            'Topic :: Software Development :: Version Control :: Git',
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: MIT License'
        ],

        package_dir={ '': 'src'},
        packages=find_packages('src'),
        include_package_data=True,
        install_requires=['click', 'tabulate', 'crontab'],
        entry_points={
            "console_scripts": [
                "grony=grony.main:main",
            ],
        },
    )

if __name__ == '__main__':
    main()
