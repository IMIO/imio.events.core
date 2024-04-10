# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timezone
from freezegun import freeze_time
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from imio.events.core.utils import expand_occurences
from imio.events.core.utils import get_agenda_for_event
from imio.events.core.utils import get_agendas_uids_for_faceted
from imio.events.core.utils import get_entity_for_obj
from imio.events.core.utils import get_start_date
from imio.events.core.utils import remove_zero_interval_from_recrule
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


class TestAgenda(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.authorized_types_in_agenda = [
            "imio.events.Folder",
            "imio.events.Event",
        ]
        self.unauthorized_types_in_agenda = [
            "imio.events.Agenda",
            "Document",
            "File",
            "Image",
        ]

        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal
        self.entity1 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity1",
        )
        self.agenda1 = api.content.create(
            container=self.entity1,
            type="imio.events.Agenda",
            id="agenda1",
        )
        self.event1 = api.content.create(
            container=self.agenda1,
            type="imio.events.Event",
            id="event1",
        )
        self.entity2 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity2",
        )
        self.agenda2 = api.content.create(
            container=self.entity2,
            type="imio.events.Agenda",
            id="agenda2",
        )
        self.event2 = api.content.create(
            container=self.agenda2,
            type="imio.events.Event",
            id="event2",
        )
        self.agenda3 = api.content.create(
            container=self.entity1,
            type="imio.events.Agenda",
            id="agenda3",
        )

    def test_get_entity_for_obj(self):
        self.assertEqual(get_entity_for_obj(self.entity1), self.entity1)
        self.assertEqual(get_entity_for_obj(self.agenda1), self.entity1)
        self.assertEqual(get_entity_for_obj(self.event1), self.entity1)

    def test_get_agenda_for_event(self):
        self.assertEqual(get_agenda_for_event(self.event1), self.agenda1)
        self.assertEqual(get_agenda_for_event(self.event2), self.agenda2)

    def test_get_agendas_uids_for_faceted(self):
        with self.assertRaises(NotImplementedError):
            get_agendas_uids_for_faceted(self.event1)
        self.assertEqual(
            get_agendas_uids_for_faceted(self.agenda1), [self.agenda1.UID()]
        )
        default_agendas = self.entity1.listFolderContents(
            contentFilter={"portal_type": "imio.events.Agenda"}
        )
        uids = []
        for event in default_agendas:
            uids.append(event.UID())
        self.assertEqual(
            get_agendas_uids_for_faceted(self.entity1).sort(),
            uids.sort(),
        )
        self.assertIn(self.agenda1.UID(), get_agendas_uids_for_faceted(self.entity1))
        self.assertIn(self.agenda3.UID(), get_agendas_uids_for_faceted(self.entity1))

    @freeze_time("2022-11-10")
    def test_expand_occurences(self):
        # test without occurence
        events = [
            {
                "start": "2022-11-13T12:00:00+00:00",
                "end": "2022-11-13T13:00:00+00:00",
                "first_start": "2022-11-13T12:00:00+00:00",
                "first_end": "2022-11-13T13:00:00+00:00",
                "recurrence": None,
                "open_end": False,
                "whole_day": False,
            }
        ]
        expanded_events = expand_occurences(events)
        self.assertEqual(len(expanded_events), 1)
        events = [
            {
                "start": "2022-11-13T12:00:00+00:00",
                "end": "2022-11-14T13:00:00+00:00",
                "first_start": "2022-11-13T12:00:00+00:00",
                "first_end": "2022-11-14T13:00:00+00:00",
                "recurrence": None,
                "open_end": False,
                "whole_day": False,
            }
        ]
        expanded_events = expand_occurences(events)
        self.assertEqual(len(expanded_events), 1)

        # test range start for occurences
        events = [
            {
                "start": "2022-11-15T12:00:00+00:00",
                "end": "2022-11-15T13:00:00+00:00",
                "first_start": "2022-11-01T12:00:00+00:00",
                "first_end": "2022-11-01T13:00:00+00:00",
                "recurrence": "RRULE:FREQ=WEEKLY;COUNT=5",
                "open_end": False,
                "whole_day": False,
            }
        ]
        expanded_events = expand_occurences(events)
        self.assertEqual(len(expanded_events), 5)

        # test occurences data
        events = [
            {
                "start": "2022-11-13T12:00:00+00:00",
                "end": "2022-11-13T13:00:00+00:00",
                "first_start": "2022-11-13T12:00:00+00:00",
                "first_end": "2022-11-13T13:00:00+00:00",
                "recurrence": "RRULE:FREQ=WEEKLY;COUNT=5",
                "open_end": False,
                "whole_day": False,
            }
        ]
        expanded_events = expand_occurences(events)
        self.assertEqual(len(expanded_events), 5)
        self.assertEqual(expanded_events[-1]["start"], "2022-12-11T12:00:00+00:00")
        self.assertEqual(expanded_events[-1]["end"], "2022-12-11T13:00:00+00:00")
        events = [
            {
                "start": "2022-11-13T12:00:00+00:00",
                "end": "2022-11-13T12:00:00+00:00",
                "first_start": "2022-11-13T12:00:00+00:00",
                "first_end": "2022-11-13T12:00:00+00:00",
                "recurrence": "RRULE:FREQ=WEEKLY;COUNT=5",
                "open_end": False,
                "whole_day": True,
            }
        ]
        expanded_events = expand_occurences(events)
        self.assertEqual(expanded_events[-1]["start"], "2022-12-11T12:00:00+00:00")
        self.assertEqual(expanded_events[-1]["end"], "2022-12-11T12:00:00+00:00")
        events = [
            {
                "start": "2022-11-13T00:00:00+00:00",
                "end": "2022-11-13T23:59:59+00:00",
                "first_start": "2022-11-13T00:00:00+00:00",
                "first_end": "2022-11-13T23:59:59+00:00",
                "recurrence": "RRULE:FREQ=WEEKLY;COUNT=5",
                "open_end": True,
                "whole_day": True,
            }
        ]
        expanded_events = expand_occurences(events)
        self.assertEqual(expanded_events[-1]["start"], "2022-12-11T00:00:00+00:00")
        self.assertEqual(expanded_events[-1]["end"], "2022-12-11T23:59:59+00:00")

    def test_get_start_date(self):
        event = {
            "start": "2022-11-13T12:00:00+00:00",
            "end": "2022-11-13T13:00:00+00:00",
            "recurrence": None,
            "open_end": False,
            "whole_day": False,
        }
        start_date = get_start_date(event)
        result = datetime(2022, 11, 13, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(start_date, result)

    def test_remove_zero_interval_from_recrule(self):
        recrule = "RRULE:FREQ=WEEKLY;COUNT=5"
        self.assertEqual(
            remove_zero_interval_from_recrule(recrule), "RRULE:FREQ=WEEKLY;COUNT=5"
        )
        recrule = "RRULE:FREQ=WEEKLY;INTERVAL=1"
        self.assertEqual(
            remove_zero_interval_from_recrule(recrule), "RRULE:FREQ=WEEKLY;INTERVAL=1"
        )
        recrule = "RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=5"
        self.assertEqual(
            remove_zero_interval_from_recrule(recrule),
            "RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=5",
        )
        recrule = "RRULE:FREQ=WEEKLY;INTERVAL=0"
        self.assertEqual(
            remove_zero_interval_from_recrule(recrule), "RRULE:FREQ=WEEKLY"
        )
        recrule = "RRULE:FREQ=WEEKLY;INTERVAL=0;COUNT=5"
        self.assertEqual(
            remove_zero_interval_from_recrule(recrule), "RRULE:FREQ=WEEKLY;COUNT=5"
        )
        recrule = "RRULE:FREQ=WEEKLY;INTERVAL=0\nRDATE:2023-09-12T000000"
        self.assertEqual(
            remove_zero_interval_from_recrule(recrule),
            "RRULE:FREQ=WEEKLY\nRDATE:2023-09-12T000000",
        )
