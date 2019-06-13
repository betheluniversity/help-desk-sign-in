This project is designed to help the ITS Help Desk manager
keep track of his students' work hours at the Help Desk
with an RFID scanner to track the start and end of each
student's work shift (like clocking in and out).

The HD manager uploads his student schedule times and
information into the 'hd_export' sheet of the Google
Spreadsheet linked in 'spreadsheet.py'. With each clock in
and out from their shifts, students will scan an RFID
scanner and select whether they are signing in or out on
the web-page. Through the RFID scanner and selected
information on the web-page, the clock in and out
information will be uploaded to the 'python_input' sheet
of the Google Spreadsheet. Once the time period of shifts
between 'python_input' and 'hd_export' matches, the HD
manager can enter the web-page and generate all "flagged"
shifts that raised issues in the program.

Flagged shifts will include shifts where the student:
* Is late to a shift by more than 8 minutes
* Is present for 8 or more minutes less than the total
duration of the shift
* Misses a shift entirely
* Forgets to clock in or out (one or the other, not both)

Students do not need to clock in and out for each shift if
they are working multiple shifts in a row. They just need
to clock in when they arrive and clock out when they leave.

Tasks still TODO:
* Web-pages for student sign in/out and HD manager's
flagged-shift generator
* Tying the RFID scanner information to code and testing
* Any other testing or issues that arise