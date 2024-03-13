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

    directives.read_permission(
        authorize_to_bring_event_anywhere="imio.events.core.BringEventIntoPersonnalAgenda"
    )
    directives.write_permission(
        authorize_to_bring_event_anywhere="imio.events.core.BringEventIntoPersonnalAgenda"
    )
    authorize_to_bring_event_anywhere = schema.Bool(
        title=_("Authorize to bring event anywhere"),
        description=_(
            "If selected, contributor of this entity can bring event in any agenda independently of agenda subscribing feature"
        ),
        required=False,
        default=False,
    )


@implementer(IEntity, ILocalManagerAware)
class Entity(Container):
    """Entity content type"""
