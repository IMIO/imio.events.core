# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from imio.events.core.contents import IEntity
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.app.layout.navigation.interfaces import INavigationRoot
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class EventsCategoriesVocabularyFactory:
    def __call__(self, context=None):
        values = [
            (u"stroll_discovery", _(u"Stroll and discovery")),
            (u"flea_market_market", _(u"Flea market and market")),
            (u"concert_festival", _(u"Concert and festival")),
            (u"conference_debate", _(u"Conference and debate")),
            (u"exhibition_artistic_meeting", _(u"Exhibition and artistic meeting")),
            (u"party_folklore", _(u"Party and folklore")),
            (u"projection_cinema", _(u"Projection and cinema")),
            (u"trade_fair_fair", _(u"Trade Fair and Fair")),
            (u"internships_courses", _(u"Internships and courses")),
            (u"theater_show", _(u"Theater and show")),
        ]
        terms = [SimpleTerm(value=t[0], token=t[0], title=t[1]) for t in values]
        return SimpleVocabulary(terms)


EventsCategoriesVocabulary = EventsCategoriesVocabularyFactory()


class EventsLocalCategoriesVocabularyFactory:
    def __call__(self, context=None):
        obj = context
        while not IEntity.providedBy(obj):
            obj = aq_parent(aq_inner(obj))
        if not obj.local_categories:
            return SimpleVocabulary([])

        values = obj.local_categories.splitlines()
        terms = [SimpleTerm(value=t, token=t, title=t) for t in values]
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
        search_context = api.portal.get()
        obj = context
        while not INavigationRoot.providedBy(obj):
            if IEntity.providedBy(obj):
                search_context = obj
                break
            parent = aq_parent(aq_inner(obj))
            obj = parent
        brains = api.content.find(
            search_context,
            portal_type="imio.events.Agenda",
            sort_on="sortable_title",
        )
        terms = [SimpleTerm(value=b.UID, token=b.UID, title=b.Title) for b in brains]
        return SimpleVocabulary(terms)


AgendasUIDsVocabulary = AgendasUIDsVocabularyFactory()
