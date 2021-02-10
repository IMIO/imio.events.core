# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s imio.events.core -t test_imio.events.Event.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src imio.events.core.testing.IMIO_EVENTS_CORE_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot /src/imio/events/core/tests/robot/test_imio.events.Event.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a site administrator I can add a imio.events.Event
  Given a logged-in site administrator
    and an add imio.events.Event form
   When I type 'My imio.events.Event' into the title field
    and I submit the form
   Then a imio.events.Event with the title 'My imio.events.Event' has been created

Scenario: As a site administrator I can view a imio.events.Event
  Given a logged-in site administrator
    and a imio.events.Event 'My imio.events.Event'
   When I go to the imio.events.Event view
   Then I can see the imio.events.Event title 'My imio.events.Event'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add imio.events.Event form
  Go To  ${PLONE_URL}/++add++imio.events.Event

a imio.events.Event 'My imio.events.Event'
  Create content  type=imio.events.Event  id=my-imio.events.Event  title=My imio.events.Event

# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.IBasic.title  ${title}

I submit the form
  Click Button  Save

I go to the imio.events.Event view
  Go To  ${PLONE_URL}/my-imio.events.Event
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a imio.events.Event with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the imio.events.Event title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
