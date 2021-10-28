# -*- coding: utf-8 -*-

from embeddify import Embedder
from imio.smartweb.common.utils import translate_vocabulary_term
from imio.smartweb.locales import SmartwebMessageFactory as _
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from plone.app.contenttypes.browser.folder import FolderView
from plone.app.event.browser.event_view import EventView
from zope.i18n import translate


class View(EventView, FolderView):

    GALLERY_IMAGES_NUMBER = 3

    def files(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "File"})

    def images(self):
        return self.context.listFolderContents(contentFilter={"portal_type": "Image"})

    def has_leadimage(self):
        if ILeadImage.providedBy(self.context) and getattr(
            self.context, "image", False
        ):
            return True
        return False

    def get_embed_video(self):
        embedder = Embedder(width=800, height=600)
        return embedder(self.context.video_url, params=dict(autoplay=False))

    def category(self):
        term = translate_vocabulary_term(
            "imio.events.vocabulary.EventsCategories", self.context.category
        )
        if term is None:
            return
        return term.title()

    def topics(self):
        topics = self.context.topics
        items = []
        for item in topics:
            term = translate_vocabulary_term("imio.smartweb.vocabulary.Topics", item)
            translated_title = translate(_(term), context=self.request)
            items.append(translated_title)
        return ", ".join(items)

    def iam(self):
        iam = self.context.iam
        items = []
        for item in iam:
            term = translate_vocabulary_term("imio.smartweb.vocabulary.IAm", item)
            translated_title = translate(_(term), context=self.request)
            items.append(translated_title)
        return ", ".join(items)
