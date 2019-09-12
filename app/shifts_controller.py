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

# gives access to Google Sheets and the Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)
client = gspread.authorize(credentials)

# variables with 'client.open' grant access to that specific sheet of the Service Desk Sign In Google Sheet
spreadsheet = client.open('Service Desk Sign-In Application')

# 'gsheet_flagged_shifts' stores the "bad" shifts of students when the scanned input is compared to their schedule
gsheet_flagged_shifts = spreadsheet.worksheet('Flagged Shifts (view only)')
# 'gsheet_scanner_data' stores the clock in/out info from the Help Desk RFID scanner, tracking student attendance
gsheet_scanner_data = spreadsheet.worksheet('Scanner Data (view only)')
# 'gsheet_sd_schedule' stores where the manager posts his expected shift schedule, typically for a two-week period
gsheet_sd_schedule = spreadsheet.worksheet('Service Desk Schedule')
# 'gsheet_sd_students' stores where the site inputs student username and card ID info for shift comparisons
gsheet_sd_students = spreadsheet.worksheet('Student Employees')


class ShiftsController:
    def refresh_credentials(self):
        new_scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        new_credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], new_scope)
        new_client = gspread.authorize(new_credentials)
        new_client.login()

    # enters clock ins and outs into Scanner Data sheet
    # card id: 5-digit ID on Bethel IDs used to identify users
    def student_time_clock(self, card_id):
        # formats the current time into string format (example: 12:00 PM)
        current_time = datetime.now().strftime('%-I:%M %p')
        # formats the current date into string format
        current_date = datetime.now().strftime('%x')

        # tracks whether an ID scan has matched with a user in Student Employees
        # if matched = True, the clock in/out will be successful
        # if matched = False, method will trigger an error message to display that the user was not found
        matched = False

        # refreshes list of scanned shifts and list of students and their card IDs
        scanner_data_list = self.scanner_data_list()
        sd_students_list = self.sd_students_list()

        # the cell_list below applies as a clock in, which is assumed unless the clock out criteria are met within the
        # double for-loops for scanner_data_list and sd_students_list
        # cell_list sets the range of cells in the Google Sheet to which the data will be appended
        # len(self.scanner_data_list) + 2 is the row in the Scanner Data sheet this cell_list will append to
        # len(self.scanner_data_list) + 2 = number of shifts currently entered + 2
        # 2 = +1 for the header row in Scanner Data and +1 for a new entry into the list
        cell_list = gsheet_scanner_data.range(len(scanner_data_list) + 2, 1, len(scanner_data_list) + 2, 4)

        # searching through users and shifts to match card_id and determine clock in or out
        for user in sd_students_list:
            if user['Card ID'] == card_id:
                matched = True
                for shift in scanner_data_list:
                    # if scanner_data_list username matches sd_students_list username and the shift's clock out is
                    # empty, this is a clock out. cell_list sets the row in Scanner Data to append to as
                    # scanner_data_list.index(shift) + 2
                    # scanner_data_list.index(shift) = the index of that user's original clock-in
                    # len(scanner_data_list) is not used so the clock-out is not appended to a new row
                    if shift['Name'] == user['Name'] and shift['Out'] == '' and shift['Date'] == current_date:
                        cell_list = gsheet_scanner_data.range(scanner_data_list.index(shift) + 2, 1,
                                                            scanner_data_list.index(shift) + 2, 4)
                        cell_list[3].value = current_time
                        gsheet_scanner_data.update_cells(cell_list)
                        return matched
                # cell_list[number].value sets a cell to a value, with number = column number in the Google Sheet range
                cell_list[0].value = user['Name']  # sets username
                cell_list[1].value = current_date
                cell_list[2].value = current_time  # sets time in as current time
                gsheet_scanner_data.update_cells(cell_list)  # appends to Scanner Data sheet
                break
        return matched

    # the 4 methods below refresh the necessary list of sheets called by student_time_clock, day_list, and
    # shift_processor
    # refreshes the list of dictionaries of the Flagged Shifts sheet, allowing new shifts to append to the next row
    def flagged_shifts_list(self):
        return gsheet_flagged_shifts.get_all_records()

    # refreshes the list of dictionaries of the Service Desk Schedule sheet, allowing the schedule to be up to date
    def sd_schedule_list(self):
        return gsheet_sd_schedule.get_all_records()

    # refreshes the list of dictionaries of the Scanner Data sheet, allowing the total list of shifts to be up to date
    def scanner_data_list(self):
        return gsheet_scanner_data.get_all_records()

    # refreshes the list of dictionaries of the Student Employees sheet, allowing the users page to be up to date
    def sd_students_list(self):
        return gsheet_sd_students.get_all_records()

    # appends any existing shift from the Scanner Data sheet on the current day to a list that displays on the main page
    def day_list(self):
        current_date = datetime.now().strftime('%x')
        day_list = []
        scanner_data_list = self.scanner_data_list()
        for shift in scanner_data_list:
            if shift['Date'] == current_date:
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
            try:  # create datetime object in form of 12:00 PM
                return datetime.strptime(convert_time, '%I:%M %p').strftime('%H:%M')
            except ValueError:  # if 'AM/PM' is not included, create datetime object in form of 12:00
                return datetime.strptime(convert_time, '%I:%M %p').strftime('%H:%M')
        # converts a time-string to 12-hour format for easier readability
        else:  # time_format == 12
            return datetime.strptime(convert_time, '%H:%M').strftime('%-I:%M %p')

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

    # updates a row of cells in Flagged Shifts sheet with info on any "bad" shifts
    # hd_shifts: list of dictionaries of shifts gathered from Service Desk Schedule sheet
    # scan_shifts: list of dictionaries of shifts gathered from Scanner Data sheet
    # hd_row: specific row from Service Desk Schedule that should be flagged as "bad"
    # scan_row: specific row from Scanner Data that should be flagged as "bad"
    # flag_num: specifies the row of Flagged Shifts sheet to append the new "bad" shift info to
    # reason: string of info about why the shift was flagged
    # skipped: boolean true/false value for if the student skipped the shift entirely
    def flagged_cells(self, hd_shifts, scan_shifts, hd_row, scan_row, reason, skipped):
        # creating new array for a new "bad" shift in Flagged Shifts sheet, setting the values of the array with the
        # shift data and returning to shift_processor method
        flag_val = [hd_shifts[hd_row]['Shift ID'], hd_shifts[hd_row]['Date'],
                    self.convert_time_format(hd_shifts[hd_row]['Start Time'], 12),
                    self.convert_time_format(hd_shifts[hd_row]['End Time'], 12), hd_shifts[hd_row]['Employee Name']]

        if skipped:  # if shift was skipped, append empty strings in 'In' and 'Out' columns
            flag_val.append('')
            flag_val.append('')
        else:  # if shift was not skipped, append times for clock in and out in 'In' and 'Out' columns, respectively
            flag_val.append(self.convert_time_format(scan_shifts[scan_row]['In'], 12))
            flag_val.append(self.convert_time_format(scan_shifts[scan_row]['Out'], 12))

        flag_val.append(reason)
        return flag_val

    # runs the comparison between Service Desk Schedule and Scanner Data to determine "bad" shifts
    # hd_shifts: list of dictionaries of shifts gathered from Service Desk Schedule sheet
    # scan_shifts: list of dictionaries of shifts gathered from Scanner Data sheet
    def shift_processor(self):
        # refreshes the list of dictionaries of Flagged Shifts, Scanner Data, and Service Desk Schedule, respectively
        # Service Desk Schedule and Scanner Data are called in this way to minimize the number of read requests to the
        # Google Sheets API and not exceed their limit of 100 read requests per 100 seconds
        flag_shifts = self.flagged_shifts_list()
        scan_shifts = self.scanner_data_list()
        hd_shifts = self.sd_schedule_list()

        # tracks the correct row number for scanner time in and out, taking into account possible extra shifts
        # gets incremented at certain points in the for loop to keep n (row number for Service Desk Schedule sheet) even
        # with row number for Scanner Data
        scan_row = 0

        # tracks the current part of the extra shift(s)
        shift_count = -1

        # tracks lower and upper bounds for the shifts being compared in Scanner Data, later being able to clear shifts
        # within this range and keeping others not in this range
        lower_bound = -1
        upper_bound = -1

        # creates keys for the list of dictionaries titled 'flag_list'
        # values that pair with these keys are added to flag_list via the flagged_cells method
        flag_key = ['Shift ID', 'Date', 'Start Time', 'End Time', 'Employee Name', 'In', 'Out', 'Issue']
        flag_list = []

        # searches through hd_shifts and removes all empty shifts from the list of dictionaries
        hd_shifts = [shift for shift in hd_shifts if not shift['Employee Name'] == '']

        # tracks earliest shift currently in Service Desk Schedule so all shifts before it in Scanner Data are ignored
        # sets earliest_shift to the first element in hd_shifts, then sets the variable to a new value whenever an
        # earlier time is found in the for loop below
        earliest_shift = datetime.strptime(hd_shifts[0]['Date'] +
                                           self.convert_time_format(hd_shifts[0]['Start Time'], 24), '%x%H:%M')
        # tracks latest shift
        latest_shift = datetime.strptime(
            hd_shifts[0]['Date'] + self.convert_time_format(hd_shifts[0]['Start Time'], 24),
            '%x%H:%M')

        # converts times in hd_shifts to 24-hour format amd sets the earliest and latest shifts
        for shift in hd_shifts:
            shift_date = shift['Date']  # setting shift_date to shift['Date'] before converting to datetime object
            shift['Date'] = datetime.strptime(shift['Date'], '%x')
            try:
                shift['Start Time'] = self.convert_time_format(shift['Start Time'], 24)
                shift['End Time'] = self.convert_time_format(shift['End Time'], 24)
            except TypeError:
                pass

            # sets earliest_shift to current shift in loop if before current value
            if datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M') < earliest_shift:
                earliest_shift = datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M')

            # sets latest_shift to current shift in loop if after current value
            if datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M') > latest_shift:
                latest_shift = datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M')

        # converting clock ins and outs to 24-hour format to ensure chronological sort
        for shift in scan_shifts:
            try:
                shift['In'] = self.convert_time_format(shift['In'], 24)
                shift['Out'] = self.convert_time_format(shift['Out'], 24)
            except TypeError:
                pass

        # copy_list is the list of shifts in scan_shifts that were not within the time range of earliest_shift and
        # latest_shift in hd_shifts. These shifts are not being compared or posted to the Flagged Shifts sheet, so
        # they are being copied to be re-posted to the Scanner Data sheet after the scanned shifts are cleared
        copy_list = [shift for shift in scan_shifts if not earliest_shift - timedelta(minutes=30) <=
                     datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M') <= latest_shift + timedelta(minutes=30)]

        # removing shifts from scan_shifts not within the date range of earliest through latest shift in hd_shifts
        scan_shifts = [shift for shift in scan_shifts if earliest_shift - timedelta(minutes=30) <=
                       datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M') <=
                       latest_shift + timedelta(minutes=30)]

        # converts times in scan_shifts to 24-hour format
        for shift in scan_shifts:
            this_shift = datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M')
            shift['Date'] = datetime.strptime(shift['Date'], '%x')

            # if shift is within the bounds of the earliest and latest shifts in Service Desk Schedule, then sets the
            # lower and upper bounds of the Scanner Data shifts that match the time range in Service Desk Schedule
            if earliest_shift - timedelta(minutes=30) <= this_shift <= latest_shift + timedelta(minutes=30):
                if lower_bound < 0:
                    lower_bound = scan_shifts.index(shift)
                while upper_bound < scan_shifts.index(shift):
                    upper_bound = scan_shifts.index(shift)

        # sorts hd_shifts and scan_shifts dictionaries in order of name, then date, then start/clock-in time
        hd_shifts = self.multi_key_sort(hd_shifts, ['Employee Name', 'Date', 'Start Time'])
        scan_shifts = self.multi_key_sort(scan_shifts, ['Name', 'Date', 'In'])

        # appends empty shifts to the end of hd_shifts and scan_shifts to prevent any IndexError out of bounds issues
        # when checking the next index's shift for multiple shifts (e.g., checking hd_shifts[n+1])
        hd_shifts.insert(len(hd_shifts),
                         {'Shift ID': '', 'Date': '', 'Start Time': '', 'End Time': '', 'Employee Name': ''})
        scan_shifts.insert(len(scan_shifts), {'Name': '', 'Date': '', 'In': '', 'Out': ''})

        # shift dates set to datetime.strptime objects are returned to strings for readability and so time_in, time_out,
        # and actual_duration can be set properly
        for shift in scan_shifts:
            if not isinstance(shift['Date'], str):
                shift['Date'] = shift['Date'].strftime('%x')

        # loops through all information in the hd_shifts and scan_shifts lists of dictionaries of shift info
        for n in range(0, len(hd_shifts)):
            # this ends the loop once all shifts have been documented
            if hd_shifts[n]['Employee Name'] == '' or scan_shifts[scan_row]['Name'] == '':
                break

            # skips iterating over each shift of a student's multiple shifts occurring consecutively
            if shift_count >= n:
                continue
            shift_count = -1  # reset shift counter if this is the first shift of multiple consecutive shifts

            # shift dates set to datetime.strptime objects are returned to strings for readability and so start_time,
            # end_time, and set_duration can be set properly
            hd_shifts[n]['Date'] = hd_shifts[n]['Date'].strftime('%x')

            while hd_shifts[n]['Employee Name'] != scan_shifts[scan_row]['Name'] and \
                    hd_shifts[n]['Employee Name'] != scan_shifts[scan_row - 1]['Name']:
                scan_row += 1

            # if scanned shift clock in occurs over 15 minutes before the earliest shift time in Service Desk Schedule,
            # it is ignored because there is no shift in Service Desk Schedule to compare it to, prevents method failing
            while datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['In'], '%x%H:%M') < \
                    earliest_shift - timedelta(minutes=15):
                scan_row += 1  # increment scan_row by 1 to analyze next shift of Scanner Data
                continue

            # sets variables for time in, start time, end time, and duration of the shift from info in hd export
            time_in = datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['In'], '%x%H:%M')
            start_time = datetime.strptime(hd_shifts[n]['Date'] + hd_shifts[n]['Start Time'], '%x%H:%M')
            end_time = datetime.strptime(hd_shifts[n]['Date'] + hd_shifts[n]['End Time'], '%x%H:%M')
            set_duration = end_time - start_time

            # case: student clocks in when they were not scheduled for a shift at that time
            # checks if the clock in is not within 1 hour in either direction of the scheduled shift start time
            # if so, it checks if the scheduled start time is later (in date or time) than the clocked time in
            # if true, it counts the original scanned shift as a shift they were not assigned to
            # if false, it continues down to where it is marked as a skipped shift
            if not start_time - timedelta(hours=1) <= time_in <= start_time + timedelta(hours=1):
                while start_time > time_in and hd_shifts[n]['Employee Name'] == scan_shifts[scan_row]['Name']:
                    scan_row += 1
                    time_in = datetime.strptime(scan_shifts[scan_row]['Date'] +
                                                scan_shifts[scan_row]['In'], '%x%H:%M')

            # case: student forgets to clock out (time out value is empty)
            # forgetting to clock in but then clocking out will be read by the scanner as forgetting to clock out
            if scan_shifts[scan_row]['Out'] == '' and hd_shifts[n]['Date'] == scan_shifts[scan_row]['Date']:
                cause = 'Forgot to clock in or out'
                # updates the Flagged Shifts sheet with info about that shift
                flag_list.append(dict(
                    zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                # if student forgets to clock out on a multiple shift
                while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n + 1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the Flagged Shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                scan_row += 1
                continue

            # case: student skips entire shift or forgets to clock in AND out
            if not start_time - timedelta(minutes=10) <= time_in <= start_time + timedelta(minutes=20):
                cause = 'Skipped shift'
                # updates the Flagged Shifts sheet with info about that shift
                flag_list.append(
                    dict(zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=True))))

                # if student forgets to clock out on a multiple shift
                while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n + 1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the Flagged Shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=True))))
                continue

            # sets variables for time out and duration of the shift from RFID entry in Scanner Data
            time_out = datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['Out'], '%x%H:%M')
            actual_duration = time_out - time_in

            # case: student works multiple shifts in a row
            while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                    hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                    hd_shifts[n + 1]['Employee Name']:
                n += 1
                end_time = datetime.strptime(hd_shifts[n]['Date'] + hd_shifts[n]['End Time'], '%x%H:%M')
                set_duration = end_time - start_time
                actual_duration = time_out - time_in
                shift_count = n

            # two cases: late or short shift
            if time_in > start_time + timedelta(minutes=8) or \
                    actual_duration < set_duration - timedelta(minutes=8):
                # case: student is late
                if time_in > start_time + timedelta(minutes=8):
                    cause = 'Late'
                    # updates the Flagged Shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                # case: student leaves early and/or has shorter shift than scheduled
                else:
                    cause = 'Short shift'
                    # updates the Flagged Shifts sheet with info about that shift
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

            scan_row += 1

        # adds shifts already in Flagged Shifts to flag_list, which will be posted to Flagged Shifts
        for shift in flag_shifts:
            flag_list.append(shift)
        # adds the list of dictionaries in flag_list into a usable format for sheets as 'cell_list'
        # cell_list posts all "bad" shifts to the Flagged Shifts sheet at once using 'update_cells' function of gspread
        cell_list = gsheet_flagged_shifts.range(2, 1, len(flag_list) + 2, 8)

        # setting shift date to a datetime object so it can be sorted by date as strings don't sort by date properly
        for shift in flag_list:
            if isinstance(shift['Date'], str):
                shift['Date'] = datetime.strptime(shift['Date'], '%x')

        # sorting the shifts in Flagged Shifts by name, date, and start time
        flag_list = self.multi_key_sort(flag_list, ['Employee Name', 'Date', 'Start Time'])

        # setting each shift in the list to a cell in the Flagged Shifts sheet, then updating the cells of the sheet
        for shift in flag_list:
            shift['Date'] = shift['Date'].strftime('%x')
            index = flag_list.index(shift)
            cell_list[index * 8].value = shift['Shift ID']
            cell_list[index * 8 + 1].value = shift['Date']
            cell_list[index * 8 + 2].value = shift['Start Time']
            cell_list[index * 8 + 3].value = shift['End Time']
            cell_list[index * 8 + 4].value = shift['Employee Name']
            cell_list[index * 8 + 5].value = shift['In']
            cell_list[index * 8 + 6].value = shift['Out']
            cell_list[index * 8 + 7].value = shift['Issue']

        # clear Flagged Shifts sheet data prior to a new run-through of the shifts
        self.reset_sheet_data(gsheet_flagged_shifts, 8)

        # re-add flagged shifts with new data to Flagged Shifts sheet
        gsheet_flagged_shifts.update_cells(cell_list)

        # clear Scanner Data sheet data prior to re-adding unused shifts
        self.reset_sheet_data(gsheet_scanner_data, 4)

        # updates cells in Scanner Data from row 2 thru the length of copy_list
        cell_list = gsheet_scanner_data.range(2, 1, len(copy_list) + 2, 4)
        # re-adds shifts to Scanner Data that were not analyzed by the method
        for shift in copy_list:
            if not isinstance(shift['Date'], str):
                shift['Date'] = shift['Date'].strftime('%x')
            shift['In'] = self.convert_time_format(shift['In'], 12)
            shift['Out'] = self.convert_time_format(shift['Out'], 12)
            index = copy_list.index(shift)
            cell_list[index * 4].value = shift['Name']
            cell_list[index * 4 + 1].value = shift['Date']
            cell_list[index * 4 + 2].value = shift['In']
            cell_list[index * 4 + 3].value = shift['Out']
        gsheet_scanner_data.update_cells(cell_list)  # appends to Scanner Data sheet

        # clears the collected data for the Scanner Data and Service Desk Schedule sheets, respectively
        self.reset_sheet_data(gsheet_sd_schedule, 5)
