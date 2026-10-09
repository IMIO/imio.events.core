# -*- coding: utf-8 -*-

from imio.events.core.utils import get_entity_for_obj
from imio.smartweb.common.sso import get_sso_auth_header
from imio.smartweb.common.utils import is_log_active
from imio.smartweb.common.utils import translate_vocabulary_term
from plone.i18n.normalizer import idnormalizer

import logging
import requests

logger = logging.getLogger("imio.events.core")

# Card model (w.c.s.) that sends a WEBPUSH notification for each new card.
NOTIFICATION_CARD_SLUG = "notifications-depuis-smartweb"

# Prefix of all log messages, to filter them easily.
LOG_PREFIX = "[eguichet]"


def get_category_titles(obj):
    """Return the French title of the event category (not the term id), in
    a list (e-guichet field format), or [] if the event has no category.
    E-guichet texts are in French."""
    if not obj.category:
        return []
    try:
        title = translate_vocabulary_term(
            "imio.events.vocabulary.EventsCategories", obj.category, "fr"
        )
    except LookupError:
        # Term not in the vocabulary anymore: send the notification anyway.
        logger.warning(f"{LOG_PREFIX} Unknown category {obj.category} on {obj.UID()}")
        return []
    return [title] if title else []


def get_text_html(obj):
    """Return the HTML of the event rich text, or "" if it is empty.
    Relative links (resolveuid) become absolute links."""
    text = getattr(obj, "text", None)
    if not text:
        return ""
    return text.output_relative_to(obj) or ""


def get_event_smartweb_url(obj, settings, site_url):
    """Return the url of the event on the smartweb site:
    <default events view url>/<slug of event title>?u=<event UID>.
    Without default events view on the smartweb site: the site url."""
    view_url = settings.get("events_view_url")
    if not view_url:
        logger.warning(
            f"{LOG_PREFIX} No default events view (smartweb.default_events_view) "
            f"on {site_url}: the notification links to the site"
        )
        return site_url
    # Same slug as the smartweb links (rest/authentic_sources.py in
    # imio.smartweb.core). Event ids are UIDs: they are not readable.
    slug = idnormalizer.normalize(obj.title, locale="fr")
    return f"{view_url.rstrip('/')}/{slug}?u={obj.UID()}"


def get_eguichet_api_settings(site_url):
    """Read the e-guichet API settings of a smartweb site
    (endpoint ``@eguichet-api-settings`` in imio.smartweb.core).
    Return None on error. Never log the password."""
    token = get_sso_auth_header()
    if token is None:
        return None
    url = f"{site_url.rstrip('/')}/@eguichet-api-settings"
    if is_log_active():
        logger.info(f"{LOG_PREFIX} Read e-guichet API settings from {url}")
    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json", "Authorization": token},
            timeout=10,
        )
    except requests.exceptions.Timeout:
        logger.warning(f"{LOG_PREFIX} Timeout when reading {url}")
        return None
    except Exception:
        logger.exception(f"{LOG_PREFIX} Can not read {url}")
        return None
    if response.status_code != 200:
        # 401: SSO token refused or missing role on smartweb.
        # 404: smartweb site without the @eguichet-api-settings endpoint.
        logger.warning(
            f"{LOG_PREFIX} Can not read {url} : status {response.status_code}"
        )
        return None
    try:
        settings = response.json()
    except ValueError:
        logger.warning(f"{LOG_PREFIX} Response of {url} is not JSON")
        return None
    if is_log_active():
        logger.info(
            f"{LOG_PREFIX} Settings from {site_url} : "
            f"url_ts={settings.get('url_ts')}, "
            f"wcs_api_url={settings.get('wcs_api_url')}, "
            f"username={settings.get('username')}"
        )
    return settings


def send_eguichet_notification(obj):
    """Create a card in the e-guichet of the smartweb site linked to the event
    entity. The card model sends a WEBPUSH notification about the new event.
    Errors are logged: they never stop the publication."""
    entity = get_entity_for_obj(obj)
    site_url = getattr(entity, "smartweb_site_url", None)
    if not site_url:
        # Normal case: the entity is not linked to a smartweb site.
        if is_log_active():
            logger.info(
                f"{LOG_PREFIX} No smartweb site on entity {entity and entity.UID()}: "
                f"no notification for event {obj.UID()}"
            )
        return False
    if is_log_active():
        logger.info(
            f"{LOG_PREFIX} Notification for event {obj.UID()} "
            f"({obj.absolute_url()}) to smartweb site {site_url}"
        )
    settings = get_eguichet_api_settings(site_url)
    if not settings:
        return False
    if not settings.get("wcs_api_url"):
        logger.warning(
            f"{LOG_PREFIX} No e-guichet url (smartweb.url_ts) on {site_url}: "
            f"no notification for event {obj.UID()}"
        )
        return False
    # !! formdefs instead of cards. So, we create a form and not a card.
    url = f"{settings['wcs_api_url']}/formdefs/{NOTIFICATION_CARD_SLUG}/submit"
    data = {
        "data": {
            "sujet": obj.title,
            "corps": get_text_html(obj),
            "url_de_redirection": get_event_smartweb_url(obj, settings, site_url),
            "notifications_evenements": get_category_titles(obj),
        }
    }
    if is_log_active():
        logger.info(f"{LOG_PREFIX} Send card for event {obj.UID()} to {url}")
    # HERE : SEND WEBPUSH NOTIFICATIONS THANK TO E-GUICHET
    try:
        response = requests.post(
            url,
            json=data,
            auth=(settings.get("username"), settings.get("password")),
            headers={"Accept": "application/json"},
            timeout=10,
        )
    except Exception:
        logger.exception(
            f"{LOG_PREFIX} Can not send card for event {obj.UID()} to {url}"
        )
        return False
    # w.c.s. answers {"err": 0, "data": {"id": ...}} when the card is created
    try:
        result = response.json()
    except ValueError:
        result = {}
    if not isinstance(result, dict):
        result = {}
    if response.status_code != 200 or result.get("err") != 0:
        logger.warning(
            f"{LOG_PREFIX} Card not created for event {obj.UID()} on {url} : "
            f"status {response.status_code} {response.text[:200]}"
        )
        return False
    logger.info(
        f"{LOG_PREFIX} Card {(result.get('data') or {}).get('id')} created "
        f"for event {obj.UID()} on {url}"
    )
    return True
