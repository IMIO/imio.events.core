# -*- coding: utf-8 -*-

from collective.geolocationbehavior.geolocation import IGeolocatable
from datetime import datetime
from imio.events.core.browser.forms import EventCustomAddForm
from imio.events.core.browser.forms import EventCustomEditForm
from imio.events.core.contents.event.content import IEvent
from imio.events.core.interfaces import IImioEventsCoreLayer
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from imio.events.core.tests.utils import make_named_image
from imio.smartweb.common.utils import geocode_object
from plone import api
from plone.api.exc import InvalidParameterError
from plone.app.contenttypes.behaviors.leadimage import ILeadImageBehavior
from plone.app.dexterity.behaviors.metadata import IBasic
from plone.app.imagecropping import PAI_STORAGE_KEY
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.z3cform.interfaces import IPloneFormLayer
from plone.dexterity.interfaces import IDexterityFTI
from plone.formwidget.geolocation.geolocation import Geolocation
from plone.namedfile.file import NamedBlobFile
from plone.namedfile.file import NamedBlobImage
from unittest import mock
from z3c.form.interfaces import WidgetActionExecutionError
from z3c.relationfield import RelationValue
from z3c.relationfield.interfaces import IRelationList
from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.component import createObject
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import Attributes
from zope.lifecycleevent import modified
from zope.publisher.browser import TestRequest
from zope.schema.interfaces import IVocabularyFactory

import geopy
import pytz
import unittest


class TestEvent(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.authorized_types_in_event = [
            "File",
            "Image",
        ]
        self.unauthorized_types_in_event = [
            "imio.events.Agenda",
            "imio.events.Folder",
            "imio.events.Event",
            "Document",
        ]
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.parent = self.portal
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="imio.events.Entity",
        )
        self.agenda = api.content.create(
            container=self.entity,
            type="imio.events.Agenda",
            id="imio.events.Agenda",
        )
        self.folder = api.content.create(
            container=self.agenda,
            type="imio.events.Folder",
            id="imio.events.Folder",
        )

    def test_ct_event_schema(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        schema = fti.lookupSchema()
        self.assertEqual(IEvent, schema)

    def test_ct_event_fti(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        self.assertTrue(fti)

    def test_ct_event_factory(self):
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        factory = fti.factory
        obj = createObject(factory)
        self.assertTrue(
            IEvent.providedBy(obj),
            "IEvent not provided by {0}!".format(
                obj,
            ),
        )

    def test_ct_event_adding(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        obj = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="imio.events.Event",
        )

        self.assertTrue(
            IEvent.providedBy(obj),
            "IEvent not provided by {0}!".format(
                obj.id,
            ),
        )

        parent = obj.__parent__
        self.assertIn("imio.events.Event", parent.objectIds())

        # check that deleting the object works too
        api.content.delete(obj=obj)
        self.assertNotIn("imio.events.Event", parent.objectIds())

    def test_ct_event_globally_addable(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        self.assertFalse(
            fti.global_allow, "{0} is not globally addable!".format(fti.id)
        )

    def test_ct_event_filter_content_type_true(self):
        setRoles(self.portal, TEST_USER_ID, ["Contributor"])
        fti = queryUtility(IDexterityFTI, name="imio.events.Event")
        portal_types = self.portal.portal_types
        parent_id = portal_types.constructContent(
            fti.id,
            self.folder,
            "imio.events.Event_id",
            title="imio.events.Event container",
        )
        folder = self.folder[parent_id]
        for t in self.unauthorized_types_in_event:
            with self.assertRaises(InvalidParameterError):
                api.content.create(
                    container=folder,
                    type=t,
                    title="My {}".format(t),
                )
        for t in self.authorized_types_in_event:
            api.content.create(
                container=folder,
                type=t,
                title="My {}".format(t),
            )
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        with self.assertRaises(InvalidParameterError):
            api.content.create(
                container=folder,
                type="imio.events.Entity",
                title="My Entity",
            )

    def test_event_local_category(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsLocalCategories"
        )
        vocabulary = factory(event)
        self.assertEqual(len(vocabulary), 0)

        self.entity.local_categories = [
            {"fr": "First", "nl": "", "de": "", "en": ""},
            {"fr": "Second", "nl": "", "de": "", "en": ""},
            {"fr": "Third", "nl": "", "de": "", "en": ""},
        ]
        vocabulary = factory(event)
        self.assertEqual(len(vocabulary), 3)

    def test_view(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="My event item",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertIn("My event item", view())

    def test_embed_video(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="My event item",
        )
        event.video_url = "https://www.youtube.com/watch?v=_dOAthafoGQ"
        view = queryMultiAdapter((event, self.request), name="view")
        embedded_video = view.get_embed_video()
        self.assertIn("iframe", embedded_video)
        self.assertIn(
            "https://www.youtube.com/embed/_dOAthafoGQ?feature=oembed", embedded_video
        )

    def test_has_leadimage(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="My event item",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertEqual(view.has_leadimage(), False)
        event.image = NamedBlobImage(**make_named_image())
        self.assertEqual(view.has_leadimage(), True)

    def test_subscriber_to_select_current_agenda(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="My event item",
        )
        self.assertEqual(event.selected_agendas, [self.agenda.UID()])

    def test_referrer_agendas(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        intids = getUtility(IIntIds)
        entity2 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity2",
        )
        agenda2 = api.content.create(
            container=entity2,
            type="imio.events.Agenda",
            id="agenda2",
        )
        event2 = api.content.create(
            container=agenda2,
            type="imio.events.Event",
            id="event2",
        )
        setattr(
            self.agenda, "populating_agendas", [RelationValue(intids.getId(agenda2))]
        )
        modified(self.agenda, Attributes(IRelationList, "populating_agendas"))
        self.assertIn(self.agenda.UID(), event2.selected_agendas)

        # if we create an event in an agenda that is referred in another agenda
        # then, referrer agenda UID is in event.selected_agendas list.
        event2b = api.content.create(
            container=agenda2,
            type="imio.events.Event",
            id="event2b",
        )
        self.assertIn(self.agenda.UID(), event2b.selected_agendas)

    def test_automaticaly_readd_container_agenda_uid(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )
        self.assertIn(self.agenda.UID(), event.selected_agendas)
        event.selected_agendas = []
        event.reindexObject()
        modified(event)
        self.assertIn(self.agenda.UID(), event.selected_agendas)

    def test_removing_old_cropping(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )
        event.image = NamedBlobImage(**make_named_image())
        view = event.restrictedTraverse("@@crop-image")
        view._crop(fieldname="image", scale="portrait_affiche", box=(1, 1, 200, 200))
        annotation = IAnnotations(event).get(PAI_STORAGE_KEY)
        self.assertEqual(annotation, {"image_portrait_affiche": (1, 1, 200, 200)})

        modified(event, Attributes(IBasic, "IBasic.title"))
        annotation = IAnnotations(event).get(PAI_STORAGE_KEY)
        self.assertEqual(annotation, {"image_portrait_affiche": (1, 1, 200, 200)})

        modified(event, Attributes(ILeadImageBehavior, "ILeadImageBehavior.image"))
        annotation = IAnnotations(event).get(PAI_STORAGE_KEY)
        self.assertEqual(annotation, {})

    def test_geolocation(self):
        attr = {"geocode.return_value": mock.Mock(latitude=1, longitude=2)}
        geopy.geocoders.Nominatim = mock.Mock(return_value=mock.Mock(**attr))

        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="event",
        )

        self.assertFalse(event.is_geolocated)
        event.geolocation = Geolocation(0, 0)
        event.street = "My beautiful street"
        geocode_object(event)
        self.assertTrue(event.is_geolocated)
        self.assertEqual(event.geolocation.latitude, 1)
        self.assertEqual(event.geolocation.longitude, 2)

    def test_geolocation_in_view(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        IGeolocatable(event).geolocation = Geolocation(latitude="4.5", longitude="45")
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertIn("map", view())
        self.assertIn('class="pat-leaflet map"', view())

    def test_name_chooser(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="event",
        )
        self.assertEqual(event.id, event.UID())

        entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="entity",
        )
        self.assertNotEqual(entity.id, entity.UID())
        self.assertEqual(entity.id, "entity")

    def test_js_bundles(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Event",
        )

        alsoProvides(self.request, IImioEventsCoreLayer)
        getMultiAdapter((event, self.request), name="view")()
        bundles = getattr(self.request, "enabled_bundles", [])
        self.assertEqual(len(bundles), 0)
        image = api.content.create(
            container=event,
            type="Image",
            title="Image",
        )
        image.image = NamedBlobImage(**make_named_image())
        getMultiAdapter((event, self.request), name="view")()
        bundles = getattr(self.request, "enabled_bundles", [])
        self.assertEqual(len(bundles), 2)
        self.assertListEqual(bundles, ["spotlightjs", "flexbin"])

    def test_has_contact(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertEqual(view.has_contact(), False)
        event.contact_name = "Mike 'Billy' Bainbridge"
        self.assertEqual(view.has_contact(), True)
        event.contact_name = None
        event.contact_email = "billy@plone.org"
        self.assertEqual(view.has_contact(), True)
        event.contact_email = None
        event.contact_phone = "01123456"
        self.assertEqual(view.has_contact(), True)

    def test_address(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertEqual(view.address(), "")
        event.street = "Rue Léon Morel"
        self.assertEqual(view.address(), "Rue Léon Morel")
        event.city = "Gembloux"
        self.assertEqual(view.address(), "Rue Léon Morel Gembloux")
        event.country = "be"
        self.assertEqual(view.address(), "Rue Léon Morel Gembloux Belgique")

    def test_iam(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertEqual(view.iam(), None)
        event.iam = ["young", "parent"]
        self.assertEqual(view.iam(), "Jeune, Parent")

    def test_topics(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertEqual(view.topics(), None)
        event.topics = ["citizen_participation", "sports"]
        self.assertEqual(view.topics(), "Participation citoyenne, Sports")

    def test_category(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertEqual(view.topics(), None)
        event.category = "exhibition_artistic_meeting"
        self.assertEqual(view.category(), "Exposition et rencontre artistique")

    def test_files_in_event_view(self):
        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertNotIn("event-files", view())
        file_obj = api.content.create(
            container=event,
            type="File",
            title="file",
        )
        file_obj.file = NamedBlobFile(data="file data", filename="file.txt")
        view = queryMultiAdapter((event, self.request), name="view")
        self.assertIn("++resource++mimetype.icons/txt.png", view())

    def test_timespan_invariant(self):
        request = TestRequest(
            form={
                "form.widgets.IBasic.title": "My Event",
                "form.widgets.event_type": "event-driven",
                "form.widgets.ticket_url": "https://www.kamoulox.be",
                "form.widgets.IEventBasic.start": "2023-09-01T22:00",
                "form.widgets.IEventBasic.end": "2050-09-01T22:00",
                "form.buttons.save": "Save",
            }
        )
        alsoProvides(request, IPloneFormLayer)
        form = EventCustomAddForm(self.folder, request)
        form.portal_type = "imio.events.Event"
        form.update()
        with self.assertRaises(WidgetActionExecutionError):
            form.handleAdd(form, {})

        request = TestRequest(
            form={
                "form.widgets.IBasic.title": "My Event",
                "form.widgets.event_type": "event-driven",
                "form.widgets.ticket_url": "https://www.kamoulox.be",
                "form.widgets.IEventBasic.start": "2023-09-01T22:00",
                "form.widgets.IEventBasic.end": "2024-09-01T22:00",
                "form.buttons.save": "Save",
            }
        )
        alsoProvides(request, IPloneFormLayer)
        alsoProvides(request, IAttributeAnnotatable)
        form = EventCustomAddForm(self.agenda, request)
        form.portal_type = "imio.events.Event"
        form.update()
        form.handleAdd(form, {})

        event = api.content.create(
            container=self.folder,
            type="imio.events.Event",
            id="my-event",
        )
        utc_timezone = pytz.UTC
        event.start = datetime(2023, 9, 1, 22, 00, tzinfo=utc_timezone)
        event.end = datetime(2024, 9, 1, 22, 00, tzinfo=utc_timezone)
        request = TestRequest(
            form={
                "form.widgets.IBasic.title": "My Event",
                "form.widgets.event_type": "event-driven",
                "form.widgets.IEventBasic.start": "2023-09-01T22:00",
                "form.widgets.IEventBasic.end": "2050-09-01T22:00",
                "form.buttons.save": "Save",
            }
        )
        alsoProvides(request, IPloneFormLayer)
        form = EventCustomEditForm(event, request)
        form.portal_type = "imio.events.Event"
        form.update()
        with self.assertRaises(WidgetActionExecutionError):
            form.handleApply(form, {})

    def test_recurrence(self):
        event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            id="event",
        )
        event.recurrence = "RRULE:FREQ=WEEKLY;INTERVAL=0;COUNT=5"
        modified(event)
        self.assertEqual(event.recurrence, "RRULE:FREQ=WEEKLY;COUNT=5")
        event.recurrence = "RRULE:FREQ=WEEKLY;INTERVAL=0"
        modified(event)
        self.assertEqual(event.recurrence, "RRULE:FREQ=WEEKLY")
