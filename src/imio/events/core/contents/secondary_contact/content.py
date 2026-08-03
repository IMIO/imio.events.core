# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.rows import IContactInformationsGrids
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.z3cform.widget import SelectFieldWidget
from plone.autoform import directives
from plone.dexterity.content import Item
from zope import schema
from zope.interface import implementer


class ISecondaryContact(IContactInformationsGrids):
    """Marker interface and Dexterity Python Schema for SecondaryContact

    One object references ONE directory contact. Several of them can be added
    to an Event: the multiplicity is the number of objects, not a multi-valued
    field. That keeps `title` meaningful -- it labels one contact, e.g.
    "Reservations" -- and the REST payload unambiguous.

    The three inherited datagrids hold a SNAPSHOT of the contact's phones,
    e-mails and urls. Unlike imio.smartweb.core's Section contact, where the
    stored data columns are residue and the render re-reads the directory, here
    they ARE the published data: an event has a temporality and must show the
    contact as it was for that event.
    """

    # Declared here rather than through plone.basic, which would make the title
    # required and also expose a description field. plone.namefromtitle derives
    # the id when a title is given and falls back to the portal type when not.
    title = schema.TextLine(
        title=_("Title"),
        required=False,
    )

    directives.widget(
        "related_contact",
        SelectFieldWidget,
        vocabulary="imio.events.vocabulary.RemoteDirectoryContact",
    )
    related_contact = schema.Choice(
        title=_("Contact"),
        description=_(
            "You can retrieve information from a contact record that already "
            "exists in your directory"
        ),
        source="imio.events.vocabulary.RemoteDirectoryContact",
        required=True,
    )


@implementer(ISecondaryContact)
class SecondaryContact(Item):
    """SecondaryContact class"""
