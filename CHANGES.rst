Changelog
=========


1.2.25 (2024-06-21)
-------------------

- WEB-4088 : Use transaction commit hook to be sure event object is available before odwb call
  [boulch]

- GHA tests on Python 3.8 3.9 and 3.10
  [remdub]


1.2.24 (2024-06-20)
-------------------

- WEB-4088 : Use one state workflow for imio.events.Agenda / imio.events.Folder
  [boulch]


1.2.23 (2024-06-19)
-------------------

- Add events lead image (preview scale) for odwb and some logs
  [boulch]

- Refactor items_to_delete : Added translations / Corrected result of number of items
  [boulch]


1.2.22 (2024-06-06)
-------------------

- WEB-4113 : Use `TranslatedAjaxSelectWidget` to fix select2 values translation
  [laulaz]


1.2.21 (2024-05-28)
-------------------

- WEB-4101 : Calculate `search-filters` JSON based on `@events` search results logic.
  We need to refactor & test (more) this module.
  [laulaz]


1.2.20 (2024-05-27)
-------------------

- WEB-4101 : Add index for local category search
  [laulaz]


1.2.19 (2024-05-24)
-------------------

- Fix naming of two fields for odwb
  [boulch]


1.2.18 (2024-05-24)
-------------------

- improves odwb fields nomenclature
  [boulch]


1.2.17 (2024-05-24)
-------------------

- WEB-4101 : Handle (local) categories translations with datagrid field and
  new indexes. French value is used as identifier for local categories.
  [laulaz]

- WEB-4088 : Cover use case for sending data in odwb for a staging environment
  [boulch]

- Fix Topics & Categories in SearchableText translated indexes
  [laulaz]

- WEB-4088 : Add some odwb endpoints (for events , for entities)
  [boulch]

- WEB-4108 : Prevent removing calendar if there is at least 1 event in it.
  [boulch]


1.2.16 (2024-05-02)
-------------------

- WEB-4101 : Use local category (if any) instead of category in `category_title` indexer
  [laulaz]


1.2.15 (2024-04-10)
-------------------

- Fix : Keep events where start date is earlier than current date and end date is later than current date (when no period defined)
  [boulch]


1.2.14 (2024-04-04)
-------------------

- Fix serializer. Sometimes we have brain, sometines event, agenda or folder...
  [boulch]

1.2.13 (2024-04-04)
-------------------

- Getting agenda title/id to use it in rest views
  [boulch]


1.2.12 (2024-03-29)
-------------------

- MWEBPM-9 : Add container_uid as metadata_field to retrieve agenda id/title in event serializer and set it in our json dataset
  [boulch]

- MWEBPM-8 : Add support for getting only past events
  [boulch]


1.2.11 (2024-03-21)
-------------------

- Fix some issues (bad copy/paste!)
  [boulch]


1.2.10 (2024-03-21)
-------------------

- WEB-4068 : Refactor / Fix some issues
  [boulch]


1.2.9 (2024-03-13)
------------------

- WEB-4068 : Add field to limit the new feature "adding events in any agenda" to some entities
  [boulch]


1.2.8 (2024-03-12)
------------------

- WEB-4068 : Refactor "adding events in any agenda" : (update translations, add feature : "remove agenda")
  [boulch]


1.2.7 (2024-03-11)
------------------

- WEB-4068 : Adding events in any agenda of the current entity
  [boulch]


1.2.6 (2024-02-28)
------------------

- WEB-4072, WEB-4073 : Enable solr.fields behavior on some content types
  [remdub]

- WEB-4006 : Exclude some content types from search results
  [remdub]

- MWEBRCHA-13 : Add versioning on imio.events.Event
  [boulch]


1.2.5 (2024-01-25)
------------------

-  WEB-3802 : Fix : Avoid noizy events occurrences. Occurences that begin later than min date with a valid end date.
   [boulch]


1.2.4 (2024-01-25)
------------------

- WEB-3802 : Fix : Keep events occurrences when start date is smaller than min date but end date is greater than min date
  [boulch]


1.2.3 (2024-01-24)
------------------

- WEB-3802 : Manually filter dates to respect range passing into REST request.
  [boulch]


1.2.2 (2024-01-22)
------------------

- WEB-3802 : Get dates range for events in REST views. Comming from imio.smartweb.core React view
  [boulch]


1.2.1 (2024-01-09)
------------------

- WEB-4041 : Handle new "carre" scale
  [boulch]


1.2 (2023-10-25)
----------------

- WEB-3985 : Use new portrait / paysage scales & logic
  [boulch, laulaz]

- WEB-3985 : Remove old cropping information when image changes
  [boulch, laulaz]


1.1.15 (2023-10-18)
-------------------

- WEB-3997 : Fix : Initial agenda must be kept!
  [boulch]

- WEB-3997 : Fix : Add condition to avoid getting a broken "_broken_to_path" old/removed agenda
  [boulch]


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
