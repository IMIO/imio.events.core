from plone.indexer import indexer
from imio.events.core.contents.event.content import IEvent


@indexer(IEvent)
def category_and_topics_indexer(obj):
    list = []
    if obj.topics is not None:
        list = obj.topics

    list.append(obj.category)

    return list
