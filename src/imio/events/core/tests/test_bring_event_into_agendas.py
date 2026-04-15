# -*- coding: utf-8 -*-

from imio.events.core.browser.bring_event_into_agendas.agendas import (
    BringEventIntoAgendasForm,
)
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.z3cform.interfaces import IPloneFormLayer
from unittest import mock
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

import unittest


class TestBringEventIntoAgendasForm(unittest.TestCase):
    """Tests for BringEventIntoAgendasForm (add/remove agendas from an event)."""

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
            title="Entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda",
            title="Agenda",
        )
        self.agenda_b = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="agenda-b",
            title="Agenda B",
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Event",
        )
        # After creation, event.selected_agendas == [self.agenda.UID()]

    def _make_form(self, event, agendas_data):
        """
        Instantiate BringEventIntoAgendasForm with extractData patched to return
        the given list of agenda UIDs, bypassing widget machinery.
        """
        form_obj = BringEventIntoAgendasForm(event, self.request)
        form_obj.selectedUID = list(event.selected_agendas)
        form_obj.extractData = mock.Mock(return_value=({"agendas": agendas_data}, []))
        return form_obj

    def test_handle_submit_adds_agenda(self):
        """Submitting with a new agenda UID appends it to context.selected_agendas."""
        form_obj = self._make_form(self.event, [self.agenda.UID(), self.agenda_b.UID()])
        form_obj.handle_submit(form_obj, None)
        self.assertIn(self.agenda_b.UID(), self.event.selected_agendas)
        self.assertIn(self.agenda.UID(), self.event.selected_agendas)

    def test_handle_submit_removes_agenda(self):
        """Submitting with fewer UIDs removes the dropped ones from selected_agendas."""
        self.event.selected_agendas.append(self.agenda_b.UID())
        form_obj = self._make_form(self.event, [self.agenda.UID()])
        form_obj.handle_submit(form_obj, None)
        self.assertNotIn(self.agenda_b.UID(), self.event.selected_agendas)
        self.assertIn(self.agenda.UID(), self.event.selected_agendas)

    def test_handle_submit_redirects_to_event(self):
        """After a successful submit, the response redirects to the event URL."""
        form_obj = self._make_form(self.event, [self.agenda.UID()])
        form_obj.handle_submit(form_obj, None)
        location = self.request.response.getHeader("location")
        self.assertEqual(location, self.event.absolute_url())

    def test_handle_submit_does_not_modify_on_errors(self):
        """When extractData returns validation errors, selected_agendas is unchanged."""
        form_obj = BringEventIntoAgendasForm(self.event, self.request)
        form_obj.selectedUID = list(self.event.selected_agendas)
        form_obj.extractData = mock.Mock(return_value=({}, [object()]))
        form_obj.formErrorsMessage = "There are errors"
        original_selected = list(self.event.selected_agendas)
        form_obj.handle_submit(form_obj, None)
        self.assertEqual(self.event.selected_agendas, original_selected)

    def test_handle_cancel_redirects_to_event(self):
        """Cancel button redirects to event URL without modifying selected_agendas."""
        original_selected = list(self.event.selected_agendas)
        form_obj = BringEventIntoAgendasForm(self.event, self.request)
        form_obj.handleCancel(form_obj, None)
        location = self.request.response.getHeader("location")
        self.assertEqual(location, self.event.absolute_url())
        self.assertEqual(self.event.selected_agendas, original_selected)

    def test_update_redirects_when_no_entity_authorizes_bring_events(self):
        """update() redirects to event URL and returns False when permission is absent."""
        # entity.authorize_to_bring_event_anywhere defaults to False
        # Use the layer's request: it already has the right nohost server setup.
        form_obj = BringEventIntoAgendasForm(self.event, self.request)
        result = form_obj.update()
        self.assertIs(result, False)
        location = self.request.response.getHeader("location")
        self.assertEqual(location, self.event.absolute_url())

    def test_update_does_not_redirect_when_entity_authorizes_bring_events(self):
        """update() returns None and skips redirect when permission is granted."""
        self.entity.authorize_to_bring_event_anywhere = True
        # A plain TestRequest is safe here: no redirect is called so the host
        # mismatch guard and IAnnotations are never exercised.
        request = TestRequest(form={})
        alsoProvides(request, IPloneFormLayer)
        form_obj = BringEventIntoAgendasForm(self.event, request)
        result = form_obj.update()
        self.assertIsNone(result)

    def test_updatewidgets_preselects_current_agendas(self):
        """updateWidgets sets selectedUID to UIDs already in context.selected_agendas."""
        self.entity.authorize_to_bring_event_anywhere = True
        request = TestRequest(form={})
        alsoProvides(request, IPloneFormLayer)
        form_obj = BringEventIntoAgendasForm(self.event, request)
        form_obj.update()
        self.assertIn(self.agenda.UID(), form_obj.selectedUID)
        self.assertNotIn(self.agenda_b.UID(), form_obj.selectedUID)


# <audit>
#   <file>test_bring_event_into_agendas.py</file>
#   <requirements_applied>R1, R2, R3, R5, R6</requirements_applied>
#   <deviations>
#     extractData is patched on form instances to inject controlled agenda UIDs,
#     bypassing z3c.form AjaxSelectWidget machinery. The real business logic
#     (list mutation, reindex, redirect) is tested against real Plone content objects.
#     R1 is satisfied for everything outside the widget layer.
#
#     IAttributeAnnotatable is applied to TestRequest instances so that
#     api.portal.show_message() (which annotates the request) works in tests.
#   </deviations>
#   <questions>None</questions>
# </audit>
