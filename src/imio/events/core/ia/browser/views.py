from collective.taxonomy.interfaces import ITaxonomy
from imio.smartweb.common.ia.browser.views import BaseProcessCategorizeContentView
from imio.events.core.contents import IEvent
from zope.component import getSiteManager


import json


class ProcessCategorizeContentView(BaseProcessCategorizeContentView):

    def _get_all_text(self):
        all_text = ""
        raw = self.request.get("BODY")
        data = json.loads(raw)
        event_title = data.get("formdata").get("form-widgets-IIASmartTitle-title", "")
        event_richtext = data.get("formdata").get(
            "form-widgets-IRichTextBehavior-text", ""
        )
        all_text = f"{event_title} {event_richtext}"
        return all_text.strip()

    def _process_specific(self, all_text, results):
        """Must be impleted"""
        ia_category = self._process_category(all_text, results)
        results["form-widgets-category"] = ia_category

        ia_local_category = self._process_local_category(all_text, results)
        results["form-widgets-local_category"] = ia_local_category
        ia_public_cible = self._process_public_cible(all_text, results)
        results["form.widgets.event_public.taxonomy_event_public"] = ia_public_cible
        return results

    def _process_public_cible(self, all_text, results):
        if (
            self.context.taxonomy_event_public is None
            or self.context.taxonomy_event_public == []
        ):
            sm = getSiteManager()
            public_cible_taxo = sm.queryUtility(
                ITaxonomy, name="collective.taxonomy.event_public"
            )
            public_cible_voca = public_cible_taxo.makeVocabulary(
                self.current_lang
            ).inv_data
            public_cible_voc = [
                {"title": v, "token": k} for k, v in public_cible_voca.items()
            ]
            data = self._ask_categorization_to_ia(all_text, public_cible_voc)
            if not data:
                return ""
            ia_public_cible = [
                {"title": r.get("title"), "token": r.get("token")}
                for r in data.get("result")
            ]

            return ia_public_cible

    def _process_category(self, all_text, results):
        category_voc = self._get_structured_data_from_vocabulary(
            "imio.events.vocabulary.EventsCategories"
        )
        data = self._ask_categorization_to_ia(all_text, category_voc)
        if not data:
            return
        ia_categories = [
            {"title": r.get("title"), "token": r.get("token")}
            for r in data.get("result", [])
        ]
        return ia_categories

    def _process_local_category(self, all_text, results):
        category_voc = self._get_structured_data_from_vocabulary(
            "imio.events.vocabulary.EventsLocalCategories", self.context
        )
        data = self._ask_categorization_to_ia(all_text, category_voc)
        if not data:
            return
        ia_categories = [
            {"title": r.get("title"), "token": r.get("token")}
            for r in data.get("result", [])
        ]
        return ia_categories
