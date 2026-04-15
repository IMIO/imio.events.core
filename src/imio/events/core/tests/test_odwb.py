# -*- coding: utf-8 -*-

from collective.geolocationbehavior.geolocation import IGeolocatable
from imio.events.core.rest.odwb_endpoint import _batched
from imio.events.core.rest.odwb_endpoint import EventEncoder
from imio.events.core.rest.odwb_endpoint import OdwbEndpointGet
from imio.events.core.rest.odwb_endpoint import OdwbEntitiesEndpointGet
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.formwidget.geolocation.geolocation import Geolocation
from unittest.mock import MagicMock
from unittest.mock import patch

import datetime
import json
import pytz
import requests
import unittest


class TestBatched(unittest.TestCase):
    """Tests for the module-level _batched() helper."""

    def test_empty_iterable_yields_nothing(self):
        self.assertEqual(list(_batched([], 3)), [])

    def test_yields_single_batch_when_shorter_than_size(self):
        self.assertEqual(list(_batched([1, 2], 5)), [[1, 2]])

    def test_splits_evenly_into_multiple_batches(self):
        self.assertEqual(list(_batched(range(6), 3)), [[0, 1, 2], [3, 4, 5]])

    def test_last_batch_contains_remainder(self):
        self.assertEqual(list(_batched(range(7), 3)), [[0, 1, 2], [3, 4, 5], [6]])

    def test_works_with_generator_input(self):
        self.assertEqual(list(_batched((x for x in range(4)), 2)), [[0, 1], [2, 3]])


class TestEventEncoder(unittest.TestCase):
    """Tests for the EventEncoder JSON encoder."""

    def test_aware_datetime_converted_to_brussels_summer(self):
        """UTC summer datetime is shifted to CEST (+2h)."""
        dt = datetime.datetime(2024, 6, 15, 10, 0, 0, tzinfo=pytz.utc)
        result = json.loads(json.dumps(dt, cls=EventEncoder))
        # 10:00 UTC → 12:00 CEST (UTC+2)
        self.assertIn("12:00:00", result)
        self.assertIn("+02:00", result)

    def test_aware_datetime_converted_to_brussels_winter(self):
        """UTC winter datetime is shifted to CET (+1h)."""
        dt = datetime.datetime(2024, 1, 15, 10, 0, 0, tzinfo=pytz.utc)
        result = json.loads(json.dumps(dt, cls=EventEncoder))
        # 10:00 UTC → 11:00 CET (UTC+1)
        self.assertIn("11:00:00", result)
        self.assertIn("+01:00", result)

    def test_naive_datetime_encoded_without_conversion(self):
        """Naive datetime (no tzinfo) is serialised as-is."""
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        result = json.loads(json.dumps(dt, cls=EventEncoder))
        self.assertIn("2024-01-15T10:30:00", result)


class RestFunctionalTest(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
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

    @patch("requests.post")
    def test_odwb_url_errors(self, mock_post):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Event",
        )
        # OdwbEndpointGet.test_in_staging_or_local = True
        mock_request = MagicMock()

        mock_post.side_effect = requests.exceptions.ConnectionError(
            "ODWB : Connection error occurred"
        )
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : Connection error occurred")
        mock_post.side_effect = requests.exceptions.Timeout("ODWB : Request timed out")
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : Request timed out")

        mock_post.side_effect = requests.exceptions.HTTPError(
            "ODWB : HTTP error occurred"
        )
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : HTTP error occurred")

        mock_post.side_effect = Exception("ODWB : Unexpected error occurred")
        endpoint = OdwbEndpointGet(event, mock_request)
        response = endpoint.reply()
        self.assertEqual(response, "ODWB : Unexpected error occurred")

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_get_events_to_send_to_odwb(self, m_post, m_reg):
        fake_response = MagicMock()
        fake_response.text = "KAMOULOX"
        m_post.return_value = fake_response
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Event",
        )
        IGeolocatable(event).geolocation = Geolocation(latitude="4.5", longitude="45")
        event.exclude_from_nav = True

        entity2 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity2",
            title="Entity 2",
        )
        agenda2 = api.content.create(
            container=entity2,
            type="imio.events.Agenda",
            id="agenda",
            title="Agenda 2",
        )

        event2 = api.content.create(
            container=agenda2,
            type="imio.events.Event",
            id="event",
            title="Event 2",
        )

        api.content.transition(event, "publish")
        endpoint = OdwbEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 1 (published) event is returned on self.portal
        self.assertEqual(endpoint.__datas_count__, 1)
        m_post.assert_called()
        called_url = m_post.call_args.args[0]
        self.assertIn("https://www.odwb.be/api/push/1.0", called_url)

        api.content.transition(event2, "publish")
        endpoint = OdwbEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 2 (published) events are returned on self.portal
        self.assertEqual(endpoint.__datas_count__, 2)

        # test endpoint on agenda
        endpoint = OdwbEndpointGet(self.agenda, self.request)
        endpoint.reply()
        # 1 (published) event is returned on self.agenda
        self.assertEqual(endpoint.__datas_count__, 1)

        # test endpoint on entity
        endpoint = OdwbEndpointGet(self.entity, self.request)
        endpoint.reply()
        # 1 (published) event is returned on self.entity
        self.assertEqual(endpoint.__datas_count__, 1)

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_get_entities_to_send_to_odwb(self, m_post, m_reg):
        fake_response = MagicMock()
        fake_response.text = "KAMOULOX"
        m_post.return_value = fake_response
        api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity2",
            title="Entity 2",
        )
        # OdwbEntitiesEndpointGet.test_in_staging_or_local = True
        endpoint = OdwbEntitiesEndpointGet(self.portal, self.request)
        endpoint.reply()
        # 2 entities are returned on self.portal (entities are automaticly published)
        self.assertEqual(len(endpoint.__datas__), 2)
        m_post.assert_called()
        called_url = m_post.call_args.args[0]
        self.assertIn("https://www.odwb.be/api/push/1.0", called_url)

        api.content.transition(self.entity, "reject")
        endpoint = OdwbEntitiesEndpointGet(self.portal, self.request)
        endpoint.reply()
        self.assertEqual(len(endpoint.__datas__), 1)

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    def test_log_odwb_response_success_ok_field(self, m_reg):
        """_log_odwb_response logs INFO with 'sent/updated' verb for {"ok": true}."""
        endpoint = OdwbEndpointGet(self.entity, self.request)
        with self.assertLogs("imio.events.core", level="INFO") as cm:
            endpoint._log_odwb_response("push", 3, '{"ok": true}')
        self.assertTrue(any("sent/updated" in line for line in cm.output))

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    def test_log_odwb_response_success_status_ok(self, m_reg):
        """_log_odwb_response logs INFO with 'deleted' verb for delete action."""
        endpoint = OdwbEndpointGet(self.entity, self.request)
        with self.assertLogs("imio.events.core", level="INFO") as cm:
            endpoint._log_odwb_response("delete", 2, '{"status": "ok"}')
        self.assertTrue(any("deleted" in line for line in cm.output))

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    def test_log_odwb_response_json_error(self, m_reg):
        """_log_odwb_response logs WARNING when ODWB returns a JSON error response."""
        endpoint = OdwbEndpointGet(self.entity, self.request)
        with self.assertLogs("imio.events.core", level="WARNING") as cm:
            endpoint._log_odwb_response("push", 5, '{"error": "invalid key"}')
        self.assertTrue(any("WARNING" in line for line in cm.output))

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    def test_log_odwb_response_non_json(self, m_reg):
        """_log_odwb_response logs WARNING with 'unexpected response' for plain strings."""
        endpoint = OdwbEndpointGet(self.entity, self.request)
        with self.assertLogs("imio.events.core", level="WARNING") as cm:
            endpoint._log_odwb_response("push", 1, "ODWB : Connection error occurred")
        self.assertTrue(any("unexpected response" in line for line in cm.output))

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_reply_returns_none_when_no_events(self, m_post, m_reg):
        """reply() returns None when there are no published events."""
        endpoint = OdwbEndpointGet(self.portal, self.request)
        result = endpoint.reply()
        self.assertIsNone(result)
        m_post.assert_not_called()

    @patch("imio.events.core.rest.odwb_endpoint._batched")
    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_reply_returns_last_response_when_all_batches_identical(
        self, m_post, m_reg, m_batched
    ):
        """reply() returns a single string when all batch responses are equal."""
        fake_response = MagicMock()
        fake_response.text = '{"ok": true}'
        m_post.return_value = fake_response
        m_batched.return_value = iter([[{"id": "e1"}], [{"id": "e2"}]])
        endpoint = OdwbEndpointGet(self.portal, self.request)
        result = endpoint.reply()
        self.assertEqual(result, '{"ok": true}')
        self.assertEqual(m_post.call_count, 2)

    @patch("imio.events.core.rest.odwb_endpoint._batched")
    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_reply_returns_list_when_batch_responses_differ(
        self, m_post, m_reg, m_batched
    ):
        """reply() returns a list when batches receive different responses."""
        r1 = MagicMock()
        r1.text = '{"ok": true}'
        r2 = MagicMock()
        r2.text = '{"error": "rate_limit"}'
        m_post.side_effect = [r1, r2]
        m_batched.return_value = iter([[{"id": "e1"}], [{"id": "e2"}]])
        endpoint = OdwbEndpointGet(self.portal, self.request)
        result = endpoint.reply()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_remove_event(self, m_post, m_reg):
        """remove() sends the event payload to the ODWB delete endpoint."""
        fake_response = MagicMock()
        fake_response.text = '{"ok": true}'
        m_post.return_value = fake_response
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
            title="Event",
        )
        api.content.transition(event, "publish")
        endpoint = OdwbEndpointGet(event, self.request)
        result = endpoint.remove()
        self.assertEqual(result, '{"ok": true}')
        called_url = m_post.call_args.args[0]
        self.assertIn("delete", called_url)

    @patch(
        "imio.smartweb.common.rest.odwb.api.portal.get_registry_record",
        return_value="KAMOULOX_KEY",
    )
    @patch("imio.smartweb.common.rest.odwb.requests.post")
    def test_remove_returns_none_when_no_events(self, m_post, m_reg):
        """remove() returns None when there are no published events."""
        endpoint = OdwbEndpointGet(self.portal, self.request)
        result = endpoint.remove()
        self.assertIsNone(result)
        m_post.assert_not_called()
