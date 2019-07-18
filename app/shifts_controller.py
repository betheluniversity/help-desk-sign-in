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
flagged_items = client.open('help_desk_sign_in').worksheet('flagged_items')
# accesses info from python_input, which takes in clock in/out info from RFID scanner
python = client.open('help_desk_sign_in').worksheet('python_input')
# accesses info from hd_export, where the manager posts his expected shift schedule
export = client.open('help_desk_sign_in').worksheet('hd_export')


class ShiftsController:
    def __init__(self):
        # initializing sheet objects and lists for reading and writing from Google Sheets
        # variables with '.get_all.records()' are lists of dictionaries from their respective sheets
        self.fi = flagged_items.get_all_records()
        # a list of dicts of info gathered from python_input sheet
        self.scanner_shifts = python.get_all_records()
        # a list of dicts of info gathered from hd_export sheet
        self.help_desk = export.get_all_records()

    def check_roles_and_route(self, allowed_roles):
        for role in allowed_roles:
            if role in flask_session['USER-ROLES']:
                return True
            abort(403)

    def student_sign_in(self, clock_type):  # , username):
        timestamp = datetime.now()
        time = timestamp.strftime('%I:%M %p')
        if time[0] == '0':
            time = time[1:]
        print(time)
        cell_list = python.range(3, 1, 3, 8)
        cell_list[0].value = ''  # pass in username
        cell_list[1].value = timestamp.strftime('%x')

        if clock_type == 'sign in':
            cell_list[2].value = time
        else:  # clock_type == 'sign out'
            cell_list[3].value = time
        python.update_cells(cell_list)

    # method called by multi_key_sort to compare and sort multiple keys in a dictionary
    def cmp(self, a, b):
        return (a > b) - (a < b)

    # method compares keys in a list of dictionaries to sort in ascending or descending order
    # items: the list of dictionaries
    # columns: the keys being sorted, in order of desired sort
    # method found at https://tinyurl.com/y2m6wuzr
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

    # method converts a time-string from 12-hour format to 24-hour format
    # converting times to 24-hour format because they sort chronologically much easier
    def convert24(self, str1):
        # if time slot is empty
        if str1 == '':
            return ''
        d = datetime.strptime(str1, '%I:%M %p')
        return d.strftime('%H:%M')

    # method converts a time-string from 24-hour format to 12-hour format
    # converting times back to 12-hour format for easier readability
    def convert12(self, str1):
        # if time slot is empty
        if str1 == '':
            return ''
        d = datetime.strptime(str1, '%H:%M')
        if d.strftime('%I:%M %p')[0] == '0':
            return d.strftime('%I:%M %p')[1:]
        return d.strftime('%I:%M %p')

    # method resets the flagged_items sheet upon each new running of the program
    def reset_flagged(self):
        cell_reset = flagged_items.range(2, 1, len(self.fi)+1, 8)
        for cell in cell_reset:
            cell.value = ''
        flagged_items.update_cells(cell_reset)
        return

    # method resets the python_input sheet upon the clicking of the web-page button
    def reset_py_data(self):
        cell_reset = python.range(2, 1, len(self.scanner_shifts)+1, 4)
        for cell in cell_reset:
            cell.value = ''
        python.update_cells(cell_reset)
        return

    # method updates a row of cells in flagged_items with info on any bad shifts
    def flagged_cells(self, hd_export, py_input, hd_row, py_row, flag_num, skipped):
        cell_list = flagged_items.range(flag_num, 1, flag_num, 8)
        cell_list[0].value = hd_export[hd_row]['Shift ID']
        cell_list[1].value = hd_export[hd_row]['Date']
        cell_list[2].value = self.convert12(hd_export[hd_row]['Start Time'])
        cell_list[3].value = self.convert12(hd_export[hd_row]['End Time'])
        cell_list[4].value = hd_export[hd_row]['Employee Name']
        if skipped:  # if true, time in and out values are printed to flagged_items as empty strings
            cell_list[5].value = ''
            cell_list[6].value = ''
        else:  # if false, time in and out values are printed to flagged_items as is
            cell_list[5].value = self.convert12(py_input[py_row]['In'])
            cell_list[6].value = self.convert12(py_input[py_row]['Out'])
        flagged_items.update_cells(cell_list)
        return

    def shift_generator(self, hd_export, py_input):
        # converts times in hd_export to 24-hour format and sorts out empty shifts
        for item in hd_export:
            # empty shifts set as 'zz - empty' to put them at the bottom of the alphabetical sort
            if item['Employee Name'] == '':
                item['Employee Name'] = 'zz - empty'
            if item['Start Time'][-1] != 'M':
                continue
            if item['End Time'][-1] != 'M':
                continue
            item['Start Time'] = self.convert24(item['Start Time'])
            item['End Time'] = self.convert24(item['End Time'])

        # converts times in py_input to 24-hour format
        for item in py_input:
            # TODO: Comparing user-names in py_input to names in hd_export
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

        # sorts hd_export and py_input dictionaries in order of name, then date, then start/clock-in time
        hd_export = self.multi_key_sort(hd_export, ['Employee Name', 'Date', 'Start Time'])
        py_input = self.multi_key_sort(py_input, ['Username', 'Date', 'In'])

        # determines what row of 'flagged_items' to update for a new flagged item, beginning at row 2
        flag_count = 2
        # tracks the correct row number for RFID time in and out, taking into account possible extra shifts
        p = 0
        # tracks the current part of the extra shift(s)
        shift_count = -1

        self.reset_flagged()

        # loops through all information in the hd_export and py_input lists of dictionaries of shift info
        for n in range(0, len(hd_export)):
            # if name value is empty, this ends the loop and all shifts have been documented
            if hd_export[n]['Employee Name'] == 'zz - empty':
                break

            # skips iterating over each shift of a student's multiple shifts in a row
            if shift_count >= n:
                continue
            shift_count = -1  # reset shift counter if this is the first shift in a row

            # sets variables for time in, start time, end time, and duration of the shift from manager's info in hd
            # export
            time_in = datetime.strptime(py_input[p]['Date']+py_input[p]['In'], '%x%H:%M')
            start_time = datetime.strptime(hd_export[n]['Date']+hd_export[n]['Start Time'], '%x%H:%M')
            end_time = datetime.strptime(hd_export[n]['Date']+hd_export[n]['End Time'], '%x%H:%M')
            set_duration = end_time - start_time

            # case: student clocks in and out when they were not scheduled for a shift at that time
            if not start_time - timedelta(minutes=60) <= time_in <= start_time + timedelta(minutes=60):
                if start_time - timedelta(minutes=10) <= \
                        datetime.strptime(py_input[p+1]['Date']+py_input[p+1]['In'], '%x%H:%M') \
                        <= start_time + timedelta(minutes=15):
                    p += 1
                    time_in = datetime.strptime(py_input[p]['Date'] + py_input[p]['In'], '%x%H:%M')
                else:
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=True)
                    flag_count += 1

                    # if student forgets to clock out on a multiple shift
                    while hd_export[n]['Date'] == hd_export[n + 1]['Date'] and hd_export[n]['End Time'] == \
                            hd_export[n + 1]['Start Time'] and hd_export[n]['Employee Name'] == \
                            hd_export[n + 1]['Employee Name']:
                        n += 1
                        shift_count = n
                        # updates the flagged_items sheet with info about that shift
                        self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=True)
                        flag_count += 1
                    continue

            # case: student forgets to clock out (time out value is empty)
            # note: forgetting to clock in but then clocking out will be read by the scanner as forgetting to clock out
            if py_input[p]['Out'] == '':
                # updates the flagged_items sheet with info about that shift
                self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=False)
                flag_count += 1

                # if student forgets to clock out on a multiple shift
                while end_time == datetime.strptime(hd_export[n]['Date']+hd_export[n+1]['Start Time'], '%x%H:%M') and \
                        hd_export[n]['Employee Name'] == hd_export[n+1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=False)
                    flag_count += 1

                p += 1
                continue

            # case: student skips entire shift or forgets to clock in AND out
            if not start_time - timedelta(minutes=10) <= time_in <= start_time + timedelta(minutes=15):
                # updates the flagged_items sheet with info about that shift
                self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=True)
                flag_count += 1

                # if student forgets to clock out on a multiple shift
                while hd_export[n]['Date'] == hd_export[n + 1]['Date'] and hd_export[n]['End Time'] == \
                        hd_export[n + 1]['Start Time'] and hd_export[n]['Employee Name'] == \
                        hd_export[n + 1]['Employee Name']:
                    n += 1
                    shift_count = n
                    # updates the flagged_items sheet with info about that shift
                    self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=True)
                    flag_count += 1
                continue

            # sets variables for time out and duration of the shift from RFID entry in python_input
            time_out = datetime.strptime(py_input[p]['Date']+py_input[p]['Out'], '%x%H:%M')
            actual_duration = time_out - time_in

            # case: student works multiple shifts in a row
            while hd_export[n]['Date'] == hd_export[n+1]['Date'] and hd_export[n]['End Time'] == \
                    hd_export[n+1]['Start Time'] and hd_export[n]['Employee Name'] == hd_export[n+1]['Employee Name']:
                n += 1
                end_time = datetime.strptime(hd_export[n]['Date']+hd_export[n]['End Time'], '%x%H:%M')
                set_duration = end_time - start_time
                actual_duration = time_out - time_in
                shift_count = n

            # case: student is late or leaves early
            if time_in > start_time + timedelta(minutes=8) or \
                    actual_duration < set_duration - timedelta(minutes=8):
                # updates the flagged_items sheet with info about that shift
                self.flagged_cells(hd_export, py_input, n, p, flag_count, skipped=False)
                flag_count += 1

            p += 1

        self.reset_py_data()
        return
