This project is designed to help the ITS Service Desk manager keep track of his or her students' work hours at the
Service Desk with an RFID scanner to track the start and end of each student's work shift (clocking in and out).

The manager uploads his or her student work schedule for a desired time period into the 'hd_export' sheet of the Google
Spreadsheet linked in 'sheets_controller.py'. The manager also must enter student information such as their full name 
and the 5-digit card ID number associated with them, located on the back of their student ID card, into the 'hd_users' 
sheet. With each clock in and out from their shifts, students will scan an RFID scanner with their ID and their shift 
will load into the table on the student time clock page of the site. By scanning their IDs, the clock in/out information
will be uploaded to the 'scan_input' sheet. Only the shifts that match with the current day will display in the table on
the student time clock page, while all other shifts will not display to the site, only in the spreadsheet. After the
manager has entered the desired shifts to be compared into 'hd_export' and the user information is up to date in
'hd_users', he or she can click the "Process Shift Data" button on the Staff page of the site to compare shifts between
the manager's 'hd_export' shifts and the collected scanned shifts located in the 'scan_input' sheet. The list of 
"flagged shifts" will be stored in the 'flagged_sheets' sheet of the spreadsheet and the 'flagged_items', 'hd_export',
'scan_input', and 'hd_users' sheets all have buttons on the Staff page that open links to their specific sheets.

Flagged shifts will include shifts where the student:
* Is late to a shift by more than 8 minutes
* Is present for 8 or more minutes less than the scheduled duration of the shift
* Misses a shift entirely / forgets to clock in and out
* Forgets to clock in or out (one or the other, not both)

Students who clock in and/or out when they were not scheduled for a shift will have their clock in/out show up in the
table on the student time clock page, but it will not be treated as a "bad" shift by the program and will be ignored as
the shift should not be clocked by a student.

Students do not need to clock in and out for each shift if they are working multiple shifts in a row. They just need to
clock in when they arrive and clock out when they leave.

Other details about how this project works can be found in the 'help.html' file, the Help/FAQ page of the site.