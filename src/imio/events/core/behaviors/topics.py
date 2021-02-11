# -*- coding: utf-8 -*-

from imio.events.core import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from zope import schema
from zope.interface import provider


@provider(IFormFieldProvider)
class ITopics(model.Schema):
    """"""

    model.fieldset("categorization", label=_(u"Categorization"), fields=["topics"])
    topics = schema.List(
        title=_(u"Topics"),
        required=False,
        value_type=schema.Choice(vocabulary=u"collective.taxonomy.topics"),
    )
