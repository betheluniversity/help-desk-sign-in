# installed python packages
import gspread
import time
from datetime import datetime
from datetime import timedelta
from oauth2client.service_account import ServiceAccountCredentials

# local
from app import app

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['INSTALL_LOCATION'], scope)
client = gspread.authorize(credentials)

flagged_items = client.open('help_desk_sign_in').worksheet('flagged_items')
output = client.open('help_desk_sign_in').worksheet('output')

# determines what row of 'flagged_items' to update for a new flagged item, beginning at row 2
flag_count = 2
# tracks the correct row number for RFID time in and out, taking into account possible extra shifts
p = 2
# tracks the current part of the extra shift(s)
shift_count = -1

# loops through all information entered between the 'python_input' and 'hd_export' sheets from the spreadsheet
# python_input is information from the RFID scanner and hd_export is Justin's entered shift information
for n in range(2, output.row_count + 1):
    print('N = ')
    print(n)
    print('P = ')
    print(p)
    print(output.cell(n, 5).value)

    # if name value is empty, this ends the loop and all shifts have been documented
    if output.cell(n, 5).value == '':
        break

    # skips iterating over each shift of a student's multiple shifts in a row
    if shift_count >= n:
        continue
    shift_count = -1  # reset shift counter if the first shift in a row

    # case: student forgets to clock out (time out value is empty)
    if output.cell(p, 7).value == '':
        # updates the flagged_items sheet with information about that shift
        for col in range(1, 6):
            flagged_items.update_cell(flag_count, col, output.cell(n, col).value)
        for col in range(6, 8):
            flagged_items.update_cell(flag_count, col, output.cell(p, col).value)
        flagged_items.update_cell(flag_count, 8, 'FLAGGED')
        flag_count += 1

        # if student forgets to clock out on a multiple-shift
        while datetime.strptime(output.cell(n, 2).value+output.cell(n, 4).value, '%x%I:%M %p') == \
                datetime.strptime(output.cell(n+1, 2).value+output.cell(n+1, 3).value, '%x%I:%M %p') \
                and output.cell(n, 5).value == output.cell(n+1, 5).value:
            n += 1
            shift_count = n
            time.sleep(5)

        p += 1
        time.sleep(20)
        continue

    # sets variables for time in, time out, and duration of the shift from RFID entry in python_input
    time_in = datetime.strptime(output.cell(n, 2).value+output.cell(p, 6).value, '%x%I:%M:%S %p')
    time_out = datetime.strptime(output.cell(n, 2).value+output.cell(p, 7).value, '%x%I:%M:%S %p')
    actual_duration = time_out - time_in

    # sets variables for start time, end time, and duration of the shift from Justin's info in hd_export
    start_time = datetime.strptime(output.cell(n, 2).value+output.cell(n, 3).value, '%x%I:%M %p')
    end_time = datetime.strptime(output.cell(n, 2).value+output.cell(n, 4).value, '%x%I:%M %p')
    set_duration = end_time - start_time

    # case: student skips entire shift or forgets to clock in AND out
    if not start_time - timedelta(minutes=15) <= time_in <= start_time + timedelta(minutes=15):
        # Updates the flagged_items sheet with information about that shift
        for col in range(1, 6):
            flagged_items.update_cell(flag_count, col, output.cell(n, col).value)
        for col in range(6, 8):
            flagged_items.update_cell(flag_count, col, '')
        flagged_items.update_cell(flag_count, 8, 'FLAGGED')
        flag_count += 1

        # if student forgets to clock out on a multiple-shift
        # TODO: Want this to print out flagged status to flagged_items for each missed shift in a
        # TODO: multiple shift, currently not working properly
        while datetime.strptime(output.cell(n, 2).value+output.cell(n, 4).value, '%x%I:%M %p') == \
                datetime.strptime(output.cell(n+1, 2).value+output.cell(n+1, 3).value, '%x%I:%M %p') \
                and output.cell(n, 5).value == output.cell(n+1, 5).value:
            n += 1
            shift_count = n
            time.sleep(5)

        time.sleep(20)
        print('skipped shift')
        continue

    # case: student works multiple shifts in a row
    while end_time == datetime.strptime(output.cell(n+1, 2).value+output.cell(n+1, 3).value, '%x%I:%M %p')\
            and output.cell(n, 5).value == output.cell(n+1, 5).value:
        n += 1
        end_time = datetime.strptime(output.cell(n, 2).value+output.cell(n, 4).value, '%x%I:%M %p')
        set_duration = end_time - start_time
        actual_duration = time_out - time_in
        shift_count = n
        time.sleep(12)

    # case: student is late or leaves early
    if time_in > start_time + timedelta(minutes=8) or \
            actual_duration < set_duration - timedelta(minutes=8):
        # Updates the flagged_items sheet with information about that shift
        for col in range(1, 6):
            flagged_items.update_cell(flag_count, col, output.cell(n, col).value)
        for col in range(6, 8):
            flagged_items.update_cell(flag_count, col, output.cell(p, col).value)
        flagged_items.update_cell(flag_count, 8, 'FLAGGED')
        flag_count += 1

    p += 1
    time.sleep(20)
