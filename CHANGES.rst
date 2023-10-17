Changelog
=========


1.1.14 (2023-10-17)
-------------------

- WEB-3997 : Fix recursive_generator if agenda A has a reference to agenda B and agenda B has a reference to agenda A
  [boulch]


1.1.13 (2023-10-11)
-------------------

- WEB-3997 : Add cascading agendas subscriptions retrieval in endpoint to get events "by dependency"
  [boulch]


1.1.12 (2023-10-09)
-------------------

- WEB-3989 : Fix infinite loop on object deletion & remove logs
  [laulaz]


1.1.11 (2023-09-12)
-------------------

- Avoid infinite loop with bad recurrence RRULE expression (`INTERVAL=0"`) - improved
  See https://github.com/plone/plone.formwidget.recurrence/issues/39
  [laulaz]


1.1.10 (2023-07-26)
-------------------

- [WEB-3937] Fix add / edit forms for events
  [boulch, laulaz]


1.1.9 (2023-07-24)
------------------

- [WEB-3937] Limit event duration to maximum 3 years
  [boulch, laulaz]


1.1.8 (2023-07-18)
------------------

- Add logs in endpoint. Help us to find why agenda go slowlier
  [boulch]


1.1.7 (2023-07-03)
------------------

- Avoid infinite loop with bad recurrence RRULE expression (`INTERVAL=0"`)
  See https://github.com/plone/plone.formwidget.recurrence/issues/39
  [laulaz]


1.1.6 (2023-05-05)
------------------

- INFRA-4725 : Add logging to find infinite loop in recurrence calculation
  [laulaz]

- Migrate to Plone 6.0.4
  [boulch]


1.1.5 (2023-03-31)
------------------

- Need fullobjects in query to avoid "Cannot read properties of undefined (reading 'latitude')" in rest view
  So, we need to serialize first_start and first_end from obj.start and obj.end. If we don't do that, we got brain.start/end
  these are updates with first valid event occurence
  [boulch]


1.1.4 (2023-03-30)
------------------

- Fix occurrences expansion calculation for start dates
  We can't use start/end recurring indexes because they return the next occurrence
  and not the first one, so recurrence rule cannot be applied on them.
  [laulaz]

- Fix bug calculating `event_dates` index with occurrences
  [laulaz]

- WEB-3908 : Create new endpoint to serve batched events occurrences
  [boulch]


1.1.3 (2023-03-13)
------------------

- Add warning message if images are too small to be cropped
  [laulaz]

- Migrate to Plone 6.0.2
  [boulch]

- Fix reindex after cut / copy / paste in some cases
  [laulaz]


1.1.2 (2023-02-20)
------------------

- Remove unused title_fr and description_fr metadatas
  [laulaz]

- Remove SearchableText_fr (Solr will use SearchableText for FR)
  [laulaz]


1.1.1 (2023-01-12)
------------------

- Add new descriptions metadatas and SearchableText indexes for multilingual
  [laulaz]


1.1 (2022-12-20)
----------------

- Update to Plone 6.0.0 final
  [boulch]


1.0.1 (2022-11-15)
------------------

- Fix SearchableText index for multilingual
  [laulaz]


1.0 (2022-11-15)
----------------

- Add multilingual features: New fields, vocabularies translations, restapi serializer
  [laulaz]


1.0a6 (2022-10-21)
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

- Fix deprecated get_mimetype_icon
  [boulch]
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
