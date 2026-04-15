# -*- coding: utf-8 -*-

from imio.events.core.browser.actions import DeleteActionView
from imio.events.core.browser.actions import DeleteConfirmationForm
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.interface import alsoProvides

import unittest


class TestDeleteConfirmationForm(unittest.TestCase):
    """Tests for DeleteConfirmationForm.items_to_delete (delete action in left menu)."""

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IImioEventsCoreLayer)
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda",
        )

    def test_items_to_delete_empty_agenda(self):
        """Empty agenda: items_to_delete returns 0, deletion is not blocked."""
        form = DeleteConfirmationForm(self.agenda, self.request)
        self.assertEqual(form.items_to_delete, 0)

    def test_items_to_delete_agenda_with_events(self):
        """Non-empty agenda: items_to_delete redirects to agenda URL and returns 0."""
        api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )
        form = DeleteConfirmationForm(self.agenda, self.request)
        result = form.items_to_delete
        self.assertEqual(result, 0)
        location = self.request.response.getHeader("location")
        self.assertEqual(location, self.agenda.absolute_url())

    def test_items_to_delete_empty_folder(self):
        """Empty folder: items_to_delete returns 0, deletion is not blocked."""
        folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="folder",
        )
        form = DeleteConfirmationForm(folder, self.request)
        self.assertEqual(form.items_to_delete, 0)

    def test_items_to_delete_folder_with_events(self):
        """Non-empty folder: items_to_delete redirects to folder URL and returns 0."""
        folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="folder",
        )
        api.content.create(
            container=folder,
            type="imio.events.Event",
            id="event",
        )
        form = DeleteConfirmationForm(folder, self.request)
        result = form.items_to_delete
        self.assertEqual(result, 0)
        location = self.request.response.getHeader("location")
        self.assertEqual(location, folder.absolute_url())


class TestDeleteActionView(unittest.TestCase):
    """Tests for DeleteActionView.action (trash icon in folder_contents view)."""

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        alsoProvides(self.request, IImioEventsCoreLayer)
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda",
        )

    def _make_view(self, context):
        view = DeleteActionView(context, self.request)
        view.errors = []
        return view

    def test_action_blocks_non_empty_agenda(self):
        """Action on agenda with events appends an error and does not delete it."""
        api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )
        view = self._make_view(self.entity)
        view.action(self.agenda)
        self.assertEqual(len(view.errors), 1)
        self.assertIn("agenda", self.entity.objectIds())

    def test_action_allows_empty_agenda(self):
        """Action on empty agenda calls super, resulting in deletion."""
        view = self._make_view(self.entity)
        view.action(self.agenda)
        self.assertEqual(len(view.errors), 0)
        self.assertNotIn("agenda", self.entity.objectIds())

    def test_action_blocks_non_empty_folder(self):
        """Action on folder with events appends an error and does not delete it."""
        folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="folder",
        )
        api.content.create(
            container=folder,
            type="imio.events.Event",
            id="event",
        )
        view = self._make_view(self.agenda)
        view.action(folder)
        self.assertEqual(len(view.errors), 1)
        self.assertIn("folder", self.agenda.objectIds())

    def test_action_allows_empty_folder(self):
        """Action on empty folder calls super, resulting in deletion."""
        folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="folder",
        )
        view = self._make_view(self.agenda)
        view.action(folder)
        self.assertEqual(len(view.errors), 0)
        self.assertNotIn("folder", self.agenda.objectIds())

    def test_action_allows_non_container_type(self):
        """Action on an event (neither Agenda nor Folder) calls super and deletes it."""
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )
        view = self._make_view(self.agenda)
        view.action(event)
        self.assertEqual(len(view.errors), 0)
        self.assertNotIn("event", self.agenda.objectIds())


# <audit>
#   <file>test_actions.py</file>
#   <requirements_applied>R1, R2, R3, R5, R6</requirements_applied>
#   <deviations>None</deviations>
#   <questions>None</questions>
# </audit>
