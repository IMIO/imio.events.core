# -*- coding: utf-8 -*-

from AccessControl import Unauthorized
from imio.events.core.contents import IAgenda
from imio.events.core.contents import IEntity
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.memoize import ram
from Products.CMFPlone.interfaces.siteroot import IPloneSiteRoot
from Products.CMFPlone.utils import parent
from zope.component import getUtility
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
