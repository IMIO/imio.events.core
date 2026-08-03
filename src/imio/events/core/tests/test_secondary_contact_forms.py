# -*- coding: utf-8 -*-

from imio.events.core.contents.secondary_contact.forms import (
    SecondaryContactCustomAddForm,
)
from imio.events.core.contents.secondary_contact.forms import (
    SecondaryContactCustomEditForm,
)
from imio.events.core.contents.secondary_contact.forms import SecondaryContactGridMixin
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.edit import DefaultEditForm
from unittest import mock

import unittest

DIRECTORY_PAYLOAD = {
    "items": [
        {
            "UID": "uid-1",
            "title": "Service culture",
            "phones": [{"label": "Accueil", "type": "work", "number": "081 12 34 56"}],
            "mails": [
                {"label": "", "type": "work", "mail_address": "culture@ville.be"}
            ],
            "urls": [{"type": "website", "url": "https://ville.be"}],
        }
    ]
}


class TestSecondaryContactFormClasses(unittest.TestCase):
    """Class-level guards that need no Plone site."""

    def test_mixin_reads_the_single_valued_field(self):
        self.assertEqual(
            "related_contact", SecondaryContactGridMixin.contact_uids_field
        )

    def test_add_form_portal_type(self):
        self.assertEqual(
            "imio.events.SecondaryContact", SecondaryContactCustomAddForm.portal_type
        )

    def test_add_form_keeps_the_base_buttons(self):
        # The failure mode this guards: without copying `buttons` before
        # @buttonAndHandler runs, the decorator creates a fresh empty manager
        # and the form silently loses Save and Cancel.
        self.assertEqual(
            ["save", "cancel", "load_contact_informations"],
            list(SecondaryContactCustomAddForm.buttons),
        )

    def test_edit_form_keeps_the_base_buttons(self):
        self.assertEqual(
            ["save", "cancel", "load_contact_informations"],
            list(SecondaryContactCustomEditForm.buttons),
        )

    def test_the_managers_are_copies_not_the_base_objects(self):
        # Same reasoning for `handlers`, whose loss is more silent: Save would
        # re-render the form without saving anything.
        self.assertIsNot(SecondaryContactCustomAddForm.buttons, DefaultAddForm.buttons)
        self.assertIsNot(
            SecondaryContactCustomAddForm.handlers, DefaultAddForm.handlers
        )
        self.assertIsNot(
            SecondaryContactCustomEditForm.buttons, DefaultEditForm.buttons
        )
        self.assertIsNot(
            SecondaryContactCustomEditForm.handlers, DefaultEditForm.handlers
        )


class TestSecondaryContactGridReload(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal, type="imio.events.Entity", id="entity"
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", id="agenda"
        )
        self.event = api.content.create(
            container=self.agenda, type="imio.events.Event", id="event"
        )
        self.contact = api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id="contact-1",
        )

    def _form(self, form_data):
        self.request.form.clear()
        self.request.form.update(form_data)
        return SecondaryContactCustomEditForm(self.contact, self.request)

    def test_pressing_load_fills_the_grids_from_the_directory(self):
        form = self._form({"form.widgets.related_contact": "uid-1"})
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        written = self.request.form
        self.assertEqual("1", written["form.widgets.phones_display.count"])
        self.assertEqual(
            "081 12 34 56", written["form.widgets.phones_display.0.widgets.number"]
        )
        self.assertEqual(
            "Service culture",
            written["form.widgets.phones_display.0.widgets.contact_title"],
        )
        self.assertEqual(
            "uid-1", written["form.widgets.phones_display.0.widgets.contact_uid"]
        )
        self.assertEqual("1", written["form.widgets.mails_display.count"])
        self.assertEqual(
            "culture@ville.be",
            written["form.widgets.mails_display.0.widgets.mail_address"],
        )
        self.assertEqual("1", written["form.widgets.urls_display.count"])
        self.assertEqual(
            "https://ville.be", written["form.widgets.urls_display.0.widgets.url"]
        )

    def test_the_raw_type_token_is_written_alongside_the_translated_label(self):
        form = self._form({"form.widgets.related_contact": "uid-1"})
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        written = self.request.form
        self.assertEqual(
            "work", written["form.widgets.phones_display.0.widgets.type_token"]
        )
        self.assertNotEqual(
            "work", written["form.widgets.phones_display.0.widgets.type"]
        )

    def test_every_row_defaults_to_all_columns_visible(self):
        form = self._form({"form.widgets.related_contact": "uid-1"})
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        self.assertEqual(
            ["label", "type", "number"],
            self.request.form["form.widgets.phones_display.0.widgets.visible_columns"],
        )

    def test_reloading_preserves_a_recorded_preference(self):
        form = self._form(
            {
                "form.widgets.related_contact": "uid-1",
                "form.widgets.phones_display.0.widgets.contact_uid": "uid-1",
                "form.widgets.phones_display.0.widgets.number": "081 12 34 56",
                "form.widgets.phones_display.0.widgets.visible_columns": ["number"],
            }
        )
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        self.assertEqual(
            ["number"],
            self.request.form["form.widgets.phones_display.0.widgets.visible_columns"],
        )

    def test_reloading_preserves_an_explicitly_hidden_row(self):
        # Nothing submitted for the checkbox group of a RENDERED row means
        # "everything unchecked", which must survive the reload as an empty list.
        form = self._form(
            {
                "form.widgets.related_contact": "uid-1",
                "form.widgets.phones_display.0.widgets.contact_uid": "uid-1",
                "form.widgets.phones_display.0.widgets.number": "081 12 34 56",
            }
        )
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        self.assertEqual(
            [],
            self.request.form["form.widgets.phones_display.0.widgets.visible_columns"],
        )

    def test_pressing_load_without_a_contact_empties_the_grids(self):
        form = self._form({})
        form._reload_display_grids()
        self.assertEqual("0", self.request.form["form.widgets.phones_display.count"])
        self.assertEqual("0", self.request.form["form.widgets.mails_display.count"])
        self.assertEqual("0", self.request.form["form.widgets.urls_display.count"])

    def test_a_directory_failure_leaves_the_request_untouched(self):
        # Rewriting the grids on a failed fetch would empty them and destroy
        # every recorded visible_columns preference on the next save.
        form = self._form({"form.widgets.related_contact": "uid-1"})
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json", return_value=None
        ):
            form._reload_display_grids()
        self.assertNotIn("form.widgets.phones_display.count", self.request.form)

    def test_the_multi_valued_field_name_is_not_read(self):
        # The section's field name must not leak into this type.
        form = self._form({"form.widgets.related_contacts": "uid-1"})
        with mock.patch(
            "imio.smartweb.common.contact.directory.get_json",
            return_value=DIRECTORY_PAYLOAD,
        ):
            form._reload_display_grids()
        self.assertEqual("0", self.request.form["form.widgets.phones_display.count"])
