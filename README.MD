This project is designed to help the ITS Help Desk manager keep track of his or her students' work hours at the Help
Desk with an RFID scanner to track the start and end of each student's work shift (clocking in and out).

The HD manager uploads his or her student schedule times for a desired time period into the 'hd_export' sheet of the
Google Spreadsheet linked in 'sheets_controller.py'. The manager also must enter student information such as full name,
Bethel username, and the 5-digit card ID # associated with them, located on the back of their student ID card into the
'hd_users' sheet. With each clock in and out from their shifts, students will scan an RFID scanner with their ID and
their shift will load into the table on the 'Student Employees' tab of the site. By scanning their IDs, the clock
in/out information will be uploaded to the 'scan_input' sheet. The shifts that match with the current day will display
in the table on the 'Student Employees' tab of the site, while all other shifts will remain unseen in the spreadsheet.
Once the time period of shifts between 'scan_input' and 'hd_export' matches, the HD manager can enter the 'Full-Time
Staff' tab of the site and click the "Process Shift Data" button to generate a list of all "flagged" shifts that raised 
issues in the program. That list will be stored in the 'flagged_items' sheet of the spreadsheet and the 'flagged_items',
'scan_input', 'hd_export', and 'hd_users' sheets all have buttons that open links to their specific sheets in the
'Full-Time Staff' tab.

Flagged shifts will include shifts where the student:
* Is late to a shift by more than 8 minutes
* Is present for 8 or more minutes less than the total duration of the shift
* Misses a shift entirely / forgets to clock in AND out
* Forgets to clock in or out (one or the other, not both)

Students who clock in (and out) when they were not scheduled for a shift will have their clock in/out show up in the
table on the 'Student Employees' tab, but it will not be treated as a "bad" shift by the program and will be ignored as
the shift should not be clocked by a student.

Students do not need to clock in and out for each shift if they are working multiple shifts in a row. They just need to
clock in when they arrive and clock out when they leave.

Tasks still TODO:
* Clearing shifts per day on the front end (table on 'Student Employees' clears with each new day to only display that
day's shifts), but shifts do not clear from 'scan_input' sheet in the Google Spreadsheet
* Comparing usernames in scan_input with usernames in hd_users to associate a shift to a name in the long for-loop of
'shifts_controller.py'
* Try/catch around common errors, such as APIError, to catch them and send Bootstrap alerts
* Import sentry into the init file to capture error messages automatically
* Other minor edits from PR #1 and other small issues to fix up
* Testing