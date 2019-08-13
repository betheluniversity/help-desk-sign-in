# Global
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Packages
import datetime
from datetime import datetime
from datetime import timedelta
from functools import cmp_to_key
from operator import itemgetter as i

# Local
from app import app

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)
client = gspread.authorize(credentials)

# variables with 'client.open' grant access to that specific sheet of the Help Desk Sign In Google Sheet
spreadsheet = client.open('help_desk_sign_in')

# 'gsheet_flagged_shifts' stores the "bad" shifts of students when the scanned input is compared to their schedule
gsheet_flagged_shifts = spreadsheet.worksheet('flagged_shifts')
# 'gsheet_scan_input' stores the clock in/out info from the Help Desk RFID scanner, tracking student attendance
gsheet_scan_input = spreadsheet.worksheet('scan_input')
# 'gsheet_hd_export' stores where the manager posts his expected shift schedule, typically for a two-week period
gsheet_hd_export = spreadsheet.worksheet('hd_export')
# 'gsheet_hd_users' stores where the site inputs student username and card ID info for shift comparisons
gsheet_hd_users = spreadsheet.worksheet('hd_users')


class ShiftsController:
    # enters clock ins and outs into scan_input sheet
    # card id: 5-digit ID on Bethel IDs used to identify users
    def student_time_clock(self, card_id):
        timestamp = datetime.now()
        # formats the time into string format (example: 12:00 PM)
        current_time = timestamp.strftime('%-I:%M %p')
        date = timestamp.strftime('%x')

        shifts_list = self.shifts_list()
        users_list = self.users_list()

        # the cell_list below applies as a clock-in, which is assumed unless the clock-out criteria are met within the
        # double for-loops for shifts_list and users_list
        # cell_list sets the range of cells in the Google Sheet to which the data will be appended
        # len(self.shifts_list) + 2 is the row in the scan_input sheet this cell_list will append to
        # len(self.shifts_list) + 2 = number of shifts currently entered + 2
        # 2 = +1 for the header row in scan_input and +1 for a new entry into the list
        cell_list = gsheet_scan_input.range(len(shifts_list) + 2, 1, len(shifts_list) + 2, 4)

        # searching through users and shifts to match card_id and determine clock in or out
        for user in users_list:
            if user['Card ID'] == card_id:
                for shift in shifts_list:
                    # if shifts_list username matches users_list username and the shift's clock out is empty,
                    # this is a clock-out. cell_list sets the row in scan_input to append to as
                    # shifts_list.index(shift) + 2
                    # shifts_list.index(shift) = the index of that user's original clock-in
                    # len(shifts_list) is not used so the clock-out is not appended to a new row
                    if shift['Name'] == user['Name'] and shift['Out'] == '' and shift['Date'] == date:
                        cell_list = gsheet_scan_input.range(shifts_list.index(shift) + 2, 1,
                                                            shifts_list.index(shift) + 2, 4)
                        cell_list[3].value = current_time
                        gsheet_scan_input.update_cells(cell_list)
                        # if there is not a return here, the code below executes and thus, when a clock out occurs, it
                        # is logged as both a clock out and a new clock in if this return does not exist
                        return 'scan success'
                # cell_list[number].value sets a cell to a value, with number = column number in the Google Sheet range
                cell_list[0].value = user['Name']  # sets username
                cell_list[1].value = date  # sets date
                cell_list[2].value = current_time  # sets time in as current time
                gsheet_scan_input.update_cells(cell_list)  # appends to scan_input sheet

    # the 4 methods below refresh the necessary list of sheets called by student_time_clock and shift_processor
    # refreshes the list of dictionaries of the hd_export sheet, allowing the schedule to be up to date
    def hd_list(self):
        return gsheet_hd_export.get_all_records()

    # refreshes the list of dictionaries of the scan_input sheet, allowing the total list of shifts to be up to date
    def shifts_list(self):
        return gsheet_scan_input.get_all_records()

    # refreshes the list of dictionaries of the hd_users sheet, allowing the users page to be up to date
    def users_list(self):
        return gsheet_hd_users.get_all_records()

    # appends any existing shift from the scan_input sheet on the current day to a list that displays on the main page
    def day_list(self):
        timestamp = datetime.now()
        date = timestamp.strftime('%x')
        day_list = []
        shifts_list = self.shifts_list()
        for shift in shifts_list:
            if shift['Date'] == date:
                day_list.append(shift)
        day_list.reverse()
        return day_list

    # compares keys in a list of dictionaries to sort in ascending or descending order
    # items: the list of dictionaries
    # columns: the keys being sorted, in order of desired sort
    # found at https://tinyurl.com/y2m6wuzr
    def multi_key_sort(self, items, columns):
        comparers = [
            ((i(col[1:].strip()), -1) if col.startswith('-') else (i(col.strip()), 1))
            for col in columns
        ]

        def cmp(a, b):
            return (a > b) - (a < b)

        def comparer(left, right):
            comparer_iter = (
                cmp(fn(left), fn(right)) * mult
                for fn, mult in comparers
            )
            return next((result for result in comparer_iter if result), 0)
        return sorted(items, key=cmp_to_key(comparer))

    # converts a time-string from one time format to the other
    # convert_time: string of the time to be converted
    # time_format: time format to be converted to (24-hour or 12-hour)
    def convert_time_format(self, convert_time, time_format):
        # if time slot is empty
        if convert_time == '':
            return ''
        # converts a time-string to 24-hour format for sorting chronologically easier
        if time_format == 24:
            d = datetime.strptime(convert_time, '%I:%M %p')
            return d.strftime('%H:%M')
        # converts a time-string to 12-hour format for easier readability
        else:  # time_format == 12
            d = datetime.strptime(convert_time, '%H:%M')
            return d.strftime('%-I:%M %p')

    # clears all cells in a specified sheet and resets their values to empty strings
    # sheet: sheet to be cleared
    # cols: number of columns in the sheet range to be cleared
    def reset_sheet_data(self, sheet, cols):
        # cell_reset sets the range of rows to clear between row 2 and row len(sheet.get_all_records())+1
        # len(sheet.get_all_records())+1 = length of the specified sheet (# of rows with values in cell(s)) + 1
        cell_reset = sheet.range(2, 1, len(sheet.get_all_records()) + 1, cols)
        for cell in cell_reset:
            cell.value = ''
        sheet.update_cells(cell_reset)

    # updates a row of cells in 'gsheet_flagged_shifts' with info on any "bad" shifts
    # hd_shifts: list of dictionaries of shifts gathered from hd_export sheet
    # scan_shifts: list of dictionaries of shifts gathered from scan_input sheet
    # hd_row: specific row from hd_export that should be flagged as "bad"
    # scan_row: specific row from scan_input that should be flagged as "bad"
    # flag_num: specifies the row of flagged_shifts sheet to append the new "bad" shift info to
    # reason: string of info about why the shift was flagged
    # skipped: boolean true/false value for if the student skipped the shift entirely
    def flagged_cells(self, hd_shifts, scan_shifts, hd_row, scan_row, reason, skipped):
        # creating new array of size 8 for the 8 columns in flagged_shifts sheet
        flag_val = [''] * 8
        # setting the values of the array with the "bad" shift data and returning to shift_processor method
        flag_val[0] = hd_shifts[hd_row]['Shift ID']
        flag_val[1] = hd_shifts[hd_row]['Date']
        flag_val[2] = self.convert_time_format(hd_shifts[hd_row]['Start Time'], 12)
        flag_val[3] = self.convert_time_format(hd_shifts[hd_row]['End Time'], 12)
        flag_val[4] = hd_shifts[hd_row]['Employee Name']
        if skipped:
            flag_val[5] = ''
            flag_val[6] = ''
        else:
            flag_val[5] = self.convert_time_format(scan_shifts[scan_row]['In'], 12)
            flag_val[6] = self.convert_time_format(scan_shifts[scan_row]['Out'], 12)
        flag_val[7] = reason
        return flag_val

    # runs the comparison between hd_export and scan_input to determine "bad" shifts
    # hd_shifts: list of dictionaries of shifts gathered from hd_export sheet
    # scan_shifts: list of dictionaries of shifts gathered from scan_input sheet
    def shift_processor(self):
        # refreshes the list of dictionaries of hd_export, scan_input, and hd_users, respectively
        # these 3 sheets from the Google Sheet are called in this way to minimize the number of read requests to the
        # Google Sheets API and not exceed their limit of 100 read requests per 100 seconds
        hd_shifts = self.hd_list()
        scan_shifts = self.shifts_list()

        # searches through hd_shifts and removes all empty shifts from the list of dictionaries
        hd_shifts = [shift for shift in hd_shifts if not shift['Employee Name'] == '']

        # converts times in hd_shifts to 24-hour format
        for shift in hd_shifts:
            date = datetime.strptime(shift['Date'], '%x')
            shift['Date'] = date.strftime('%x')
            # if time-in does not end in 'M' (as in AM/PM), it is already in 24-hour format, break out of loop
            if shift['Start Time'][-1] != 'M':
                break
            shift['Start Time'] = self.convert_time_format(shift['Start Time'], 24)
            shift['End Time'] = self.convert_time_format(shift['End Time'], 24)

        # converts times in scan_shifts to 24-hour format and user-names into full names
        for shift in scan_shifts:
            date = datetime.strptime(shift['Date'], '%x')
            shift['Date'] = date.strftime('%x')
            # if time-in is empty, time conversion is complete, break out of loop
            # if time-in does not end in 'M' (as in AM/PM), it is already in 24-hour format, break out of loop
            if shift['In'] == '' or shift['In'][-1] != 'M':
                break
            shift['In'] = self.convert_time_format(shift['In'], 24)
            shift['Out'] = self.convert_time_format(shift['Out'], 24)

        # sorts hd_shifts and scan_shifts dictionaries in order of name, then date, then start/clock-in time
        hd_shifts = self.multi_key_sort(hd_shifts, ['Employee Name', 'Date', 'Start Time'])
        scan_shifts = self.multi_key_sort(scan_shifts, ['Name', 'Date', 'In'])

        # tracks the correct row number for scanner time in and out, taking into account possible extra shifts
        # gets incremented at certain points in the for loop to keep n (row number for hd_export sheet) even with
        # row number for scan_input
        scan_row = 0
        # tracks the current part of the extra shift(s)
        shift_count = -1

        # clear flagged_shifts sheet data prior to a new run-through of the shifts
        self.reset_sheet_data(gsheet_flagged_shifts, 8)

        # creates keys for the list of dictionaries titled 'flag_list'
        # values that pair with these keys are added via the flagged_cells method
        flag_key = ['Shift ID', 'Date', 'Start Time', 'End Time', 'Employee Name', 'In', 'Out', 'Issue']
        flag_list = []

        # appends an empty shift onto the end of the hd_export list of dictionaries because otherwise, the method cannot
        # check for multiple shifts (i.e. checking hd_shifts[n+1] could lead to IndexError out of bounds without this)
        hd_shifts.insert(len(hd_shifts),
                         {'Shift ID': '', 'Date': '', 'Start Time': '', 'End Time': '', 'Employee Name': ''})
        scan_shifts.insert(len(scan_shifts), {'Name': '', 'Date': '12/31/30', 'In': '23:58', 'Out': '23:59'})

        # loops through all information in the hd_shifts and scan_shifts lists of dictionaries of shift info
        for n in range(0, len(hd_shifts)):
            # this ends the loop once all shifts have been documented
            if hd_shifts[n]['Employee Name'] == '' or scan_shifts[scan_row]['Name'] == '':
                break

            # skips iterating over each shift of a student's multiple shifts in a row
            if shift_count >= n:
                continue
            shift_count = -1  # reset shift counter if this is the first shift in a row

            # sets variables for time in, start time, end time, and duration of the shift from info in hd export
            time_in = datetime.strptime(scan_shifts[scan_row]['Date']+scan_shifts[scan_row]['In'], '%x%H:%M')
            start_time = datetime.strptime(hd_shifts[n]['Date']+hd_shifts[n]['Start Time'], '%x%H:%M')
            end_time = datetime.strptime(hd_shifts[n]['Date']+hd_shifts[n]['End Time'], '%x%H:%M')
            set_duration = end_time - start_time

            # case: student clocks in when they were not scheduled for a shift at that time
            # checks if the clock in is not within 60 minutes in either direction of the scheduled shift start time
            # if so, it checks if the scheduled start time is later (in date or time) than the clocked time in
            # if true, it counts the original scanned shift as a shift they were not assigned to
            # if false, it continues down to where it is marked as a skipped shift
            if not start_time - timedelta(minutes=60) <= time_in <= start_time + timedelta(minutes=60):
                while start_time > time_in and hd_shifts[n]['Employee Name'] == scan_shifts[scan_row]['Name']:
                    scan_row += 1
                    time_in = datetime.strptime(scan_shifts[scan_row]['Date'] +
                                                scan_shifts[scan_row]['In'], '%x%H:%M')

            # case: student forgets to clock out (time out value is empty)
            # forgetting to clock in but then clocking out will be read by the scanner as forgetting to clock out
            if scan_shifts[scan_row]['Out'] == '' and hd_shifts[n]['Date'] == scan_shifts[scan_row]['Date']:
                cause = 'Forgot to clock in or out'
                # updates the flagged_shifts sheet with info about that shift
                flag_list.append(dict(
                    zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                # if student forgets to clock out on a multiple shift
                while hd_shifts[n]['Date'] == hd_shifts[n+1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n+1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n+1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the flagged_shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                scan_row += 1
                continue

            # case: student skips entire shift or forgets to clock in AND out
            if not start_time - timedelta(minutes=10) <= time_in <= start_time + timedelta(minutes=20):
                cause = 'Skipped shift'
                # updates the flagged_shifts sheet with info about that shift
                flag_list.append(
                    dict(zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=True))))

                # if student forgets to clock out on a multiple shift
                while hd_shifts[n]['Date'] == hd_shifts[n+1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n+1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n+1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the flagged_shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=True))))
                continue

            # sets variables for time out and duration of the shift from RFID entry in scan_input
            time_out = datetime.strptime(scan_shifts[scan_row]['Date']+scan_shifts[scan_row]['Out'], '%x%H:%M')
            actual_duration = time_out - time_in

            # case: student works multiple shifts in a row
            while hd_shifts[n]['Date'] == hd_shifts[n+1]['Date'] and hd_shifts[n]['End Time'] == \
                    hd_shifts[n+1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                    hd_shifts[n+1]['Employee Name']:
                n += 1
                end_time = datetime.strptime(hd_shifts[n]['Date']+hd_shifts[n]['End Time'], '%x%H:%M')
                set_duration = end_time - start_time
                actual_duration = time_out - time_in
                shift_count = n

            # two cases: late or short shift
            if time_in > start_time + timedelta(minutes=8) or \
                    actual_duration < set_duration - timedelta(minutes=8):
                # case: student is late
                if time_in > start_time + timedelta(minutes=8):
                    cause = 'Late'
                    # updates the flagged_shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                # case: student leaves early and/or has shorter shift than scheduled
                else:
                    cause = 'Short shift'
                    # updates the flagged_shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

            scan_row += 1

        # adds the list of dictionaries in flag_list into a usable format for sheets as 'cell_list'
        # cell_list posts all "bad" shifts to the flagged_shifts sheet at once using 'update_cells' function of gspread
        cell_list = gsheet_flagged_shifts.range(2, 1, len(flag_list) + 2, 8)
        for shift in flag_list:
            index = flag_list.index(shift)
            cell_list[index * 8].value = shift['Shift ID']
            cell_list[index * 8 + 1].value = shift['Date']
            cell_list[index * 8 + 2].value = shift['Start Time']
            cell_list[index * 8 + 3].value = shift['End Time']
            cell_list[index * 8 + 4].value = shift['Employee Name']
            cell_list[index * 8 + 5].value = shift['In']
            cell_list[index * 8 + 6].value = shift['Out']
            cell_list[index * 8 + 7].value = shift['Issue']
        gsheet_flagged_shifts.update_cells(cell_list)  # appends to flagged_shifts sheet

        # clears the collected data for the scan_input and hd_export sheets, respectively
        # self.reset_sheet_data(gsheet_scan_input, 4)
        # self.reset_sheet_data(gsheet_hd_export, 5)
