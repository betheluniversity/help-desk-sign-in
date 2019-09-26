# Global
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Packages
import datetime
from datetime import datetime
from datetime import timedelta
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


class ShiftsController:
    # enters clock ins and outs into Scanner Data sheet, taking in card ID, returning if clock in/out was successful
    def student_time_clock(self, card_id):
        current_time = datetime.now().strftime('%-I:%M %p')
        current_date = datetime.now().strftime('%x')

        # tracks whether an ID scan has matched with a user in Student Employees, clocking in/out or displaying an error
        matched_id = False

        # refreshes list of scanned shifts and list of students and their card IDs
        scanner_data_list = self.refresh_shifts(gsheet_scanner_data)
        sd_students_list = self.refresh_shifts(gsheet_sd_students)

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

    # refresh a sheet to ensure shifts in student_time_clock, day_list, or shift_processor are up to date
    def refresh_shifts(self, sheet):
        client.login()  # refresh Sheets API OAuth access token to prevent 401 error
        return sheet.get_all_records()

    def day_list(self):
        current_date = datetime.now().strftime('%x')
        day_list = []
        scanner_data_list = self.refresh_shifts(gsheet_scanner_data)
        for shift in scanner_data_list:
            if shift['Date'] == current_date:
                day_list.append(shift)
        day_list.reverse()
        return day_list  # display list of today's shifts on student time clock page

    # compares keys in a list of dictionaries to sort in ascending or descending order
    # items: the list of dictionaries; columns: the keys being sorted, in order of desired sort
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

    def convert_time_format(self, convert_time, time_format):
        if convert_time == '':
            return ''
        if time_format == 24:  # convert time-string to 24-hour format for chronological sorting
            try:  # create datetime object in form of 12:00 PM
                return datetime.strptime(convert_time, '%I:%M %p').strftime('%H:%M')
            except ValueError:  # if 'AM/PM' is not included, create datetime object in form of 12:00
                return datetime.strptime(convert_time, '%I:%M %p').strftime('%H:%M')
        else:  # convert time-string to 12-hour format for easier readability
            return datetime.strptime(convert_time, '%H:%M').strftime('%-I:%M %p')

    # clears specified number of cell columns in a specified sheet and resets their values to empty strings
    def reset_sheet_data(self, sheet, cols):
        # append data to row of current length of specified sheet + 1
        list_row_length = len(sheet.get_all_records()) + 1
        cell_reset = sheet.range(2, 1, list_row_length, cols)
        for cell in cell_reset:
            cell.value = ''
        sheet.update_cells(cell_reset)

    def flagged_cells(self, hd_shifts, scan_shifts, hd_row, scan_row, reason, skipped):
        flag_val = [hd_shifts[hd_row]['Shift ID'], hd_shifts[hd_row]['Date'],
                    self.convert_time_format(hd_shifts[hd_row]['Start Time'], 12),
                    self.convert_time_format(hd_shifts[hd_row]['End Time'], 12), hd_shifts[hd_row]['Employee Name']]

        if skipped:
            flag_val.append('')
            flag_val.append('')
        else:
            flag_val.append(self.convert_time_format(scan_shifts[scan_row]['In'], 12))
            flag_val.append(self.convert_time_format(scan_shifts[scan_row]['Out'], 12))

        flag_val.append(reason)
        return flag_val  # updates a row of cells in Flagged Shifts sheet with info on any "bad" shifts

    # runs the comparison between Service Desk Schedule and Scanner Data to determine "bad" shifts
    def shift_processor(self):
        flag_shifts = self.refresh_shifts(gsheet_flagged_shifts)
        scan_shifts = self.refresh_shifts(gsheet_scanner_data)
        hd_shifts = self.refresh_shifts(gsheet_sd_schedule)

        scan_row = 0  # tracks the correct row number for scanner time in and out
        shift_count = -1  # tracks the current part of the extra shift(s)
        lower_bound = -1
        upper_bound = -1

        # creates keys for the list of dictionaries titled 'flag_list'
        flag_key = ['Shift ID', 'Date', 'Start Time', 'End Time', 'Employee Name', 'In', 'Out', 'Issue']
        flag_list = []

        hd_shifts = [shift for shift in hd_shifts if not shift['Employee Name'] == '']  # remove empty shifts

        earliest_shift = datetime.strptime(hd_shifts[0]['Date'] +
                                           self.convert_time_format(hd_shifts[0]['Start Time'], 24), '%x%H:%M')
        latest_shift = datetime.strptime(
            hd_shifts[0]['Date'] + self.convert_time_format(hd_shifts[0]['Start Time'], 24),
            '%x%H:%M')

        for shift in hd_shifts:
            shift_date = shift['Date']
            shift['Date'] = datetime.strptime(shift['Date'], '%x')
            try:  # convert hd_shifts to 24-hour format
                shift['Start Time'] = self.convert_time_format(shift['Start Time'], 24)
                shift['End Time'] = self.convert_time_format(shift['End Time'], 24)
            except TypeError:
                pass
            if datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M') < earliest_shift:
                earliest_shift = datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M')
            if datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M') > latest_shift:
                latest_shift = datetime.strptime(shift_date + shift['Start Time'], '%x%H:%M')

        for shift in scan_shifts:
            try:  # convert scan_shifts to 24-hour format
                shift['In'] = self.convert_time_format(shift['In'], 24)
                shift['Out'] = self.convert_time_format(shift['Out'], 24)
            except TypeError:
                pass

        # copy shifts not in time range to be ignored by comparison
        copy_list = [shift for shift in scan_shifts if not earliest_shift - timedelta(minutes=30) <=
                     datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M') <= latest_shift + timedelta(minutes=30)]

        # removing shifts from scan_shifts not within the date range of earliest through latest shift in hd_shifts
        scan_shifts = [shift for shift in scan_shifts if earliest_shift - timedelta(minutes=30) <=
                       datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M') <=
                       latest_shift + timedelta(minutes=30)]

        for shift in scan_shifts:
            this_shift = datetime.strptime(shift['Date'] + shift['In'], '%x%H:%M')
            shift['Date'] = datetime.strptime(shift['Date'], '%x')
            if earliest_shift - timedelta(minutes=30) <= this_shift <= latest_shift + timedelta(minutes=30):
                if lower_bound < 0:
                    lower_bound = scan_shifts.index(shift)
                while upper_bound < scan_shifts.index(shift):
                    upper_bound = scan_shifts.index(shift)

        hd_shifts = self.multi_key_sort(hd_shifts, ['Employee Name', 'Date', 'Start Time'])
        scan_shifts = self.multi_key_sort(scan_shifts, ['Name', 'Date', 'In'])

        # append empty shifts to prevent IndexError out of bounds when checking for multiple shifts
        hd_shifts.insert(len(hd_shifts),
                         {'Shift ID': '', 'Date': '', 'Start Time': '', 'End Time': '', 'Employee Name': ''})
        scan_shifts.insert(len(scan_shifts), {'Name': '', 'Date': '', 'In': '', 'Out': ''})

        for shift in scan_shifts:
            if not isinstance(shift['Date'], str):
                shift['Date'] = shift['Date'].strftime('%x')  # return scan_shifts dates to strings

        for n in range(0, len(hd_shifts)):
            # end loop once all shifts have been documented
            if hd_shifts[n]['Employee Name'] == '' or scan_shifts[scan_row]['Name'] == '':
                break

            if shift_count >= n:  # skips iterating over each shift of a student's consecutive shifts
                continue
            shift_count = -1  # reset shift counter if this is the first shift of multiple consecutive shifts

            hd_shifts[n]['Date'] = hd_shifts[n]['Date'].strftime('%x')  # return hd_shifts dates to strings

            while hd_shifts[n]['Employee Name'] != scan_shifts[scan_row]['Name'] and \
                    hd_shifts[n]['Employee Name'] != scan_shifts[scan_row - 1]['Name']:
                scan_row += 1

            # if scanned shift clock occurs 15+ minutes before the earliest shift time, ignore and continue
            while datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['In'], '%x%H:%M') < \
                    earliest_shift - timedelta(minutes=15):
                scan_row += 1
                continue

            time_in = datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['In'], '%x%H:%M')
            start_time = datetime.strptime(hd_shifts[n]['Date'] + hd_shifts[n]['Start Time'], '%x%H:%M')
            end_time = datetime.strptime(hd_shifts[n]['Date'] + hd_shifts[n]['End Time'], '%x%H:%M')
            set_duration = end_time - start_time

            # if student clocks in when they were not scheduled for a shift at that time
            if not start_time - timedelta(hours=1) <= time_in <= start_time + timedelta(hours=1):
                while start_time > time_in and hd_shifts[n]['Employee Name'] == scan_shifts[scan_row]['Name']:
                    scan_row += 1
                    time_in = datetime.strptime(scan_shifts[scan_row]['Date'] +
                                                scan_shifts[scan_row]['In'], '%x%H:%M')

            if scan_shifts[scan_row]['IP Address'] != '140.88.175':
                cause = 'Invalid IP: Did not sign in at Service Desk'
                flag_list.append(dict(
                    zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n + 1]['Employee Name']:  # user works multiple shifts in a row
                    n += 1
                    shift_count = n

                scan_row += 1
                continue

            if scan_shifts[scan_row]['Out'] == '' and hd_shifts[n]['Date'] == scan_shifts[scan_row]['Date']:
                cause = 'Forgot to clock in or out'
                flag_list.append(dict(
                    zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n + 1]['Employee Name']:  # user works multiple shifts in a row
                    n += 1
                    shift_count = n
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                scan_row += 1
                continue

            if not start_time - timedelta(minutes=10) <= time_in <= start_time + timedelta(minutes=20):
                cause = 'Skipped shift'  # also if student forgets to clock in AND out
                flag_list.append(
                    dict(zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=True))))

                while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                        hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                        hd_shifts[n + 1]['Employee Name']:  # user works multiple shifts in a row
                    n += 1
                    shift_count = n
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=True))))
                continue

            time_out = datetime.strptime(scan_shifts[scan_row]['Date'] + scan_shifts[scan_row]['Out'], '%x%H:%M')
            actual_duration = time_out - time_in

            # if student works multiple shifts in a row
            while hd_shifts[n]['Date'] == hd_shifts[n + 1]['Date'] and hd_shifts[n]['End Time'] == \
                    hd_shifts[n + 1]['Start Time'] and hd_shifts[n]['Employee Name'] == \
                    hd_shifts[n + 1]['Employee Name']:
                n += 1
                end_time = datetime.strptime(hd_shifts[n]['Date'] + hd_shifts[n]['End Time'], '%x%H:%M')
                set_duration = end_time - start_time
                actual_duration = time_out - time_in
                shift_count = n

            if time_in > start_time + timedelta(minutes=8) or \
                    actual_duration < set_duration - timedelta(minutes=8):
                # if student is late
                if time_in > start_time + timedelta(minutes=8):
                    cause = 'Late'
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

                # if student leaves early and/or has shorter shift than scheduled
                else:
                    cause = 'Short shift'
                    flag_list.append(dict(
                        zip(flag_key, self.flagged_cells(hd_shifts, scan_shifts, n, scan_row, cause, skipped=False))))

            scan_row += 1

        for shift in flag_shifts:
            flag_list.append(shift)  # adds shifts already in Flagged Shifts to flag_list

        list_row_length = len(flag_list) + 2
        cell_list = gsheet_flagged_shifts.range(2, 1, list_row_length, 8)

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

        self.reset_sheet_data(gsheet_flagged_shifts, 8)  # clear Flagged Shifts sheet prior to a new run-through
        gsheet_flagged_shifts.update_cells(cell_list)  # re-add flagged shifts with new data to Flagged Shifts sheet
        self.reset_sheet_data(gsheet_scanner_data, 5)  # clear Scanner Data sheet data prior to re-adding unused shifts

        list_row_length = len(copy_list) + 2
        cell_list = gsheet_scanner_data.range(2, 1, list_row_length, 4)

        # re-adds shifts to Scanner Data that were not analyzed by the method
        for shift in copy_list:
            if not isinstance(shift['Date'], str):
                shift['Date'] = shift['Date'].strftime('%x')  # returns copy_list shifts to strings
            shift['In'] = self.convert_time_format(shift['In'], 12)
            shift['Out'] = self.convert_time_format(shift['Out'], 12)
            index = copy_list.index(shift)
            cell_list[index * 4].value = shift['Name']
            cell_list[index * 4 + 1].value = shift['Date']
            cell_list[index * 4 + 2].value = shift['In']
            cell_list[index * 4 + 3].value = shift['Out']
        gsheet_scanner_data.update_cells(cell_list)  # appends to Scanner Data sheet

        self.reset_sheet_data(gsheet_sd_schedule, 5)  # clears Service Desk Schedule sheet
