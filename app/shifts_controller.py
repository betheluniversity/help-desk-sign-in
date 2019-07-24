# Global
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Packages
import datetime
from datetime import datetime
from datetime import timedelta
from flask import abort
from flask import session as flask_session
from functools import cmp_to_key
from operator import itemgetter as i

# Local
from app import app

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['INSTALL_LOCATION'], scope)
client = gspread.authorize(credentials)

# variables with 'client.open' grant access to that specific sheet of the Help Desk Sign In Google Sheet
# 'flagged_items' stores the "bad" shifts of students when the scanned input is compared to their schedule
flagged_items = client.open('help_desk_sign_in').worksheet('flagged_items')
# 'rfid_input' stores the clock in/out info from the Help Desk RFID scanner, tracking student attendance
rfid_input = client.open('help_desk_sign_in').worksheet('scan_input')
# 'hd_export' stores where the manager posts his expected shift schedule, typically for a two-week period
hd_export = client.open('help_desk_sign_in').worksheet('hd_export')
# 'hd_users' stores where the site inputs student username and card ID info for shift comparisons
hd_users = client.open('help_desk_sign_in').worksheet('hd_users')


class ShiftsController:
    def __init__(self):
        # initializing sheet objects and lists for reading and writing from Google Sheets
        # variables with '.get_all.records()' are lists of dictionaries from their respective sheets
        self.fi = flagged_items.get_all_records()
        # a list of dicts of info gathered from scan_input sheet
        self.scanner_shifts = rfid_input.get_all_records()
        # a list of dicts of info gathered from hd_export sheet
        self.hd_shifts = hd_export.get_all_records()
        # a list of dicts of info gathered from hd_users sheet
        self.users = hd_users.get_all_records()

    # used to only allow admin access to staff and user pages of the site
    # def check_roles_and_route(self, allowed_roles):
    #     for role in allowed_roles:
    #         if role in flask_session['USER-ROLES']:
    #             return True
    #         abort(403)

    # enters clock ins and outs into 'scan_input' sheet
    def student_time_clock(self, clock_type, card_id):
        self.scanner_shifts = rfid_input.get_all_records()
        timestamp = datetime.now()
        time = timestamp.strftime('%I:%M %p')
        if time[0] == '0':
            time = time[1:]
        if clock_type == 'sign in':
            for user in self.users:
                if user['Card ID'] == card_id:
                    cell_list = rfid_input.range(len(self.scanner_shifts) + 2, 1, len(self.scanner_shifts) + 2, 4)
                    cell_list[0].value = user['Username']
                    cell_list[1].value = timestamp.strftime('%x')
                    cell_list[2].value = time
                    rfid_input.update_cells(cell_list)
                    return user['Name']
                else:
                    continue
        else:  # clock_type == 'sign out'
            cell_list = rfid_input.range(len(self.scanner_shifts) + 1, 1, len(self.scanner_shifts) + 1, 4)
            cell_list[3].value = time
            rfid_input.update_cells(cell_list)

    def users_list(self):
        users_list = hd_users.get_all_records()
        return users_list

    def shifts_list(self):
        shifts_list = rfid_input.get_all_records()
        return shifts_list

    # adds user info to the 'hd_users' sheet
    def add_users(self, student_name, username, card_id):
        self.users = hd_users.get_all_records()
        cell_list = hd_users.range(len(self.users)+2, 1, len(self.users)+2, 3)
        cell_list[0].value = username
        cell_list[1].value = student_name
        cell_list[2].value = card_id
        hd_users.update_cells(cell_list)

    # called by multi_key_sort to compare and sort multiple keys in a dictionary
    def cmp(self, a, b):
        return (a > b) - (a < b)

    # compares keys in a list of dictionaries to sort in ascending or descending order
    # items: the list of dictionaries
    # columns: the keys being sorted, in order of desired sort
    # found at https://tinyurl.com/y2m6wuzr
    def multi_key_sort(self, items, columns):
        comparers = [
            ((i(col[1:].strip()), -1) if col.startswith('-') else (i(col.strip()), 1))
            for col in columns
        ]

        def comparer(left, right):
            comparer_iter = (
                self.cmp(fn(left), fn(right)) * mult
                for fn, mult in comparers
            )
            return next((result for result in comparer_iter if result), 0)
        return sorted(items, key=cmp_to_key(comparer))

    # converts a time-string from 12-hour format to 24-hour format for sorting chronologically easier
    def convert24(self, str1):
        # if time slot is empty
        if str1 == '':
            return ''
        d = datetime.strptime(str1, '%I:%M %p')
        return d.strftime('%H:%M')

    # converts a time-string from 24-hour format to 12-hour format for easier readability
    def convert12(self, str1):
        # if time slot is empty
        if str1 == '':
            return ''
        d = datetime.strptime(str1, '%H:%M')
        if d.strftime('%I:%M %p')[0] == '0':
            return d.strftime('%I:%M %p')[1:]
        return d.strftime('%I:%M %p')

    # resets the 'flagged_items' sheet upon each new running of the program
    def reset_flagged(self):
        cell_reset = flagged_items.range(2, 1, len(self.fi)+1, 8)
        for cell in cell_reset:
            cell.value = ''
        flagged_items.update_cells(cell_reset)
        return

    # resets the 'scan_input' sheet upon each new running of the program
    def reset_scan_data(self):
        cell_reset = rfid_input.range(2, 1, len(self.scanner_shifts)+1, 4)
        for cell in cell_reset:
            cell.value = ''
        rfid_input.update_cells(cell_reset)
        return

    # updates a row of cells in 'flagged_items' with info on any "bad" shifts
    def flagged_cells(self, hd_input, scan_input, hd_row, scan_row, flag_num, reason, skipped):
        cell_list = flagged_items.range(flag_num, 1, flag_num, 8)
        cell_list[0].value = hd_input[hd_row]['Shift ID']
        cell_list[1].value = hd_input[hd_row]['Date']
        cell_list[2].value = self.convert12(hd_input[hd_row]['Start Time'])
        cell_list[3].value = self.convert12(hd_input[hd_row]['End Time'])
        cell_list[4].value = hd_input[hd_row]['Employee Name']
        if skipped:  # if true, time in and out values are printed to flagged_items as empty strings
            cell_list[5].value = ''
            cell_list[6].value = ''
        else:  # if false, time in and out values are printed to flagged_items as is
            cell_list[5].value = self.convert12(scan_input[scan_row]['In'])
            cell_list[6].value = self.convert12(scan_input[scan_row]['Out'])
        cell_list[7].value = reason
        flagged_items.update_cells(cell_list)
        return

    # runs the comparison between 'hd_export' and 'scanned_input' to determine "bad" shifts
    def shift_generator(self, hd_input, scan_input):
        # converts times in hd_input to 24-hour format and sorts out empty shifts
        for item in hd_input:
            # empty shifts set as 'zz - empty' to put them at the bottom of the alphabetical sort
            if item['Employee Name'] == '':
                item['Employee Name'] = 'zz - empty'
            if item['Start Time'][-1] != 'M':
                continue
            if item['End Time'][-1] != 'M':
                continue
            item['Start Time'] = self.convert24(item['Start Time'])
            item['End Time'] = self.convert24(item['End Time'])

        # converts times in scan_input to 24-hour format and usernames into full names
        for item in scan_input:
            # TODO: Comparing user-names in scan_input to names in hd_input
            # TODO: Inefficient and non-maintainable code currently, will need to fix later
            # TODO: Current setup exists for comparison in special cases
            if item['Username'] == 'matt-b':
                item['Username'] = 'Matt Barton'
            elif item['Username'] == 'micah-b':
                item['Username'] = 'Micah BigEagle'
            elif item['Username'] == 'nate-c':
                item['Username'] = 'Nate Chau'
            elif item['Username'] == 'joren-e':
                item['Username'] = 'Joren Eklund'
            elif item['Username'] == 'kim-e':
                item['Username'] = 'Kimberly Enemark'
            elif item['Username'] == 'matt-f':
                item['Username'] = 'Matt Flynn'
            elif item['Username'] == 'caleb-f':
                item['Username'] = 'Caleb Foster'
            elif item['Username'] == 'ryken-k':
                item['Username'] = 'Ryken Kreps'
            elif item['Username'] == 'kevin-k':
                item['Username'] = 'Kevin Krohn'
            elif item['Username'] == 'jared-l':
                item['Username'] = 'Jared Lundberg'
            elif item['Username'] == 'ryan-m':
                item['Username'] = 'Ryan McKimens'
            elif item['Username'] == 'jacques-p':
                item['Username'] = 'Jacques Perrault'
            elif item['Username'] == 'lindsay-p':
                item['Username'] = 'Lindsay Pila'
            elif item['Username'] == 'leif-r':
                item['Username'] = 'Leif Riveness'
            elif item['Username'] == 'trevor-v':
                item['Username'] = 'Trevor Vollendorf'
            elif item['Username'] == 'micah-w':
                item['Username'] = 'Micah Weiberg'

            if item['In'] == '':
                break
            elif item['In'][-1] != 'M':
                continue
            else:
                item['In'] = self.convert24(item['In'])
                item['Out'] = self.convert24(item['Out'])

        # sorts hd_input and scan_input dictionaries in order of name, then date, then start/clock-in time
        hd_input = self.multi_key_sort(hd_input, ['Employee Name', 'Date', 'Start Time'])
        scan_input = self.multi_key_sort(scan_input, ['Username', 'Date', 'In'])

        # determines what row of 'flagged_items' to update for a new flagged item, beginning at row 2
        flag_count = 2
        # tracks the correct row number for RFID time in and out, taking into account possible extra shifts
        p = 0
        # tracks the current part of the extra shift(s)
        shift_count = -1

        self.reset_flagged()

        # loops through all information in the hd_input and scan_input lists of dictionaries of shift info
        for n in range(0, len(hd_input)):
            # if name value is empty, this ends the loop and all shifts have been documented
            if hd_input[n]['Employee Name'] == 'zz - empty':
                break

            # skips iterating over each shift of a student's multiple shifts in a row
            if shift_count >= n:
                continue
            shift_count = -1  # reset shift counter if this is the first shift in a row

            # sets variables for time in, start time, end time, and duration of the shift from info in hd export
            time_in = datetime.strptime(scan_input[p]['Date']+scan_input[p]['In'], '%x%H:%M')
            start_time = datetime.strptime(hd_input[n]['Date']+hd_input[n]['Start Time'], '%x%H:%M')
            end_time = datetime.strptime(hd_input[n]['Date']+hd_input[n]['End Time'], '%x%H:%M')
            set_duration = end_time - start_time

            # case: student clocks in and out when they were not scheduled for a shift at that time
            if not start_time - timedelta(minutes=60) <= time_in <= start_time + timedelta(minutes=60):
                if start_time - timedelta(minutes=10) <= \
                        datetime.strptime(scan_input[p+1]['Date']+scan_input[p+1]['In'], '%x%H:%M') \
                        <= start_time + timedelta(minutes=15):
                    p += 1
                    time_in = datetime.strptime(scan_input[p]['Date'] + scan_input[p]['In'], '%x%H:%M')

            # case: student forgets to clock out (time out value is empty)
            # forgetting to clock in but then clocking out will be read by the scanner as forgetting to clock out
            if scan_input[p]['Out'] == '':
                cause = 'Forgot to clock in or out'
                # updates the flagged_items sheet with info about that shift
                self.flagged_cells(hd_input, scan_input, n, p, flag_count, cause, skipped=False)
                flag_count += 1

                # if student forgets to clock out on a multiple shift
                while end_time == datetime.strptime(hd_input[n]['Date']+hd_input[n+1]['Start Time'], '%x%H:%M') and \
                        hd_input[n]['Employee Name'] == hd_input[n+1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_input, scan_input, n, p, flag_count, cause, skipped=False)
                    flag_count += 1

                p += 1
                continue

            # case: student skips entire shift or forgets to clock in AND out
            if not start_time - timedelta(minutes=10) <= time_in <= start_time + timedelta(minutes=15):
                cause = 'Skipped or forgot to clock shift'
                # updates the flagged_items sheet with info about that shift
                self.flagged_cells(hd_input, scan_input, n, p, flag_count, cause, skipped=True)
                flag_count += 1

                # if student forgets to clock out on a multiple shift
                while hd_input[n]['Date'] == hd_input[n + 1]['Date'] and hd_input[n]['End Time'] == \
                        hd_input[n + 1]['Start Time'] and hd_input[n]['Employee Name'] == \
                        hd_input[n + 1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_input, scan_input, n, p, flag_count, cause, skipped=True)
                    flag_count += 1
                continue

            # sets variables for time out and duration of the shift from RFID entry in rfid_input
            time_out = datetime.strptime(scan_input[p]['Date']+scan_input[p]['Out'], '%x%H:%M')
            actual_duration = time_out - time_in

            # case: student works multiple shifts in a row
            while hd_input[n]['Date'] == hd_input[n+1]['Date'] and hd_input[n]['End Time'] == \
                    hd_input[n+1]['Start Time'] and hd_input[n]['Employee Name'] == hd_input[n+1]['Employee Name']:
                n += 1
                end_time = datetime.strptime(hd_input[n]['Date']+hd_input[n]['End Time'], '%x%H:%M')
                set_duration = end_time - start_time
                actual_duration = time_out - time_in
                shift_count = n

            # two cases: late or short shift
            if time_in > start_time + timedelta(minutes=8) or \
                    actual_duration < set_duration - timedelta(minutes=8):
                # case: student is late
                if time_in > start_time + timedelta(minutes=8):
                    cause = 'Late'
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_input, scan_input, n, p, flag_count, cause, skipped=False)
                    flag_count += 1

                # case: student leaves early and/or has shorter shift than scheduled
                else:
                    cause = 'Short shift'
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_input, scan_input, n, p, flag_count, cause, skipped=False)
                    flag_count += 1

            p += 1

        self.reset_scan_data()
        return
