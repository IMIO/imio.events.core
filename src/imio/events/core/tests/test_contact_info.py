# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from imio.smartweb.common.config import DIRECTORY_URL
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from unittest.mock import MagicMock
from unittest.mock import patch
from zope.component import getMultiAdapter

import json
import unittest


# The two views proxy the remote directory through
# imio.smartweb.common.utils.get_json, so ``requests.get`` is the only thing
# mocked: get_json itself (status handling, JSON parsing) and the URLs the views
# build are exercised for real.
REQUESTS_GET = "imio.smartweb.common.utils.requests.get"


class DirectoryInfoTestCase(unittest.TestCase):
    """Shared fixture for both views of ``browser/contact_info.py``."""

    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.request.form.clear()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
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
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Event",
        )

    def make_view(self, context, name):
        return getMultiAdapter((context, self.request), name=name)

    def fake_response(self, payload, status_code=200):
        """Stand in for a ``requests`` response as get_json consumes it."""
        response = MagicMock()
        response.status_code = status_code
        response.text = json.dumps(payload)
        return response


class TestDirectoryContactInfoView(DirectoryInfoTestCase):
    def make_view(self, context=None):
        return super().make_view(
            context if context is not None else self.event,
            "directory_contact_info",
        )

    def contact_payload(self, **contact):
        """A directory @search result holding a single contact."""
        return {"items": [contact], "items_total": 1}

    def test_no_uid_returns_empty_json(self):
        with patch(REQUESTS_GET) as mock_get:
            result = json.loads(self.make_view()())
        self.assertEqual(result, {})
        # Without a uid there is nothing to look up: the directory is not called.
        mock_get.assert_not_called()

    def test_response_is_flagged_as_json(self):
        self.make_view()()
        self.assertEqual(
            self.request.response.getHeader("Content-Type"), "application/json"
        )

    def test_returns_contact_and_address_fields(self):
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(
            **{
                "@id": "https://annuaire.enwallonie.be/mons/contact-uid",
                "title": "Centre culturel",
                "street": "rue de Nimy",
                "number": "106",
                "complement": "boîte 2",
                "zipcode": "7000",
                "city": "Mons",
                "country": {"title": "Belgique", "token": "be"},
                "phones": [{"label": None, "number": "+3265000000", "type": "work"}],
                "mails": [
                    {"label": None, "mail_address": "info@ccmons.be", "type": "work"}
                ],
            }
        )
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(
            result,
            {
                "url": "https://annuaire.enwallonie.be/mons/contact-uid",
                "name": "Centre culturel",
                "email": "info@ccmons.be",
                "phone": "+3265000000",
                "street": "rue de Nimy",
                "number": "106",
                "complement": "boîte 2",
                "zipcode": "7000",
                "city": "Mons",
                "country": "be",
            },
        )

    def test_name_combines_title_and_subtitle(self):
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(title="Centre culturel", subtitle="Billetterie")
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result["name"], "Centre culturel: Billetterie")

    def test_name_ignores_empty_subtitle(self):
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(title="Centre culturel", subtitle=None)
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result["name"], "Centre culturel")

    def test_country_falls_back_to_title_without_token(self):
        # A serializer variant that only exposes the human-readable label.
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(country={"title": "Belgique"})
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result["country"], "Belgique")

    def test_country_token_is_kept_as_is_when_not_a_dict(self):
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(country="be")
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result["country"], "be")

    def test_unset_fields_are_normalised_to_empty_strings(self):
        # What the real directory returns for a contact whose address, phones
        # and mails were never filled in: every key present, every value None.
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(
            **{
                "@id": None,
                "title": "FEDER",
                "subtitle": None,
                "street": None,
                "number": None,
                "complement": None,
                "zipcode": None,
                "city": None,
                "country": None,
                "phones": None,
                "mails": None,
            }
        )
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result.pop("name"), "FEDER")
        self.assertEqual(set(result.values()), {""})

    def test_legacy_integer_zipcode_is_coerced_to_string(self):
        # ``zipcode`` is a TextLine today, but records created when it was an
        # Int may still hold one.
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(zipcode=5300)
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result["zipcode"], "5300")

    def test_first_phone_and_mail_win(self):
        self.request.form["uid"] = "contact-uid"
        payload = self.contact_payload(
            phones=[{"number": "+3265000000"}, {"number": "+3265999999"}],
            mails=[{"mail_address": "first@ccmons.be"}, {"mail_address": "b@c.be"}],
        )
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result["phone"], "+3265000000")
        self.assertEqual(result["email"], "first@ccmons.be")

    def test_unknown_uid_returns_empty_json(self):
        self.request.form["uid"] = "gone"
        payload = {"items": [], "items_total": 0}
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(result, {})

    def test_unreachable_directory_returns_empty_json(self):
        self.request.form["uid"] = "contact-uid"
        with patch(REQUESTS_GET, return_value=self.fake_response({}, status_code=503)):
            result = json.loads(self.make_view()())
        self.assertEqual(result, {})

    def test_searches_the_directory_on_the_contact_uid(self):
        self.request.form["uid"] = "contact uid/with specials"
        with patch(
            REQUESTS_GET, return_value=self.fake_response(self.contact_payload())
        ) as mock_get:
            self.make_view()()
        self.assertEqual(
            mock_get.call_args[0][0],
            "{}/@search?UID={}&fullobjects=true".format(
                DIRECTORY_URL, "contact uid/with specials"
            ),
        )

    def test_cache_buster_is_forwarded_to_the_directory(self):
        # The "Refresh" button sends "_=<timestamp>" so no cache in front of the
        # directory can serve a contact that was just edited there.
        self.request.form["uid"] = "contact-uid"
        self.request.form["_"] = "1755000000000"
        with patch(
            REQUESTS_GET, return_value=self.fake_response(self.contact_payload())
        ) as mock_get:
            self.make_view()()
        self.assertEqual(
            mock_get.call_args[0][0],
            "{}/@search?UID=contact-uid&fullobjects=true&_=1755000000000".format(
                DIRECTORY_URL
            ),
        )

    def test_no_cache_buster_leaves_the_url_untouched(self):
        self.request.form["uid"] = "contact-uid"
        with patch(
            REQUESTS_GET, return_value=self.fake_response(self.contact_payload())
        ) as mock_get:
            self.make_view()()
        self.assertNotIn("&_=", mock_get.call_args[0][0])


class TestDirectoryLinkedEntitiesInfoView(DirectoryInfoTestCase):
    def make_view(self, context=None):
        return super().make_view(
            context if context is not None else self.event,
            "directory_entities_info",
        )

    def entities_payload(self, *entities):
        return {"items": list(entities), "items_total": len(entities)}

    def test_returns_empty_list_outside_an_entity(self):
        with patch(REQUESTS_GET) as mock_get:
            result = json.loads(self.make_view(self.portal)())
        self.assertEqual(result, [])
        mock_get.assert_not_called()

    def test_response_is_flagged_as_json(self):
        self.make_view()()
        self.assertEqual(
            self.request.response.getHeader("Content-Type"), "application/json"
        )

    def test_returns_empty_list_without_linked_entities(self):
        self.assertFalse(self.entity.directory_linked_entities)
        with patch(REQUESTS_GET) as mock_get:
            result = json.loads(self.make_view()())
        self.assertEqual(result, [])
        mock_get.assert_not_called()

    def test_returns_title_and_url_of_each_linked_entity(self):
        self.entity.directory_linked_entities = ["uid1", "uid2"]
        payload = self.entities_payload(
            {"@id": "https://annuaire.enwallonie.be/mons", "title": "Mons"},
            {"@id": "https://annuaire.enwallonie.be/namur", "title": "Namur"},
        )
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(
            result,
            [
                {"title": "Mons", "url": "https://annuaire.enwallonie.be/mons"},
                {"title": "Namur", "url": "https://annuaire.enwallonie.be/namur"},
            ],
        )

    def test_skips_entities_without_url(self):
        self.entity.directory_linked_entities = ["uid1", "uid2"]
        payload = self.entities_payload(
            {"@id": None, "title": "Sans URL"},
            {"@id": "https://annuaire.enwallonie.be/mons", "title": "Mons"},
        )
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(
            result, [{"title": "Mons", "url": "https://annuaire.enwallonie.be/mons"}]
        )

    def test_missing_title_is_normalised_to_an_empty_string(self):
        self.entity.directory_linked_entities = ["uid1"]
        payload = self.entities_payload(
            {"@id": "https://annuaire.enwallonie.be/mons", "title": None}
        )
        with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
            result = json.loads(self.make_view()())
        self.assertEqual(
            result, [{"title": "", "url": "https://annuaire.enwallonie.be/mons"}]
        )

    def test_unreachable_directory_returns_empty_list(self):
        self.entity.directory_linked_entities = ["uid1"]
        with patch(REQUESTS_GET, return_value=self.fake_response({}, status_code=503)):
            result = json.loads(self.make_view()())
        self.assertEqual(result, [])

    def test_asks_the_directory_for_every_linked_entity_at_once(self):
        self.entity.directory_linked_entities = ["uid1", "uid2"]
        with patch(
            REQUESTS_GET, return_value=self.fake_response(self.entities_payload())
        ) as mock_get:
            self.make_view()()
        # Repeated UID params are OR-ed by the catalog, hence a single request.
        self.assertEqual(
            mock_get.call_args[0][0],
            "{}/@search?portal_type=imio.directory.Entity&sort_on=sortable_title"
            "&b_size=3000&metadata_fields=UID&UID=uid1&UID=uid2".format(DIRECTORY_URL),
        )

    def test_looks_up_the_entity_from_a_nested_context(self):
        # The view is called on <body data-base-url>, i.e. the Event on an edit
        # form and the container Agenda on an add form: both must resolve the
        # same parent Entity.
        self.entity.directory_linked_entities = ["uid1"]
        payload = self.entities_payload(
            {"@id": "https://annuaire.enwallonie.be/mons", "title": "Mons"}
        )
        for context in (self.entity, self.agenda, self.event):
            with patch(REQUESTS_GET, return_value=self.fake_response(payload)):
                result = json.loads(self.make_view(context)())
            self.assertEqual(
                result,
                [{"title": "Mons", "url": "https://annuaire.enwallonie.be/mons"}],
                "unexpected result for context {}".format(context.portal_type),
            )


# <audit>
#   <file>test_contact_info.py</file>
#   <requirements_applied>R1, R2, R4, R5, R6</requirements_applied>
#   <deviations>
#     R1: the skill prescribes requests_mock, but no test in imio.events.core
#     depends on it (it is not in test-requirements either). Followed R6 and used
#     unittest.mock.patch on requests.get, as test_odwb.py and test_rest.py do.
#     R3: no content added to testing.py — the entity/agenda/event fixture is
#     specific to this file, matching test_odwb.py and test_actions.py.
#   </deviations>
#   <questions>None</questions>
# </audit>
