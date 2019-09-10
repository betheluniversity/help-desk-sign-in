## Description

Caleb made changes to the nav-bar to allow only ITS employees to view the Staff and Help tabs of the nav-bar
on the site. Student employees are now unable to see those links. I (Micah) changed the naming of the Google Sheets and
their corresponding variables in shifts_controller.py in order to make things less confusing to the Service Desk
staff when they enter the spreadsheet and make things simpler within the code. Naming of the sheets now corresponds 
to how they are labeled on the buttons on the Staff page of the site.

Fixes # 7 (Google Sheet name updates)

## Size and Type of change

- Small Change - 1 person needs to review this

- Bug fix

## How Has This Been Tested?

Please briefly describe the tests that you ran to verify your changes.

- I only did some renaming of spreadsheet names, but I have yet to rename the sheets in the Google Sheet to their
corresponding variable names so that the site does not break under the current version being used today (9/10/19).
I need to rename these sheets once this branch is pushed to master.
- The Time Clock page was not clocking shifts properly. Caleb found that it was due to the page going through CAS
when the Time Clock page does not have a user signed into CAS. This has been fixed and things are
working properly.

## Checklist:

Only check what applies and what you have done.

- [x] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] I have tested on multiple browsers (Chrome, Firefox, Safari, IE suite)
