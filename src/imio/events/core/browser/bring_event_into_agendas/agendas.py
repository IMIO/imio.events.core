# -*- coding: utf-8 -*-

from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.autoform import directives
from plone.autoform.form import AutoExtensibleForm
from plone.app.z3cform.widget import AjaxSelectFieldWidget
from zope import schema
from z3c.form import button
from z3c.form import form
from z3c.form.button import buttonAndHandler
from plone.supermodel import model

import transaction


class IBringEventIntoAgendasForm(model.Schema):
    """ """

    directives.widget(
        "agendas",
        AjaxSelectFieldWidget,
        source="imio.events.vocabulary.UserAgendas",
        pattern_options={"multiple": True},
    )
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
    label = _("Add this event in your agendas")

    @buttonAndHandler("Submit")
    def handle_submit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        for new_agenda in data.get("agendas"):
            if new_agenda not in self.context.selected_agendas:
                self.context.selected_agendas.append(new_agenda)
        transaction.commit()
        self.context.reindexObject(idxs=["selected_agendas"])
        success_message = _("Event correctly added in agenda(s).")
        self.request.response.redirect(self.context.absolute_url())
        self.status = success_message

    @button.buttonAndHandler("Cancel")
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())
