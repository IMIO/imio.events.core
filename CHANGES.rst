Changelog
=========


1.0a6 (unreleased)
------------------

- WEB-3770 : Add serializer to get included items when you request an imio.events.Event fullbobjects
  [boulch]

- WEB-3757 : Automaticaly create some defaults agendas (with agendas subscription) when creating a new entity
  [boulch]

- WEB-3726 : Add subjects (keyword) in SearchableText
  [boulch]


1.0a5 (2022-10-18)
------------------

- Add logging to find cause of infinite loop statement
  [laulaz]

- Add eea.faceted.navigable behavior on Entity & Agenda types
  [laulaz]


1.0a4 (2022-07-14)
------------------

- Ensure objects are marked as modified after appending to a list attribute
  [laulaz]

- Fix selected_agendas on events after creating a "linked" agenda
  [boulch]


1.0a3 (2022-05-03)
------------------

- Remove useless imio.events.Page content type
  [boulch]

- Use unique urls for images scales to ease caching
  [boulch]

- Use common.interfaces.ILocalManagerAware to mark a locally manageable content
  [boulch]


1.0a2 (2022-02-09)
------------------

- Add event_dates index to handle current events queries correctly
  [laulaz]

- Update buildout to use Plone 6.0.0a3 packages versions
  [boulch]


1.0a1 (2022-01-25)
------------------

- Initial release.
  [boulch]
