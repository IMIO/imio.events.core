# -*- coding: utf-8 -*-

from collective.geolocationbehavior.geolocation import IGeolocatable
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.content import Container
from plone.supermodel import model
from plone.supermodel.interfaces import FIELDSETS_KEY
from plone.supermodel.model import Fieldset
from zope import schema
from zope.interface import implementer


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

    model.fieldset("categorization", fields=["category"])
    category = schema.Choice(
        title=_(u"Category"),
        description=_(
            u"Important! These categories are used to supplement the information provided by the topics"
        ),
        source="imio.events.vocabulary.EventsCategories",
        required=False,
    )


@implementer(IEvent)
class Event(Container):
    """Event class"""
