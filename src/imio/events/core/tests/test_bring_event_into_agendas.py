# -*- coding: utf-8 -*-

from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import TEST_USER_PASSWORD
from plone.testing.zope import Browser

import json
import transaction
import unittest


class TestEvent(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.request = self.layer["request"]
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity1 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity1",
            title="Entity 1",
        )
        self.agenda1 = api.content.create(
            container=self.entity1,
            type="imio.events.Agenda",
            id="agenda1",
            title="Agenda 1",
        )
        self.agenda1b = api.content.create(
            container=self.entity1,
            type="imio.events.Agenda",
            id="agenda1b",
            title="Agenda 1b",
        )
        self.event1 = api.content.create(
            container=self.agenda1,
            type="imio.events.Event",
            id="event1",
            title="Event 1",
        )

        self.entity2 = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            id="entity2",
            title="Entity 2",
        )
        self.agenda2 = api.content.create(
            container=self.entity2,
            type="imio.events.Agenda",
            id="agenda2",
            title="Agenda 2",
        )
        self.event2 = api.content.create(
            container=self.agenda2,
            type="imio.events.Event",
            id="event2",
            title="Event 2",
        )

    def test_brings_event_into_agendas(self):
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
        browser.open(
            f"{self.event2.absolute_url()}/@@bring_event_into_agendas_form/@@getVocabulary?name=imio.events.vocabulary.UserAgendas&field=agendas"
        )
        content = browser.contents
        results = json.loads(content).get("results")
        available_agendas_uids = [r.get("id") for r in results]
        self.assertNotIn(self.event2.selected_agendas, available_agendas_uids)

        # To be continued...
        # browser.open(f"{self.event2.absolute_url()}/@@bring_event_into_agendas_form")
        # select = browser.getControl(name="form.widgets.agendas")
        # select.value = "23eaca484039416c959a29a1c7509470"

        # button = browser.getControl(name="form.buttons.submit").click()

        # request = self.request
        # # request.form['agendas'] = "23eaca484039416c959a29a1c7509470"
        # # request.form['form.buttons.submit'] = 'Submit'
        # request.form.update({'form.widgets.agendas': '23eaca484039416c959a29a1c7509470', 'form.buttons.submit': 'Submit'})

        # request = TestRequest(
        #     form={'form.widgets.agendas': '23eaca484039416c959a29a1c7509470', 'form.buttons.submit': 'Submit'}
        # )

        # alsoProvides(request, IPloneFormLayer)
        # alsoProvides(request, IBringEventIntoAgendasForm)
        # form = BringEventIntoAgendasForm(self.event2, request)
        # form.portal_type = "imio.events.Event"
        # form.update()
        # form.widgets['agendas'].value = "23eaca484039416c959a29a1c7509470"
        # form.update()
        # data, errors = form.extractData()
        # browser.open(f"{self.event2.absolute_url()}/@@bring_event_into_agendas_form")
        # browser.getControl(name="form.buttons.submit").click()
        # response_data = json.loads(browser.contents)
        # # submit_button = form.buttons['submit']
        # # form.request.form.update({'form.widgets.agendas': '23eaca484039416c959a29a1c7509470', 'form.buttons.submit': 'Submit'})
        # # form.portal_type = "imio.events.Event"
        # # form.handle_submit(form, submit_button)
        # # form.handle_submit(submit_button, action='Submit')
