# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING  # noqa: E501
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that imio.events.core is properly installed."""

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if imio.events.core is installed."""
        self.assertTrue(self.installer.isProductInstalled("imio.events.core"))

    def test_browserlayer(self):
        """Test that IImioEventsCoreLayer is registered."""
        from imio.events.core.interfaces import IImioEventsCoreLayer
        from plone.browserlayer import utils

        self.assertIn(IImioEventsCoreLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstallProducts(["imio.events.core"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if imio.events.core is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled("imio.events.core"))

    def test_browserlayer_removed(self):
        """Test that IImioEventsCoreLayer is removed."""
        from imio.events.core.interfaces import IImioEventsCoreLayer
        from plone.browserlayer import utils

        self.assertNotIn(IImioEventsCoreLayer, utils.registered_layers())
