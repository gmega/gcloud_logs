from setuptools import setup

setup(
    name='gcloud_logs',
    version='0.1',
    description='Pull and tail logs from Stackdriver into your console',
    author='Giuliano Mega',
    author_email='giuliano@playax.com',
    install_requires=[
        'colorama >= 0.4.4',
        'dateutils >= 0.6.12',
        'google-cloud-core >= 1.6.0',
        'google-cloud-logging >= 2.2.0'
    ],
    py_modules=['gcloud_logs'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    license='MIT',
    entry_points={
        'console_scripts': ['gcloud-logs=gcloud_logs:main']
    }
)