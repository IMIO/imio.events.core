# -*- coding: utf-8 -*-

from collective.geolocationbehavior.geolocation import IGeolocatable
from imio.events.core.utils import get_agenda_uid_for_event
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.autoform.directives import read_permission
from plone.autoform.directives import write_permission
from plone.dexterity.content import Container
from plone.supermodel import model
from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.supermodel.model import Fieldset
from zope import schema
from zope.interface import implementer
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


class IAddress(model.Schema):

    model.fieldset(
        "address",
        label=_(u"Address"),
        fields=["street", "number", "complement", "zipcode", "city", "country"],
    )
    street = schema.TextLine(title=_(u"Street"), required=False)
    number = schema.TextLine(title=_(u"Number"), required=False)
    complement = schema.TextLine(title=_(u"Complement"), required=False)
    zipcode = schema.Int(title=_(u"Zipcode"), required=False)
    city = schema.TextLine(title=_(u"City"), required=False)
    country = schema.Choice(
        title=_(u"Country"),
        source="imio.smartweb.vocabulary.Countries",
        default="be",
        required=False,
    )


# Move geolocation field to our Address fieldset
address_fieldset = Fieldset(
    "address",
    fields=["geolocation"],
)
IGeolocatable.setTaggedValue(FIELDSETS_KEY, [address_fieldset])


@provider(IContextAwareDefaultFactory)
def get_current_agenda_UID(context):
    return [get_agenda_uid_for_event(context)]


class IEvent(IAddress):
    """Marker interface and Dexterity Python Schema for Event"""

    video_url = schema.URI(
        title=_(u"Video url"),
        description=_(u"Video url from youtube, vimeo"),
        required=False,
    )

    ticket_url = schema.URI(
        title=_(u"Ticket url"),
        description=_(u"Ticket url to subscribe to this event"),
        required=False,
    )

    facebook = schema.URI(
        title=_(u"Facebook"),
        description=_(u"Facebook url for this event"),
        required=False,
    )

    twitter = schema.URI(
        title=_(u"Twitter"),
        description=_(u"Twitter url for this event"),
        required=False,
    )

    instagram = schema.URI(
        title=_(u"Instagram"),
        description=_(u"Instagram url for this event"),
        required=False,
    )

    free_entry = schema.Bool(
        title=_(u"Free entry"),
        description=_(u"Check if entry is free"),
        required=False,
        default=False,
    )

    online_participation = schema.URI(
        title=_(u"Online participation url"),
        description=_(u"Link to online participation"),
        required=False,
    )

    reduced_mobility_facilities = schema.Bool(
        title=_(u"Facilities for person with reduced mobility"),
        description=_(u"Check if there is facilities for person with reduced mobility"),
        required=False,
        default=False,
    )

    model.fieldset(
        "categorization", fields=["selected_agendas", "category", "local_category"]
    )
    directives.widget(selected_agendas=SelectFieldWidget)
    selected_agendas = schema.List(
        title=_(u"Selected agendas"),
        description=_(
            u"Select agendas where this event will be displayed. Current agenda is always selected."
        ),
        value_type=schema.Choice(vocabulary="imio.events.vocabulary.AgendasUIDs"),
        default=[],
        required=False,
    )

    category = schema.Choice(
        title=_(u"Category"),
        description=_(
            u"Important! These categories are used to supplement the information provided by the topics"
        ),
        source="imio.events.vocabulary.EventsCategories",
        required=False,
    )

    local_category = schema.Choice(
        title=_(u"Specific category"),
        description=_(
            u"Important! These categories allow you to use criteria that are specific to your organization"
        ),
        source="imio.events.vocabulary.EventsLocalCategories",
        required=False,
    )

    event_type = schema.Choice(
        title=_(u"Event type"),
        source="imio.events.vocabulary.EventTypes",
        required=False,
    )

    read_permission(selected_agendas="imio.events.core.AddEntity")
    write_permission(selected_agendas="imio.events.core.AddEntity")


@implementer(IEvent)
class Event(Container):
    """Event class"""
