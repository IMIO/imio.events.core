# -*- coding: utf-8 -*-

from imio.events.core.viewlets.event import (
    user_is_contributor_in_entity_which_authorize_to_bring_events,
)
from imio.smartweb.common.utils import get_vocabulary
from imio.smartweb.common.widgets.select import TranslatedAjaxSelectWidget
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from zope import schema
from z3c.form import button
from z3c.form import form
from z3c.form.button import buttonAndHandler
from plone.supermodel import model


class IBringEventIntoAgendasForm(model.Schema):
    """ """

    directives.widget(
        "agendas",
        TranslatedAjaxSelectWidget,
        vocabulary="imio.events.vocabulary.UserAgendas",
        pattern_options={"multiple": True},
    )
    directives.write_permission(agendas="cmf.SetOwnProperties")
    agendas = schema.List(
        title=_("Available agendas"),
        value_type=schema.Choice(source="imio.events.vocabulary.UserAgendas"),
        required=True,
    )


class BringEventIntoAgendasForm(AutoExtensibleForm, form.Form):
    """ """

    schema = IBringEventIntoAgendasForm
    ignoreContext = True
    enable_autofocus = False
    label = _("Add/Remove agenda(s)")

    def update(self):
        super(BringEventIntoAgendasForm, self).update()
        if user_is_contributor_in_entity_which_authorize_to_bring_events is False:
            api.portal.show_message(
                _("You don't have rights to access this page."), self.request
            )
            self.request.response.redirect(self.context.absolute_url())
            return False

    def updateWidgets(self):
        super(BringEventIntoAgendasForm, self).updateWidgets()
        selectedItems = {}
        self.selectedUID = []
        vocabulary = get_vocabulary("imio.events.vocabulary.UserAgendas")

        for term in vocabulary:
            if term.value in self.context.selected_agendas:
                self.selectedUID.append(term.value)
                selectedItems[term.value] = term.title
        self.widgets["agendas"].value = ";".join(self.selectedUID)

    @buttonAndHandler(_("Submit"))
    def handle_submit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        if len(data.get("agendas")) < len(self.selectedUID):
            # we want to remove agenda(s) out of this event
            agendas_to_remove = list(set(self.selectedUID) - set(data.get("agendas")))
            for agenda in agendas_to_remove:
                self.context.selected_agendas.remove(agenda)
            success_message = _("Agenda(s) correctly removed.")
        else:
            # we want to add an agenda in this event
            for agenda in data.get("agendas"):
                if agenda not in self.context.selected_agendas:
                    self.context.selected_agendas.append(agenda)
            success_message = _("Agenda(s) correctly added.")

        self.context.reindexObject(idxs=["selected_agendas"])
        self.status = success_message
        api.portal.show_message(_(self.status), self.request)

        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())
