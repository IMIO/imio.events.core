# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles, TEST_USER_ID
from Products.CMFPlone.utils import get_installer
import unittest


class TestSetup(unittest.TestCase):
    """Test that imio.events.core is properly installed."""

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])

    def test_product_installed(self):
        """Test if imio.events.core is installed."""
        self.assertTrue(self.installer.is_product_installed("imio.events.core"))

    def test_browserlayer(self):
        """Test that IImioEventsCoreLayer is registered."""
        from imio.events.core.interfaces import IImioEventsCoreLayer
        from plone.browserlayer import utils

        self.assertIn(IImioEventsCoreLayer, utils.registered_layers())

    def test_profile_version(self):
        setup = api.portal.get_tool("portal_setup")
        self.assertEqual(
            "1027", setup.getLastVersionForProfile("imio.events.core:default")[0]
        )

    def test_upgrade_to_1027_is_registered(self):
        setup = api.portal.get_tool("portal_setup")
        upgrades = setup.listUpgrades("imio.events.core:default", show_old=True)
        destinations = []
        for entry in upgrades:
            steps = entry if isinstance(entry, list) else [entry]
            destinations.extend(step["sdest"] for step in steps)
        self.assertIn("1027", destinations)


class TestUninstall(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.installer = get_installer(self.portal, self.layer["request"])
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstall_product("imio.events.core")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if imio.events.core is cleanly uninstalled."""
        self.assertFalse(self.installer.is_product_installed("imio.events.core"))

    def test_browserlayer_removed(self):
        """Test that IImioEventsCoreLayer is removed."""
        from imio.events.core.interfaces import IImioEventsCoreLayer
        from plone.browserlayer import utils

        self.assertNotIn(IImioEventsCoreLayer, utils.registered_layers())
