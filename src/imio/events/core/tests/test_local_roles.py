# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import transaction
import unittest


class TestLocalRoles(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="Entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            title="Agenda",
        )
        self.folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            title="Folder",
        )
        self.event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            title="Event",
        )

    def test_local_manager_in_sharing(self):
        transaction.commit()
        browser = Browser(self.layer["app"])
        browser.addHeader(
            "Authorization",
            "Basic %s:%s"
            % (
                TEST_USER_NAME,
                TEST_USER_PASSWORD,
            ),
        )
        browser.open("{}/@@sharing".format(self.entity.absolute_url()))
        content = browser.contents
        self.assertIn("Can manage locally", content)

        browser.open("{}/@@sharing".format(self.agenda.absolute_url()))
        content = browser.contents
        self.assertNotIn("Can manage locally", content)

        browser.open("{}/@@sharing".format(self.folder.absolute_url()))
        content = browser.contents
        self.assertNotIn("Can manage locally", content)

        browser.open("{}/@@sharing".format(self.event.absolute_url()))
        content = browser.contents
        self.assertNotIn("Can manage locally", content)
