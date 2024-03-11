# -*- coding: utf-8 -*-

from imio.smartweb.common.utils import get_vocabulary
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone import api
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
    label = _("Add/Remove agenda(s)")

    def updateWidgets(self):
        agendas_to_display = []
        vocabulary = get_vocabulary("imio.events.vocabulary.UserAgendas")
        # Loop to display only agenda where user has the permission (ex : to remove these agendas out of event)
        for agenda_uid in self.context.selected_agendas:
            if vocabulary.by_token.get(agenda_uid) is None:
                # user can't remove this agenda because he has no permission on it so we don't display it
                pass
            agendas_to_display.append(agenda_uid)
        self.fields["agendas"].field.default = agendas_to_display
        super(BringEventIntoAgendasForm, self).updateWidgets()

    @buttonAndHandler(_("Submit"))
    def handle_submit(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        if len(data.get("agendas")) < len(self.fields["agendas"].field.default):
            # we want to remove agenda(s) out of this event
            agendas_to_remove = list(
                set(self.fields["agendas"].field.default) - set(data.get("agendas"))
            )
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
        transaction.commit()
        self.status = success_message
        api.portal.show_message(_(self.status), self.request)

        self.request.response.redirect(self.context.absolute_url())

    @button.buttonAndHandler(_("Cancel"))
    def handleCancel(self, action):
        self.request.response.redirect(self.context.absolute_url())
