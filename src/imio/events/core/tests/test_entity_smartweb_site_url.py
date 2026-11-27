# -*- coding: utf-8 -*-

from imio.events.core.contents.entity.content import IEntity
from imio.events.core.testing import IMIO_EVENTS_CORE_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.autoform.interfaces import READ_PERMISSIONS_KEY
from plone.autoform.interfaces import WRITE_PERMISSIONS_KEY
from plone.restapi.interfaces import IDeserializeFromJson
from plone.restapi.interfaces import ISerializeToJson
from plone.supermodel.utils import mergedTaggedValueDict
from plone.testing.zope import Browser
from urllib.parse import urlencode
from zope.component import getMultiAdapter
from zope.interface import Invalid
from zope.schema import TextLine

import transaction
import unittest

PASSWORD = "secret-password"
GEMBLOUX = "https://www.gembloux.be"
WIDGET = "form.widgets.smartweb_site_url"


class TestEntitySmartwebSiteUrl(unittest.TestCase):
    """The URL of the public SmartWeb site of an entity: optional, for everyone to read, for Managers to change."""

    layer = IMIO_EVENTS_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="Gembloux",
            zip_codes=["5030"],
        )
        # Each user holds one role, where it applies: none of them is Manager through another way.
        self.users = {
            "Manager": self._user("manager", roles=["Manager"]),
            "Site Administrator": self._user("siteadmin", roles=["Site Administrator"]),
            "Editor": self._user("editor", local_roles=["Editor"]),
            "Contributor": self._user("contributor", local_roles=["Contributor"]),
            "Owner": self._user("owner", local_roles=["Owner"]),
        }
        setRoles(self.portal, TEST_USER_ID, [])
        transaction.commit()

    def _user(self, username, roles=(), local_roles=()):
        api.user.create(
            email=f"{username}@example.org",
            username=username,
            password=PASSWORD,
            roles=roles,
        )
        if local_roles:
            api.user.grant_roles(
                username=username, obj=self.entity, roles=list(local_roles)
            )
        return username

    def _browser(self, role):
        browser = Browser(self.layer["app"])
        browser.handleErrors = False
        browser.addHeader("Authorization", f"Basic {self.users[role]}:{PASSWORD}")
        return browser

    def test_field_is_an_optional_text_line(self):
        field = IEntity["smartweb_site_url"]
        self.assertEqual(
            (type(field), field.required, field.default), (TextLine, False, None)
        )

    def test_an_existing_entity_has_no_url(self):
        self.assertIsNone(self.entity.smartweb_site_url)

    def test_accepts_http_and_https_urls_with_or_without_a_final_slash(self):
        field = IEntity["smartweb_site_url"]
        for url in (
            GEMBLOUX,
            f"{GEMBLOUX}/",
            "http://www.gembloux.be",
            "https://www.gembloux.be/fr",
        ):
            with self.subTest(url=url):
                field.validate(url)

    def test_refuses_what_is_not_the_url_of_a_website(self):
        field = IEntity["smartweb_site_url"]
        for url in (
            "www.gembloux.be",
            "ftp://www.gembloux.be",
            "javascript:alert(1)",
            "https://",
            "https://user:password@www.gembloux.be",
            "https://www.gembloux.be/a page",
            "https://www.gembloux.be/?q=1",
            "https://www.gembloux.be/#top",
        ):
            with self.subTest(url=url):
                with self.assertRaises(Invalid):
                    field.validate(url)

    def test_a_manager_sees_the_field_in_the_add_form(self):
        browser = self._browser("Manager")
        browser.open(f"{self.portal.absolute_url()}/++add++imio.events.Entity")
        self.assertIn(WIDGET, browser.contents)

    def test_a_manager_changes_the_url_in_the_edit_form_and_reads_it(self):
        browser = self._browser("Manager")
        browser.open(f"{self.entity.absolute_url()}/@@edit")
        browser.getControl(name=WIDGET).value = GEMBLOUX
        browser.getControl(name="form.buttons.save").click()
        self.assertEqual(self.portal["gembloux"].smartweb_site_url, GEMBLOUX)
        browser.open(f"{self.entity.absolute_url()}/@@edit")
        self.assertEqual(browser.getControl(name=WIDGET).value, GEMBLOUX)

    def test_other_roles_do_not_see_the_field_in_the_edit_form(self):
        for role in ("Site Administrator", "Editor", "Owner"):
            with self.subTest(role=role):
                browser = self._browser(role)
                browser.open(f"{self.entity.absolute_url()}/@@edit")
                # They edit the entity, but not its SmartWeb site.
                self.assertIn("form.widgets.IBasic.title", browser.contents)
                self.assertNotIn(WIDGET, browser.contents)
                # Cancel releases the lock the edit form takes, which would turn the next user away.
                browser.getControl(name="form.buttons.cancel").click()

    def test_a_contributor_does_not_get_the_edit_form(self):
        browser = self._browser("Contributor")
        browser.handleErrors = True
        browser.open(f"{self.entity.absolute_url()}/@@edit")
        self.assertNotIn("form.widgets.IBasic.title", browser.contents)
        self.assertNotIn(WIDGET, browser.contents)

    def test_a_forged_edit_form_does_not_change_the_url(self):
        self.entity.smartweb_site_url = GEMBLOUX
        transaction.commit()
        for role in ("Site Administrator", "Editor", "Owner"):
            with self.subTest(role=role):
                browser = self._browser(role)
                browser.open(f"{self.entity.absolute_url()}/@@edit")
                authenticator = (
                    browser.getForm(id="form").getControl(name="_authenticator").value
                )
                browser.post(
                    f"{self.entity.absolute_url()}/@@edit",
                    urlencode(
                        {
                            "_authenticator": authenticator,
                            "form.widgets.IBasic.title": f"Gembloux, by {role}",
                            "form.widgets.zip_codes:list": "5030",
                            WIDGET: "https://evil.example",
                            "form.buttons.save": "Save",
                        }
                    ),
                )
                entity = self.portal["gembloux"]
                self.assertEqual(
                    (entity.title, entity.smartweb_site_url),
                    (f"Gembloux, by {role}", GEMBLOUX),
                )

    def test_the_rest_api_ignores_the_url_from_other_roles(self):
        self.entity.smartweb_site_url = GEMBLOUX
        for role in ("Site Administrator", "Editor", "Contributor", "Owner"):
            with self.subTest(role=role):
                with api.env.adopt_user(username=self.users[role]):
                    self._deserialize({"smartweb_site_url": "https://evil.example"})
                self.assertEqual(self.entity.smartweb_site_url, GEMBLOUX)

    def test_the_rest_api_takes_the_url_from_a_manager(self):
        with api.env.adopt_user(username=self.users["Manager"]):
            self._deserialize({"smartweb_site_url": GEMBLOUX})
        self.assertEqual(self.entity.smartweb_site_url, GEMBLOUX)

    def test_anyone_reads_the_url_through_the_rest_api(self):
        self.entity.smartweb_site_url = GEMBLOUX
        with api.env.adopt_roles(["Anonymous"]):
            serialized = getMultiAdapter(
                (self.entity, self.request), ISerializeToJson
            )()
        self.assertEqual(serialized["smartweb_site_url"], GEMBLOUX)

    def test_only_this_field_changes_the_permissions_of_the_entity(self):
        self.assertEqual(
            (
                mergedTaggedValueDict(IEntity, READ_PERMISSIONS_KEY),
                mergedTaggedValueDict(IEntity, WRITE_PERMISSIONS_KEY),
            ),
            (
                {
                    "authorize_to_bring_event_anywhere": "imio.events.core.BringEventIntoPersonnalAgenda"
                },
                {
                    "authorize_to_bring_event_anywhere": "imio.events.core.BringEventIntoPersonnalAgenda",
                    "smartweb_site_url": "cmf.ManagePortal",
                },
            ),
        )

    def _deserialize(self, data):
        deserializer = getMultiAdapter(
            (self.entity, self.request), IDeserializeFromJson
        )
        deserializer(data=data)
