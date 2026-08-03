# -*- coding: utf-8 -*-

from imio.events.core.contents.secondary_contact.serializer import (
    get_secondary_contacts,
)
from imio.events.core.contents.secondary_contact.serializer import kept_rows
from imio.events.core.contents.secondary_contact.serializer import (
    serialize_secondary_contact,
)
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


def phone_row(number, visible_columns, label="Accueil", token="work"):
    """A stored phones_display row, as build_display_rows would have written it."""
    return {
        "contact_uid": "uid-1",
        "contact_title": "Service culture",
        "type_token": token,
        "label": label,
        "type": "Telephone de travail",
        "number": number,
        "visible_columns": visible_columns,
    }


def mail_row(mail_address, visible_columns, token="work"):
    return {
        "contact_uid": "uid-1",
        "contact_title": "Service culture",
        "type_token": token,
        "label": "",
        "type": "Email de travail",
        "mail_address": mail_address,
        "visible_columns": visible_columns,
    }


class _EventFixture(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
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

    def _contact(self, contact_id="contact-1"):
        return api.content.create(
            container=self.event,
            type="imio.events.SecondaryContact",
            id=contact_id,
        )


class TestKeptRows(_EventFixture):
    def test_no_stored_rows_gives_no_rows(self):
        self.assertEqual([], kept_rows(self._contact(), "phones"))

    def test_none_visible_columns_yields_every_column(self):
        # "no preference recorded" -- the row goes out complete.
        contact = self._contact()
        contact.phones_display = [phone_row("081", None)]
        self.assertEqual(
            [{"label": "Accueil", "type": "work", "number": "081"}],
            kept_rows(contact, "phones"),
        )

    def test_empty_visible_columns_drops_the_row(self):
        # "explicitly hidden" -- never confused with the None case above.
        contact = self._contact()
        contact.phones_display = [phone_row("081", [])]
        self.assertEqual([], kept_rows(contact, "phones"))

    def test_only_the_retained_columns_are_emitted(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["number"])]
        self.assertEqual([{"number": "081"}], kept_rows(contact, "phones"))

    def test_the_type_column_is_emitted_as_the_raw_token(self):
        # Not the translated label: the consuming site translates it itself.
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["type"], token="cell")]
        self.assertEqual([{"type": "cell"}], kept_rows(contact, "phones"))

    def test_columns_are_emitted_in_the_canonical_order(self):
        # The stored order is the editor's checkbox order and must not leak.
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["number", "label", "type"])]
        self.assertEqual(
            ["label", "type", "number"], list(kept_rows(contact, "phones")[0])
        )

    def test_unknown_columns_are_ignored(self):
        contact = self._contact()
        contact.phones_display = [phone_row("081", ["number", "bogus"])]
        self.assertEqual([{"number": "081"}], kept_rows(contact, "phones"))

    def test_a_row_without_its_key_column_is_dropped(self):
        contact = self._contact()
        contact.phones_display = [phone_row("", None)]
        self.assertEqual([], kept_rows(contact, "phones"))

    def test_a_missing_value_becomes_an_empty_string(self):
        contact = self._contact()
        row = phone_row("081", None)
        del row["label"]
        contact.phones_display = [row]
        self.assertEqual("", kept_rows(contact, "phones")[0]["label"])

    def test_several_rows_keep_their_order(self):
        contact = self._contact()
        contact.phones_display = [
            phone_row("081", ["number"]),
            phone_row("082", ["number"]),
        ]
        self.assertEqual(
            ["081", "082"], [row["number"] for row in kept_rows(contact, "phones")]
        )

    def test_a_hidden_row_between_two_kept_ones_is_dropped(self):
        contact = self._contact()
        contact.phones_display = [
            phone_row("081", ["number"]),
            phone_row("082", []),
            phone_row("083", ["number"]),
        ]
        self.assertEqual(
            ["081", "083"], [row["number"] for row in kept_rows(contact, "phones")]
        )

    def test_the_mails_kind_uses_its_own_key_and_columns(self):
        contact = self._contact()
        contact.mails_display = [mail_row("a@b.be", ["mail_address"])]
        self.assertEqual([{"mail_address": "a@b.be"}], kept_rows(contact, "mails"))


class TestSerializeSecondaryContact(_EventFixture):
    def test_the_full_shape(self):
        contact = self._contact()
        contact.title = "Reservations"
        contact.related_contact = "uid-1"
        contact.phones_display = [phone_row("081", ["number"])]
        contact.mails_display = [mail_row("resa@ville.be", ["mail_address"])]
        contact.urls_display = []
        self.assertEqual(
            {
                "uid": "uid-1",
                "title": "Reservations",
                "phones": [{"number": "081"}],
                "mails": [{"mail_address": "resa@ville.be"}],
                "urls": [],
            },
            serialize_secondary_contact(contact),
        )

    def test_a_missing_title_becomes_an_empty_string(self):
        contact = self._contact()
        contact.related_contact = "uid-1"
        self.assertEqual("", serialize_secondary_contact(contact)["title"])

    def test_the_three_kinds_are_always_present(self):
        contact = self._contact()
        contact.related_contact = "uid-1"
        result = serialize_secondary_contact(contact)
        self.assertEqual([], result["phones"])
        self.assertEqual([], result["mails"])
        self.assertEqual([], result["urls"])

    def test_a_contact_without_a_related_contact_is_not_serialized(self):
        # related_contact is required, so this can only be legacy data; the
        # payload must never carry an entry with a null uid.
        self.assertIsNone(serialize_secondary_contact(self._contact()))


class TestGetSecondaryContacts(_EventFixture):
    def test_an_event_without_children_gives_an_empty_list(self):
        self.assertEqual([], get_secondary_contacts(self.event))

    def test_children_are_returned_in_folder_order(self):
        for index, uid in enumerate(["uid-a", "uid-b", "uid-c"], start=1):
            contact = self._contact("contact-{}".format(index))
            contact.related_contact = uid
        self.assertEqual(
            ["uid-a", "uid-b", "uid-c"],
            [item["uid"] for item in get_secondary_contacts(self.event)],
        )

    def test_other_child_types_are_ignored(self):
        api.content.create(container=self.event, type="Image", id="an-image")
        self.assertEqual([], get_secondary_contacts(self.event))

    def test_a_child_without_a_related_contact_is_skipped(self):
        self._contact()
        self.assertEqual([], get_secondary_contacts(self.event))

    def test_a_usable_child_survives_an_unusable_sibling(self):
        self._contact("contact-1")
        usable = self._contact("contact-2")
        usable.related_contact = "uid-b"
        self.assertEqual(
            ["uid-b"], [item["uid"] for item in get_secondary_contacts(self.event)]
        )
