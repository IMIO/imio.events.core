# -*- coding: utf-8 -*-

from Acquisition import aq_inner
from Acquisition import aq_parent
from imio.events.core.contents import IEntity
from imio.smartweb.locales import SmartwebMessageFactory as _
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


class EventsCategoriesVocabularyFactory:
    def __call__(self, context=None):
        values = [
            (u"stroll_discovery", _(u"Stroll & discovery")),
            (u"flea_market_market", _(u"Flea market & market")),
            (u"concert_festival", _(u"Concert & festival")),
            (u"conference_debate", _(u"Conference & debate")),
            (u"exhibit", _(u"Exhibit")),
            (u"movie", _(u"Movie")),
            (u"party_folklore", _(u"Party & folklore")),
            (u"trade_fair_fair", _(u"Trade Fair & Fair")),
            (u"internships_courses", _(u"Internships & courses")),
            (u"theater_show", _(u"Theater & show")),
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

        values = obj.local_categories.split("\n")
        terms = [SimpleTerm(value=t, token=t, title=t) for t in values]
        return SimpleVocabulary(terms)


EventsLocalCategoriesVocabulary = EventsLocalCategoriesVocabularyFactory()
