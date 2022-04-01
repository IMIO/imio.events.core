# -*- coding: utf-8 -*-

from imio.smartweb.common.interfaces import ILocalManagerAware
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import schema
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class IEntity(model.Schema):
    """Marker interface and Dexterity Python Schema for Entity"""

    directives.widget(zip_codes=SelectFieldWidget)
    zip_codes = schema.List(
        title=_("Zip codes and cities"),
        description=_("Choose zip codes for this entity"),
        value_type=schema.Choice(vocabulary="imio.smartweb.vocabulary.Cities"),
    )

    model.fieldset("categorization", fields=["local_categories"])
    local_categories = schema.Text(
        title=_("Specific events categories"),
        description=_(
            "List of events categories values available for this entity (one per line)"
        ),
        required=False,
    )


@implementer(IEntity, ILocalManagerAware)
class Entity(Container):
    """Entity content type"""
