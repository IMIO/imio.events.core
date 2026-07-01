# -*- coding: utf-8 -*-

from collective.taxonomy.interfaces import ITaxonomy
from AccessControl import Unauthorized
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.smartweb.common.config import DIRECTORY_URL
from imio.smartweb.common.utils import get_json
from imio.smartweb.common.utils import get_parent_providing
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.memoize import ram
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import parent
from zope.component import getSiteManager
from zope.component import getUtility
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import provider

import time

ENABLE_CACHE = True


def _cache_key(func, context):
    user = api.user.get_current()
    return f"user_{user.getId()}_{int(time.time() / 10)}"  # Changes every 30s


class EventsCategoriesVocabularyFactory:
    def __call__(self, context=None):
        values = [
            ("stroll_discovery", _("Stroll and discovery")),
            ("flea_market_market", _("Flea market and market")),
            ("concert_festival", _("Concert and festival")),
            ("conference_debate", _("Conference and debate")),
            ("exhibition_artistic_meeting", _("Exhibition and artistic meeting")),
            ("party_folklore", _("Party and folklore")),
            ("projection_cinema", _("Projection and cinema")),
            ("trade_fair_fair", _("Trade Fair and Fair")),
            ("internships_courses", _("Internships and courses")),
            ("theater_show", _("Theater and show")),
        ]
        terms = [SimpleTerm(value=t[0], token=t[0], title=t[1]) for t in values]
        return SimpleVocabulary(terms)


EventsCategoriesVocabulary = EventsCategoriesVocabularyFactory()


class EventsCategoriesDeVocabularyFactory:
    def __call__(self, context=None):
        vocabulary = EventsCategoriesVocabularyFactory()(context)
        translated_terms = [
            SimpleTerm(
                value=term.value,
                token=term.token,
                title=translate(term.title, target_language="de"),
            )
            for term in vocabulary
        ]
        return SimpleVocabulary(translated_terms)


EventsCategoriesDeVocabulary = EventsCategoriesDeVocabularyFactory()


class EventsLocalCategoriesVocabularyFactory:
    def __call__(self, context=None, lang="fr"):
        if IPloneSiteRoot.providedBy(context):
            # ex: call on @types or @vocabularies from RESTAPI
            return SimpleVocabulary([])
        obj = context
        while not IEntity.providedBy(obj) and obj is not None:
            obj = parent(obj)
        if not obj.local_categories:
            return SimpleVocabulary([])

        values = {cat["fr"]: cat[lang] or cat["fr"] for cat in obj.local_categories}
        terms = [SimpleTerm(value=k, token=k, title=v) for k, v in values.items()]
        return SimpleVocabulary(terms)


EventsLocalCategoriesVocabulary = EventsLocalCategoriesVocabularyFactory()


class EventsLocalCategoriesDeVocabularyFactory:
    def __call__(self, context=None, lang="fr"):
        vocabulary = EventsLocalCategoriesVocabularyFactory()(context)
        translated_terms = [
            SimpleTerm(
                value=term.value,
                token=term.token,
                title=translate(term.title, target_language="de"),
            )
            for term in vocabulary
        ]
        return SimpleVocabulary(translated_terms)


EventsLocalCategoriesDeVocabulary = EventsLocalCategoriesDeVocabularyFactory()


class EventsCategoriesAndTopicsVocabularyFactory:
    def __call__(self, context=None):
        events_categories_factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsCategories"
        )

        events_local_categories_factory = getUtility(
            IVocabularyFactory, "imio.events.vocabulary.EventsLocalCategories"
        )

        topics_factory = getUtility(
            IVocabularyFactory, "imio.smartweb.vocabulary.Topics"
        )

        terms = []

        for term in events_categories_factory(context):
            terms.append(
                SimpleTerm(
                    value=term.value,
                    token=term.token,
                    title=term.title,
                )
            )

        for term in events_local_categories_factory(context):
            terms.append(
                SimpleTerm(
                    value=term.value,
                    token=term.token,
                    title=term.title,
                )
            )

        for term in topics_factory(context):
            terms.append(
                SimpleTerm(
                    value=term.value,
                    token=term.token,
                    title=term.title,
                )
            )

        return SimpleVocabulary(terms)


EventsCategoriesAndTopicsVocabulary = EventsCategoriesAndTopicsVocabularyFactory()


class AgendasUIDsVocabularyFactory:
    def __call__(self, context=None):
        portal = api.portal.get()
        brains = api.content.find(
            context=portal,
            portal_type="imio.events.Agenda",
            sort_on="breadcrumb",
        )
        terms = [
            SimpleTerm(value=b.UID, token=b.UID, title=b.breadcrumb) for b in brains
        ]
        return SimpleVocabulary(terms)


AgendasUIDsVocabulary = AgendasUIDsVocabularyFactory()


class EventTypesVocabularyFactory:
    def __call__(self, context=None):
        event_types = [
            (
                "event-driven",
                _(
                    "Event-driven (festivity, play, conference, flea market, walk, etc.)"
                ),
            ),
            (
                "activity",
                _("Activity (extracurricular, sport, workshop and course, etc.)"),
            ),
        ]
        terms = [SimpleTerm(value=t[0], token=t[0], title=t[1]) for t in event_types]
        return SimpleVocabulary(terms)


EventTypesVocabulary = EventTypesVocabularyFactory()


class EventTypesDeVocabularyFactory:
    def __call__(self, context=None):
        vocabulary = EventTypesVocabularyFactory()(context)
        translated_terms = [
            SimpleTerm(
                value=term.value,
                token=term.token,
                title=translate(term.title, target_language="de"),
            )
            for term in vocabulary
        ]
        return SimpleVocabulary(translated_terms)


EventTypesDeVocabulary = EventTypesDeVocabularyFactory()


@provider(IVocabularyFactory)
class UserAgendasVocabularyFactory:

    if ENABLE_CACHE is True:

        def __call__(self, context=None):
            return self.call(context)

    else:

        @ram.cache(_cache_key)
        def __call__(self, context=None):
            return self.call(context)

    def call(self, context=None):
        site = api.portal.get()
        user = site.portal_membership.getAuthenticatedMember()
        permission = "imio.events.core: Add Event"
        # Get search query from request
        request = api.portal.getRequest()
        search_query = request.form.get("query", "").lower() if request else ""
        terms = []

        brains = api.content.find(object_provides=[IAgenda])
        for brain in brains:
            try:
                title = brain.breadcrumb.lower()
                if not search_query or search_query in title:
                    obj = brain.getObject()
                    if user.has_permission(permission, obj):
                        terms.append(
                            SimpleTerm(
                                value=brain.UID, token=brain.UID, title=brain.breadcrumb
                            )
                        )
            except Unauthorized:
                pass
        sorted_terms = sorted(terms, key=lambda x: x.title)
        return SimpleVocabulary(sorted_terms)


UserAgendasVocabulary = UserAgendasVocabularyFactory()


class EventPublicDeVocabularyFactory:
    def __call__(self, context=None):
        sm = getSiteManager()
        event_public_taxo = sm.queryUtility(
            ITaxonomy, name="collective.taxonomy.event_public"
        )
        if not event_public_taxo:
            return SimpleVocabulary([])
        categories_voca = event_public_taxo.makeVocabulary("de").inv_data
        terms = [
            SimpleTerm(value=k, token=k, title=v) for k, v in categories_voca.items()
        ]
        return SimpleVocabulary(terms)


EventPublicDeVocabulary = EventPublicDeVocabularyFactory()


class RemoteDirectoryContactVocabularyFactory:
    # Cache key MUST depend on the entity: a single global (time-only) key let
    # one call's result be served to every other event's form. In particular a
    # call without an IEntity ancestor (RESTAPI @types/@vocabularies, an add
    # form, a widget resolved at the site root) computed an empty vocabulary and
    # poisoned the cache for everyone for up to 60s, so sponsors/contacts came
    # up empty intermittently even while editing. The None/empty cases are now
    # handled in __call__ and are never cached.
    @ram.cache(
        lambda method, self, entity_uid, directory_entities: "{}-{}-{}".format(
            entity_uid, directory_entities, time.time() // 60
        )
    )
    def _fetch(self, entity_uid, directory_entities):
        params = [
            "portal_type=imio.directory.Contact",
            "sort_on=breadcrumb",
            "b_size=100000",
            "metadata_fields=UID",
            "metadata_fields=breadcrumb",
        ]
        params.extend("selected_entities={}".format(uid) for uid in directory_entities)
        url = "{}/@search?{}".format(DIRECTORY_URL, "&".join(params))
        json_contacts = get_json(url, None, 12)
        if json_contacts is None or len(json_contacts.get("items", [])) == 0:
            return SimpleVocabulary([])
        return SimpleVocabulary(
            [
                SimpleTerm(value=elem["UID"], title=elem["breadcrumb"])
                for elem in json_contacts.get("items")
            ]
        )

    def __call__(self, context=None):
        parent_entity = get_parent_providing(context, IEntity)
        if parent_entity is None:
            # No IEntity ancestor: e.g. RESTAPI @types/@vocabularies
            # introspection, an add form before the object exists, or a widget
            # whose vocabulary is resolved at the site root. Return empty
            # WITHOUT caching so a later call with a real context still builds
            # the actual vocabulary.
            return SimpleVocabulary([])
        directory_entities = parent_entity.directory_linked_entities or []
        if not directory_entities:
            return SimpleVocabulary([])
        # tuple(sorted(...)) → stable, hashable component for the cache key.
        return self._fetch(parent_entity.UID(), tuple(sorted(directory_entities)))


RemoteDirectoryContactVocabulary = RemoteDirectoryContactVocabularyFactory()
