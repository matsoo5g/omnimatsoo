from setuptools import setup, find_packages


setup(
    name="omnimatsoo",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    extras_require={},
    tests_require=["pytest"],
    install_requires=["pyyaml", "bokeh", "flask", "boto3"],
    entry_points={
        "console_scripts": [
            "matsoogo = omnimatsoo.wsgi:start",
        ]
    },
)
