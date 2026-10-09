# -*- coding: utf-8 -*-

from imio.events.core.eguichet import get_category_titles
from imio.events.core.eguichet import get_eguichet_api_settings
from imio.events.core.eguichet import get_event_smartweb_url
from imio.events.core.eguichet import get_text_html
from imio.events.core.eguichet import send_eguichet_notification
from imio.events.core.subscribers import notify_eguichet
from imio.events.core.testing import IMIO_EVENTS_CORE_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.textfield.value import RichTextValue
from unittest.mock import MagicMock
from unittest.mock import patch

import transaction
import unittest

SETTINGS = {
    "url_ts": "https://belleville.guichet-citoyen.be",
    "wcs_api_url": "https://belleville-formulaires.guichet-citoyen.be/api",
    "username": "sw-user",
    "password": "sw-pwd",
    "events_view_url": "https://belleville.staging.imio.be/agenda",
}
CARD_URL = (
    "https://belleville-formulaires.guichet-citoyen.be/api"
    "/formdefs/notifications-depuis-smartweb/submit"
)


def fake_response(status_code=200, json_data=None):
    response = MagicMock(status_code=status_code, text=str(json_data))
    response.json.return_value = json_data
    return response


class TestEguichet(unittest.TestCase):
    layer = IMIO_EVENTS_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.entity = api.content.create(
            container=self.portal,
            type="imio.events.Entity",
            title="Belleville",
            smartweb_site_url="https://belleville.staging.imio.be/",
        )
        self.agenda = api.content.create(
            container=self.entity, type="imio.events.Agenda", title="Agenda"
        )
        self.event = api.content.create(
            container=self.agenda,
            type="imio.events.Event",
            title="Le grand concert d'été",
            category="concert_festival",
            text=RichTextValue("<p>Le <b>concert</b></p>", "text/html", "text/html"),
            description="Un concert",
        )

    @patch("imio.events.core.eguichet.get_sso_auth_header")
    @patch("imio.events.core.eguichet.requests.get")
    def test_get_eguichet_api_settings(self, mock_get, mock_token):
        mock_token.return_value = "Bearer TOKEN"
        mock_get.return_value = fake_response(json_data=SETTINGS)
        settings = get_eguichet_api_settings("https://belleville.staging.imio.be/")
        self.assertEqual(settings, SETTINGS)
        # settings are read on the smartweb site, with the SSO token
        self.assertEqual(
            mock_get.call_args.args[0],
            "https://belleville.staging.imio.be/@eguichet-api-settings",
        )
        headers = mock_get.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer TOKEN")

        # access denied on smartweb: status is logged, no password in logs
        mock_get.return_value = fake_response(status_code=401, json_data={})
        with self.assertLogs("imio.events.core", level="WARNING") as logs:
            self.assertIsNone(
                get_eguichet_api_settings("https://belleville.staging.imio.be")
            )
        self.assertIn("status 401", logs.output[0])

        # no SSO token: smartweb is not called
        mock_get.reset_mock()
        mock_token.return_value = None
        self.assertIsNone(
            get_eguichet_api_settings("https://belleville.staging.imio.be")
        )
        mock_get.assert_not_called()

    def test_get_event_smartweb_url(self):
        site_url = "https://belleville.staging.imio.be/"
        self.assertEqual(
            get_event_smartweb_url(self.event, SETTINGS, site_url),
            "https://belleville.staging.imio.be/agenda/"
            f"le-grand-concert-dete?u={self.event.UID()}",
        )
        # no default events view on the smartweb site: link to the site
        settings = dict(SETTINGS, events_view_url="")
        with self.assertLogs("imio.events.core", level="WARNING"):
            self.assertEqual(
                get_event_smartweb_url(self.event, settings, site_url), site_url
            )

    def test_get_text_html(self):
        self.assertEqual(get_text_html(self.event), "<p>Le <b>concert</b></p>")
        self.event.text = None
        self.assertEqual(get_text_html(self.event), "")

    def test_get_category_titles(self):
        # the French title, not the term id
        self.assertEqual(get_category_titles(self.event), ["Concert et festival"])
        # no category: empty list, not [""]
        self.event.category = None
        self.assertEqual(get_category_titles(self.event), [])
        # unknown term
        self.event.category = "unknown"
        self.assertEqual(get_category_titles(self.event), [])

    @patch("imio.events.core.eguichet.get_eguichet_api_settings")
    @patch("imio.events.core.eguichet.requests.post")
    def test_send_eguichet_notification(self, mock_post, mock_settings):
        mock_settings.return_value = SETTINGS
        mock_post.return_value = fake_response(json_data={"err": 0, "data": {"id": 5}})
        with self.assertLogs("imio.events.core", level="INFO") as logs:
            self.assertTrue(send_eguichet_notification(self.event))
        mock_settings.assert_called_once_with("https://belleville.staging.imio.be/")
        # card id is logged, the password is never logged
        self.assertIn("Card 5 created", logs.output[-1])
        self.assertNotIn("sw-pwd", "".join(logs.output))

        # card is posted on w.c.s., with the e-guichet API credentials
        self.assertEqual(mock_post.call_args.args[0], CARD_URL)
        self.assertEqual(mock_post.call_args.kwargs["auth"], ("sw-user", "sw-pwd"))
        self.assertEqual(
            mock_post.call_args.kwargs["json"],
            {
                "data": {
                    "sujet": "Le grand concert d'été",
                    "corps": "<p>Le <b>concert</b></p>",
                    "url_de_redirection": (
                        "https://belleville.staging.imio.be/agenda/"
                        f"le-grand-concert-dete?u={self.event.UID()}"
                    ),
                    "notifications_evenements": ["Concert et festival"],
                }
            },
        )

        # w.c.s. error
        mock_post.return_value = fake_response(json_data={"err": 1})
        with self.assertLogs("imio.events.core", level="WARNING") as logs:
            self.assertFalse(send_eguichet_notification(self.event))
        self.assertIn("Card not created", logs.output[0])

        # w.c.s. answers JSON that is not a dict
        mock_post.return_value = fake_response(json_data=["unexpected"])
        with self.assertLogs("imio.events.core", level="WARNING") as logs:
            self.assertFalse(send_eguichet_notification(self.event))
        self.assertIn("Card not created", logs.output[0])

        # no settings (smartweb site down, access denied, ...)
        mock_post.reset_mock()
        mock_settings.return_value = None
        self.assertFalse(send_eguichet_notification(self.event))
        mock_post.assert_not_called()

        # no smartweb site on the entity
        mock_settings.reset_mock()
        self.entity.smartweb_site_url = None
        self.assertFalse(send_eguichet_notification(self.event))
        mock_settings.assert_not_called()

    def test_published_event_transition(self):
        def eguichet_hooks():
            return [
                hook
                for hook, args, kws in transaction.get().getAfterCommitHooks()
                if hook is notify_eguichet
            ]

        api.content.transition(self.event, "publish")
        self.assertEqual(len(eguichet_hooks()), 1)
        # other transitions do not notify
        api.content.transition(self.event, "retract")
        self.assertEqual(len(eguichet_hooks()), 1)

    @patch("imio.events.core.subscribers.send_eguichet_notification")
    def test_notify_eguichet(self, mock_send):
        notify_eguichet(False, obj=self.event)
        mock_send.assert_not_called()
        notify_eguichet(True, obj=self.event)
        mock_send.assert_called_once_with(self.event)
