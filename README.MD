This project is designed to help the ITS Service Desk manager keep track of his or her students' work hours at the
Service Desk with an RFID scanner to track the start and end of each student's work shift (clocking in and out).

The manager uploads his or her student work schedule for a desired time period into the Scanner Data sheet of the Google
Spreadsheet linked in app/sheets_controller.py. The manager also must enter student information such as their full name 
and the 5-digit card ID number associated with them, located on the back of their student ID card, into the Student
Employees sheet. With each clock in and out from their shifts, students will scan an RFID scanner with their ID and
their shift will load into the table on the student time clock page of the site. By scanning their IDs, the clock in/out
information will be uploaded to the Scanner Data sheet. Only the shifts that match with the current day will display in
the table on the student time clock page, while all other shifts will not display to the site, only in the spreadsheet.
After the manager has entered the desired shifts to be compared into the Service Desk Schedule sheet and the user
information is up to date in the Student Employees sheet, he or she can click the "Process Shift Data" button on the
Staff page of the site to compare shifts between the manager's shifts in the Service Desk Schedule sheet and the
collected scanned shifts located in the Scanner Data sheet. The list of "flagged shifts" will be stored in the Flagged
Shifts sheet of the spreadsheet and the Flagged Shifts, Service Desk Schedule, Scanner Data, and Student Employees
sheets all have buttons on the Staff page that open links to their specific sheets.

Flagged shifts will include shifts where the student:
* Is late to a shift by more than 8 minutes
* Is present for 8 or more minutes less than the scheduled duration of the shift
* Misses a shift entirely / forgets to clock in and out
* Forgets to clock in or out (one or the other, not both)
* Signs in from an IP address other than the Service Desk's kiosk computer

Students who clock in and/or out when they were not scheduled for a shift will have their clock in/out show up in the
table on the student time clock page, but it will not be treated as a "bad" shift by the program and will be ignored as
the shift should not be clocked by a student.

Students do not need to clock in and out for each shift if they are working multiple shifts in a row. They just need to
clock in when they arrive and clock out when they leave.

Other details about how this project works can be found in the Help page of the site, which contains FAQ for the
manager.