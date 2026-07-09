# -*- coding: utf-8 -*-

from imio.events.core.utils import refresh_contact_informations
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.dexterity.browser.edit import DefaultEditForm
from plone.dexterity.events import EditCancelledEvent
from plone.dexterity.events import EditFinishedEvent
from plone.dexterity.i18n import MessageFactory as DMF_
from plone.z3cform import layout
from Products.statusmessages.interfaces import IStatusMessage
from z3c.form import button
from zope.event import notify


class ContactCustomEditForm(DefaultEditForm):
    """Edit form for imio.events.Contact adding a "Refresh from directory"
    button that (re)populates the phones/mails/urls datagrids server-side."""

    @button.buttonAndHandler(
        _("Refresh contact informations from directory"), name="refresh_directory"
    )
    def handleRefreshDirectory(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        # Save first so the refresh uses the currently selected contact and
        # keeps any tick the editor just changed, then overwrite the datagrids
        # with the directory data (preserving the ticked lines).
        self.applyChanges(data)
        refresh_contact_informations(self.context)
        self.context.reindexObject()
        IStatusMessage(self.request).addStatusMessage(
            _("Contact informations have been refreshed from the directory."), "info"
        )
        self.request.response.redirect("{}/edit".format(self.context.absolute_url()))

    @button.buttonAndHandler(DMF_("Save"), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(self.success_message, "info")
        self.request.response.redirect(self.nextURL())
        notify(EditFinishedEvent(self.context))

    @button.buttonAndHandler(DMF_("Cancel"), name="cancel")
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(DMF_("Edit cancelled"), "info")
        self.request.response.redirect(self.context.absolute_url())
        notify(EditCancelledEvent(self.context))


ContactCustomEditView = layout.wrap_form(ContactCustomEditForm)
