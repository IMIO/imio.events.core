# -*- coding: utf-8 -*-

from imio.smartweb.common.contact.forms import ContactInformationsGridMixin
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.browser.add import DefaultAddForm
from plone.dexterity.browser.add import DefaultAddView
from plone.dexterity.browser.edit import DefaultEditForm
from plone.z3cform import layout
from z3c.form import button


class SecondaryContactGridMixin(ContactInformationsGridMixin):
    """A Secondary contact references ONE contact, in `related_contact`.

    No `hide_title` handling here: that field belongs to imio.smartweb.core's
    Section base and does not exist on this type.
    """

    contact_uids_field = "related_contact"


class SecondaryContactCustomAddForm(SecondaryContactGridMixin, DefaultAddForm):
    portal_type = "imio.events.SecondaryContact"

    # Both MUST be copied before the decorator runs: @buttonAndHandler does a
    # setdefault on the `buttons` AND on the `handlers` name of the class body
    # being defined. Without the copies it would create fresh, empty managers
    # that shadow the base ones -- the form would lose the Save / Cancel
    # buttons (buttons) and, more silently, their handlers (handlers), so
    # pressing Save would render the form again without saving anything.
    buttons = DefaultAddForm.buttons.copy()
    handlers = DefaultAddForm.handlers.copy()

    @button.buttonAndHandler(
        _("Load contact information"), name="load_contact_informations"
    )
    def handleLoadContactInformations(self, action):
        """No-op: the grids were already rebuilt in update()."""


class SecondaryContactCustomAddView(DefaultAddView):
    form = SecondaryContactCustomAddForm


class SecondaryContactCustomEditForm(SecondaryContactGridMixin, DefaultEditForm):
    # See SecondaryContactCustomAddForm for why both managers are copied here.
    buttons = DefaultEditForm.buttons.copy()
    handlers = DefaultEditForm.handlers.copy()

    @button.buttonAndHandler(
        _("Load contact information"), name="load_contact_informations"
    )
    def handleLoadContactInformations(self, action):
        """No-op: the grids were already rebuilt in update()."""


SecondaryContactCustomEditView = layout.wrap_form(SecondaryContactCustomEditForm)
