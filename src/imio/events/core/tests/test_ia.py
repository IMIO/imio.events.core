# -*- coding: utf-8 -*-

from imio.events.core.ia.browser.views import ProcessCategorizeContentView
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import patch

import unittest


class TestProcessCategorizeContentView(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", title="Entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", title="Agenda"
        )
        self.folder = api.content.create(
            container=self.agenda, type="imio.events.Folder", title="Folder"
        )

    def test_view_registered_on_event_containers(self):
        # ++add++imio.events.Event posts to its container
        for container in (self.agenda, self.folder):
            view = api.content.get_view(
                "ProcessCategorizeContent", container, self.request
            )
            self.assertIsInstance(view, ProcessCategorizeContentView)

    def test_process_public_cible_on_container(self):
        view = ProcessCategorizeContentView(self.agenda, self.request)
        with patch.object(view, "_ask_categorization_to_ia", return_value={}):
            self.assertEqual(view._process_public_cible("text", {}), "")
