# -*- coding: utf-8 -*-
from collective.taxonomy.exportimport import TaxonomyImportExportAdapter
from collective.taxonomy.factory import registerTaxonomy
from collective.taxonomy.vdex import ImportVdex
from lxml.etree import fromstring
from plone import api
import os


class SortedTaxonomyImportAdapter(TaxonomyImportExportAdapter):
    def importDocument(self, taxonomy, document, clear=False):
        tree = fromstring(document)
        results = ImportVdex(tree, self.IMSVDEX_NS)()

        for language, items in results.items():
            items.sort()
            taxonomy.update(language, items, clear)


def create_taxonomy_object(data_tax, portal):
    taxonomy = registerTaxonomy(
        api.portal.get(),
        name=data_tax["taxonomy"],
        title=data_tax["field_title"],
        description=data_tax["field_description"],
        default_language=data_tax["default_language"],
    )

    adapter = SortedTaxonomyImportAdapter(portal)
    base_path = os.path.dirname(__file__)
    file_path = os.path.join(base_path, data_tax["filepath"])
    data = (open(file_path, "r").read(),)
    import_file = data[0]
    adapter.importDocument(taxonomy, import_file)

    del data_tax["taxonomy"]
    del data_tax["filepath"]
    taxonomy.registerBehavior(**data_tax)
