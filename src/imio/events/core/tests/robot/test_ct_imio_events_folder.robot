# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s imio.events.core -t test_imio.events.Folder.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src imio.events.core.testing.IMIO_EVENTS_CORE_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot /src/imio/events/core/tests/robot/test_imio.events.Folder.robot
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

Scenario: As a site administrator I can add a imio.events.Folder
  Given a logged-in site administrator
    and an add imio.events.Folder form
   When I type 'My imio.events.Folder' into the title field
    and I submit the form
   Then a imio.events.Folder with the title 'My imio.events.Folder' has been created

Scenario: As a site administrator I can view a imio.events.Folder
  Given a logged-in site administrator
    and a imio.events.Folder 'My imio.events.Folder'
   When I go to the imio.events.Folder view
   Then I can see the imio.events.Folder title 'My imio.events.Folder'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add imio.events.Folder form
  Go To  ${PLONE_URL}/++add++imio.events.Folder

a imio.events.Folder 'My imio.events.Folder'
  Create content  type=imio.events.Folder  id=my-imio.events.Folder  title=My imio.events.Folder

# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.IBasic.title  ${title}

I submit the form
  Click Button  Save

I go to the imio.events.Folder view
  Go To  ${PLONE_URL}/my-imio.events.Folder
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a imio.events.Folder with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the imio.events.Folder title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
