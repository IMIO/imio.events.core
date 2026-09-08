# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import json
import unittest


class TestSharedDirectoryResources(unittest.TestCase):
    """The proxy views and the autofill script now live in imio.smartweb.common.
    This package runs on a different Plone version than that package's own test
    suite, so it keeps its own smoke coverage of their registration."""

    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]

    def browser(self):
        browser = Browser(self.app)
        browser.addHeader(
            "Authorization",
            "Basic {}:{}".format(TEST_USER_NAME, TEST_USER_PASSWORD),
        )
        return browser

    def test_directory_contact_info_is_registered(self):
        # No uid: the view answers an empty JSON object without calling out.
        browser = self.browser()
        browser.open("{}/@@directory_contact_info".format(self.portal.absolute_url()))
        self.assertEqual(json.loads(browser.contents), {})

    def test_autofill_script_is_published(self):
        browser = self.browser()
        browser.open(
            "{}/++plone++imio.smartweb.common/"
            "directory_contact_autofill.js".format(self.portal.absolute_url())
        )
        # Served as a static resource, so browser.contents comes back as bytes
        # (unlike a rendered HTML page, which zope.testbrowser decodes to str).
        contents = browser.contents.decode("utf-8")
        self.assertIn("form-widgets-directory_linked_contact", contents)
