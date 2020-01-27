# Global
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Packages
import datetime
from datetime import datetime, timedelta
from flask import request
from functools import cmp_to_key
from operator import itemgetter as i

# Local
from app import app

# gives access to Google Sheets and the Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['GS_CLIENT_SECRET'], scope)
client = gspread.authorize(credentials)
spreadsheet = client.open('Service Desk Sign-In Application')

# individual sheets of the Service Desk Sign-In Application spreadsheet
gsheet_flagged_shifts = spreadsheet.worksheet('Flagged Shifts (view only)')
gsheet_scanner_data = spreadsheet.worksheet('Scanner Data (view only)')
gsheet_sd_schedule = spreadsheet.worksheet('Service Desk Schedule')
gsheet_sd_students = spreadsheet.worksheet('Student Employees')


def refresh_shifts(sheet):
    client.login()  # refresh Sheets API OAuth access token to prevent 401 error
    return sheet.get_all_records()


def convert_time_format(convert_time, time_format):
    if convert_time == '':
        return ''
    if time_format == 24:  # convert time-string to 24-hour format for chronological sorting
        try:  # create datetime object in form of 12:00 PM
            return datetime.strptime(convert_time, '%I:%M %p').strftime('%H:%M')
        except ValueError:  # if 'AM/PM' is not included, create datetime object in form of 12:00
            return datetime.strptime(convert_time, '%I:%M %p').strftime('%H:%M')
    else:  # convert time-string to 12-hour format for easier readability
        return datetime.strptime(convert_time, '%H:%M').strftime('%-I:%M %p')


def prep_hd_shifts(earliest_shift, hd_shifts, latest_shift):
    for shift in hd_shifts:
        try:  # convert hd_shifts to 24-hour format
            shift['Start Time'] = convert_time_format(shift['Start Time'], 24)
            shift['End Time'] = convert_time_format(shift['End Time'], 24)
        except TypeError:
            pass
        # set earliest or latest shift to this shift
        if datetime.strptime(shift['Date'], '%x') < earliest_shift:
            earliest_shift = datetime.strptime(shift['Date'], '%x')
        if datetime.strptime(shift['Date'], '%x') > latest_shift:
            latest_shift = datetime.strptime(shift['Date'], '%x')
    return earliest_shift, latest_shift


def prep_scan_shifts(earliest_shift, latest_shift, lower_bound, scan_shifts, upper_bound):
    for shift in scan_shifts:
        this_shift = datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M')
        shift['Date'] = datetime.strptime(shift['Date'], '%x')
        if earliest_shift - timedelta(minutes=30) <= this_shift <= latest_shift + timedelta(minutes=30):
            if lower_bound < 0:  # sets lower bound to this shift
                lower_bound = scan_shifts.index(shift)
            while upper_bound < scan_shifts.index(shift):  # sets upper bound to this shift
                upper_bound = scan_shifts.index(shift)


# compares keys in a list of dictionaries to sort in ascending or descending order
# items: the list of dictionaries; columns: the keys being sorted, in order of desired sort
# found at https://tinyurl.com/y2m6wuzr
def multi_key_sort(items, columns):
    compare = [
        ((i(col[1:].strip()), -1) if col.startswith('-') else (i(col.strip()), 1))
        for col in columns
    ]

    def cmp(a, b):
        return (a > b) - (a < b)

    def comparer(left, right):
        comparer_iter = (
            cmp(fn(left), fn(right)) * multiply
            for fn, multiply in compare
        )
        return next((result for result in comparer_iter if result), 0)

    return sorted(items, key=cmp_to_key(comparer))


def return_to_string(shift_list):
    for shift in shift_list:
        if not isinstance(shift['Date'], str):
            shift['Date'] = shift['Date'].strftime('%x')  # return shift_list dates to strings


def flagged_cells(hd_shifts, scan_shifts, hd_row, scan_row, reason, skipped):
    flag_val = [hd_shifts[hd_row]['Shift ID'], hd_shifts[hd_row]['Date'],
                convert_time_format(hd_shifts[hd_row]['Start Time'], 12),
                convert_time_format(hd_shifts[hd_row]['End Time'], 12), hd_shifts[hd_row]['Employee Name']]
    if skipped:  # append empty strings so next shift's in and out are not appended
        flag_val.append('')
        flag_val.append('')
    else:
        flag_val.append(convert_time_format(scan_shifts[scan_row]['In'], 12))
        flag_val.append(convert_time_format(scan_shifts[scan_row]['Out'], 12))
    flag_val.append(reason)
    return flag_val  # updates a row of cells in Flagged Shifts sheet with array of information on a "bad" shift


def multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts, shift_count):
    if cause == 'Skipped shift':
        skipped = True
    else:
        skipped = False

    placeholder_row = hd_row  # setting current value of hd_row to a placeholder variable, to return to this value later
    while hd_shifts[hd_row]['Date'] == hd_shifts[hd_row + 1]['Date'] and hd_shifts[hd_row]['End Time'] == \
            hd_shifts[hd_row + 1]['Start Time'] and hd_shifts[hd_row]['Employee Name'] == \
            hd_shifts[hd_row + 1]['Employee Name']:  # user works multiple shifts in a row
        hd_row += 1
        shift_count = hd_row
    hd_shifts[placeholder_row]['End Time'] = hd_shifts[hd_row]['End Time']  # end time to last shift's end time in loop
    hd_row = placeholder_row

    flag_list.append(dict(
        zip(flag_key, flagged_cells(hd_shifts, scan_shifts, hd_row, scan_row, cause, skipped))))
    return shift_count


def prep_flag_list(cell_list, flag_list):
    for shift in flag_list:  # prep flagged shifts for posting to Flagged Shifts sheet
        shift['Start Time'] = convert_time_format(shift['Start Time'], 12)
        index = flag_list.index(shift)
        cell_list[index * 8].value = shift['Shift ID']
        cell_list[index * 8 + 1].value = shift['Date']
        cell_list[index * 8 + 2].value = shift['Start Time']
        cell_list[index * 8 + 3].value = shift['End Time']
        cell_list[index * 8 + 4].value = shift['Employee Name']
        cell_list[index * 8 + 5].value = shift['In']
        cell_list[index * 8 + 6].value = shift['Out']
        cell_list[index * 8 + 7].value = shift['Issue']


def reset_sheet_data(sheet, cols):
    # append data to row of current length of specified sheet + 1
    list_row_length = len(sheet.get_all_records()) + 1
    cell_reset = sheet.range(2, 1, list_row_length, cols)
    for cell in cell_reset:
        cell.value = ''  # clears cells in specified range of specified sheet
    sheet.update_cells(cell_reset)


# re-adds shifts to Scanner Data that were not analyzed by shift_processor method
def prep_copy_list(cell_list, copy_list):
    for shift in copy_list:
        shift['In'] = convert_time_format(shift['In'], 12)
        shift['Out'] = convert_time_format(shift['Out'], 12)
        index = copy_list.index(shift)
        cell_list[index * 5].value = shift['Name']
        cell_list[index * 5 + 1].value = shift['Date']
        cell_list[index * 5 + 2].value = shift['In']
        cell_list[index * 5 + 3].value = shift['Out']
        cell_list[index * 5 + 4].value = shift['IP Address']
    gsheet_scanner_data.update_cells(cell_list)  # appends to Scanner Data sheet


class ShiftsController:
    def student_time_clock(self, card_id):
        current_time = datetime.now().strftime('%-I:%M %p')
        current_date = datetime.now().strftime('%x')
        matched_id = False  # initialize whether card ID matched with student employee
        scanner_data_list = refresh_shifts(gsheet_scanner_data)
        sd_students_list = refresh_shifts(gsheet_sd_students)

        list_row_length = len(scanner_data_list) + 2  # append data to row of current length of Scanner Data sheet + 2
        # sets the range of cells in the sheet to append data in form (row start, col start, row end, col end)
        cell_list = gsheet_scanner_data.range(list_row_length, 1, list_row_length, 5)

        for user in sd_students_list:
            if user['Card ID'] == card_id:
                matched_id = True
                ip_address = request.environ['REMOTE_ADDR']
                for shift in scanner_data_list:
                    # if user has already signed in, treat scan as a clock out
                    if shift['Name'] == user['Name'] and shift['Out'] == '' and shift['Date'] == current_date:
                        list_row_length = scanner_data_list.index(shift) + 2
                        cell_list = gsheet_scanner_data.range(list_row_length, 1, list_row_length, 4)
                        cell_list[3].value = current_time
                        gsheet_scanner_data.update_cells(cell_list)
                        return matched_id
                cell_list[0].value = user['Name']
                cell_list[1].value = current_date
                cell_list[2].value = current_time
                cell_list[4].value = ip_address
                gsheet_scanner_data.update_cells(cell_list)  # appends scan info to Scanner Data sheet
                break
        return matched_id

    def day_list(self):
        current_date = datetime.now().strftime('%x')
        day_list = []
        scanner_data_list = refresh_shifts(gsheet_scanner_data)
        for shift in scanner_data_list:
            if shift['Date'] == current_date:
                day_list.append(shift)
        day_list.reverse()
        return day_list  # display list of today's shifts on student time clock page

    # runs the comparison between Service Desk Schedule and Scanner Data to determine "bad" shifts
    def shift_processor(self):
        flag_shifts = refresh_shifts(gsheet_flagged_shifts)
        scan_shifts = refresh_shifts(gsheet_scanner_data)
        hd_shifts = refresh_shifts(gsheet_sd_schedule)

        scan_row = 0  # tracks the correct row number for scanner time in and out
        last_shift = 0  # tracks the last shift to be analyzed successfully
        shift_count = -1  # tracks the current part of the extra shift(s)
        lower_bound = -1
        upper_bound = -1
        student_name_match = 'match successful'  # indicates student's name is present within hd_shifts & scan_shifts

        # creates keys for the list of dictionaries titled 'flag_list'
        flag_key = ['Shift ID', 'Date', 'Start Time', 'End Time', 'Employee Name', 'In', 'Out', 'Issue']
        flag_list = []

        hd_shifts = [shift for shift in hd_shifts if not shift['Employee Name'] == '']  # remove empty shifts

        earliest_shift = datetime.strptime(hd_shifts[0]['Date'], '%x')
        latest_shift = datetime.strptime(hd_shifts[0]['Date'], '%x')

        earliest_shift, latest_shift = prep_hd_shifts(earliest_shift, hd_shifts, latest_shift)

        for shift in scan_shifts:
            try:  # convert scan_shifts to 24-hour format
                shift['In'] = convert_time_format(shift['In'], 24)
                shift['Out'] = convert_time_format(shift['Out'], 24)
            except TypeError:
                pass

        # copy shifts not in time range to be ignored by comparison
        copy_list = [shift for shift in scan_shifts if not earliest_shift <= datetime.strptime(shift['Date'], '%x') <=
                     latest_shift]

        # removing shifts from scan_shifts not within the date range of earliest through latest shift in hd_shifts
        scan_shifts = [shift for shift in scan_shifts if earliest_shift <= datetime.strptime(shift['Date'], '%x') <=
                       latest_shift]

        prep_scan_shifts(earliest_shift, latest_shift, lower_bound, scan_shifts, upper_bound)

        hd_shifts = multi_key_sort(hd_shifts, ['Employee Name', 'Date', 'Start Time'])
        scan_shifts = multi_key_sort(scan_shifts, ['Name', 'Date', 'In'])

        # append empty shifts to prevent IndexError out of bounds when checking for multiple shifts
        hd_shifts.insert(len(hd_shifts),
                         {'Shift ID': '', 'Date': '', 'Start Time': '', 'End Time': '', 'Employee Name': ''})
        scan_shifts.insert(len(scan_shifts), {'Name': '', 'Date': '', 'In': '', 'Out': ''})

        return_to_string(hd_shifts)
        return_to_string(scan_shifts)

        for hd_row in range(0, len(hd_shifts)):
            # end loop once all shifts have been documented
            if hd_shifts[hd_row]['Employee Name'] == '' or scan_shifts[scan_row]['Name'] == '':
                break

            if shift_count >= hd_row:  # skips iterating over each shift of a student's consecutive shifts
                continue
            shift_count = -1  # reset shift counter if this is the first shift of multiple consecutive shifts

            while scan_shifts[scan_row]['Name'] not in hd_shifts[hd_row]['Employee Name'] and \
                    scan_shifts[scan_row - 1]['Name'] not in hd_shifts[hd_row]['Employee Name']:
                if scan_shifts[scan_row + 1]['Name'] == '' and student_name_match == 'no match':
                    scan_row = last_shift + 1
                    student_name_match = 'next shift empty'  # list of scan_shifts is done, name still not found
                    break
                student_name_match = 'no match'  # condition of the while loop has been met, student name not found yet
                scan_row += 1

            if student_name_match == 'next shift empty':  # list of students complete, skip hd_shift that caused issue
                student_name_match = 'match successful'  # return back to original value, analyze next hd_shift
                continue

            last_shift = scan_row
            time_in = datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['In'], '%x%H:%M')
            start_time = datetime.strptime(hd_shifts[hd_row]['Date'] + hd_shifts[hd_row]['Start Time'], '%x%H:%M')
            end_time = datetime.strptime(hd_shifts[hd_row]['Date'] + hd_shifts[hd_row]['End Time'], '%x%H:%M')
            set_duration = end_time - start_time

            # if clock-in not w/in 1.5 hours of the scheduled start, student clocked in when not scheduled
            if not start_time - timedelta(hours=1.5) <= time_in <= start_time + timedelta(hours=1.5):
                # while clock-in is more than 1.5 hours before scheduled start, check next shift until loop breaks
                while start_time - timedelta(hours=1.5) > time_in and hd_shifts[hd_row]['Employee Name'] == \
                        scan_shifts[scan_row]['Name']:
                    scan_row += 1
                    # ignore current shift and set time_in to next shift's time in
                    time_in = datetime.strptime(scan_shifts[scan_row]['Date'] +
                                                scan_shifts[scan_row]['In'], '%x%H:%M')

            if scan_shifts[scan_row]['IP Address'] != '140.88.175.144':
                cause = 'Invalid IP: Did not sign in at Service Desk'
                shift_count = multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts,
                                              shift_count)
                scan_row += 1
                continue

            if scan_shifts[scan_row]['Out'] == '' and hd_shifts[hd_row]['Date'] == scan_shifts[scan_row]['Date'] or \
                    end_time - timedelta(minutes=15) <= time_in <= end_time + timedelta(minutes=15):
                cause = 'Forgot to clock in or out'
                shift_count = multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts,
                                              shift_count)
                scan_row += 1
                continue

            if not start_time - timedelta(hours=1.5) <= time_in <= start_time + timedelta(hours=1.5):
                cause = 'Skipped shift'  # also if student forgets to clock in AND out
                shift_count = multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts,
                                              shift_count)
                continue

            time_out = datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['Out'], '%x%H:%M')
            actual_duration = time_out - time_in

            # if student works multiple shifts in a row
            placeholder_row = hd_row  # setting current value of hd_row to a placeholder variable, to return to it later
            while hd_shifts[hd_row]['Date'] == hd_shifts[hd_row + 1]['Date'] and hd_shifts[hd_row]['End Time'] == \
                    hd_shifts[hd_row + 1]['Start Time'] and hd_shifts[hd_row]['Employee Name'] == \
                    hd_shifts[hd_row + 1]['Employee Name']:
                hd_row += 1
                end_time = datetime.strptime(hd_shifts[hd_row]['Date'] + hd_shifts[hd_row]['End Time'], '%x%H:%M')
                set_duration = end_time - start_time
                actual_duration = time_out - time_in
                shift_count = hd_row
            hd_row = placeholder_row

            # student forgets to sign out and signs in later in the day, clock in is not clock out of old shift
            if end_time + timedelta(hours=1) < time_out and \
                    scan_shifts[scan_row]['Date'] == scan_shifts[scan_row + 1]['Date']:
                cause = 'Forgot to clock in or out'
                next_in = datetime.strptime(scan_shifts[scan_row + 1]['Date'] +
                                            scan_shifts[scan_row + 1]['In'], '%x%H:%M')
                if next_in - time_out >= timedelta(minutes=10):
                    # only replace next shift's out if next in isn't w/in 10 min of current shift's out
                    scan_shifts[scan_row + 1]['Out'] = scan_shifts[scan_row + 1]['In']
                scan_shifts[scan_row + 1]['In'] = scan_shifts[scan_row]['Out']
                scan_shifts[scan_row]['Out'] = ''
                shift_count = multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts,
                                              shift_count)
                scan_row += 1
                continue

            if time_in > start_time + timedelta(minutes=8):
                cause = 'Late'
                shift_count = multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts,
                                              shift_count)
                scan_row += 1
                continue

            if actual_duration < set_duration - timedelta(minutes=8):
                cause = 'Short shift'
                shift_count = multiple_shifts(cause, flag_key, flag_list, hd_shifts, hd_row, scan_row, scan_shifts,
                                              shift_count)
            scan_row += 1

        for shift in flag_shifts:
            flag_list.append(shift)  # adds shifts already in Flagged Shifts to flag_list

        list_row_length = len(flag_list) + 2
        cell_list = gsheet_flagged_shifts.range(2, 1, list_row_length, 8)

        return_to_string(flag_list)
        for shift in flag_list:
            try:
                shift['Start Time'] = convert_time_format(shift['Start Time'], 24)
            except TypeError:
                pass

        # sorting the shifts in Flagged Shifts by name, date, and start time
        flag_list = multi_key_sort(flag_list, ['Employee Name', 'Date', 'Start Time'])
        prep_flag_list(cell_list, flag_list)

        reset_sheet_data(gsheet_flagged_shifts, 8)  # clear Flagged Shifts sheet prior to a new run-through
        gsheet_flagged_shifts.update_cells(cell_list)  # re-add flagged shifts with new data to Flagged Shifts sheet
        reset_sheet_data(gsheet_scanner_data, 5)  # clear Scanner Data sheet data prior to re-adding unused shifts

        list_row_length = len(copy_list) + 2
        cell_list = gsheet_scanner_data.range(2, 1, list_row_length, 5)

        return_to_string(copy_list)
        prep_copy_list(cell_list, copy_list)
        reset_sheet_data(gsheet_sd_schedule, 5)  # clears Service Desk Schedule sheet
