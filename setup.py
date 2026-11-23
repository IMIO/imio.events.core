# -*- coding: utf-8 -*-
"""Installer for the imio.events.core package."""

from setuptools import setup

long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="imio.events.core",
    version="2.0.1.dev0",
    description="Core product for iMio events website",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="iMio",
    author_email="christophe.boulanger@imio.be",
    url="https://github.com/collective/imio.events.core",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/imio.events.core",
        "Source": "https://github.com/collective/imio.events.core",
        "Tracker": "https://github.com/collective/imio.events.core/issues",
        # 'Documentation': 'https://imio.events.core.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=[
        "embeddify",
        "z3c.jbot",
        "plone.api>=1.8.4",
        "plone.gallery",
        "plone.restapi",
        "plone.app.dexterity",
        "plone.app.discussion",
        "plone.app.imagecropping",
        "collective.geolocationbehavior",
        "collective.taxonomy",
        "collective.z3cform.datagridfield",
        "eea.facetednavigation",
        "imio.smartweb.common",
        "imio.smartweb.locales",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.testing>=5.0.0",
            "plone.app.contenttypes",
            "plone.app.robotframework[debug]",
            "mock",
            "freezegun",
        ],
    },
    entry_points="""""",
)
