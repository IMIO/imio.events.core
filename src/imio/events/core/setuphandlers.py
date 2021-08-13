# -*- coding: utf-8 -*-

from Products.CMFPlone.interfaces import INonInstallable
from plone import api
from zope.interface import implementer
import os


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "imio.events.core:uninstall",
        ]


def post_install(context):
    """Post install script"""
    portal = api.portal.get()
    default_entity = api.content.create(
        type="imio.events.Entity", title="Imio", container=portal
    )
    faceted_config = "/faceted/config/events.xml"
    # Create global faceted agenda
    faceted = api.content.create(
        type="imio.events.Agenda", title="Agenda", container=default_entity
    )
    subtyper = faceted.restrictedTraverse("@@faceted_subtyper")
    subtyper.enable()
    with open(os.path.dirname(__file__) + faceted_config, "rb") as faceted_config:
        faceted.unrestrictedTraverse("@@faceted_exportimport").import_xml(
            import_file=faceted_config
        )


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
