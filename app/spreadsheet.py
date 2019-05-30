# installed python packages
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# local
from app import app

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(app.config['INSTALL_LOCATION'], scope)
client = gspread.authorize(credentials)

worksheet = client.open('help_desk_sign_in')
sheet = client.open('help_desk_sign_in').sheet1

# help_desk = sheet.get_all_records()
# print(help_desk)

# row = ['maf28473', 'Matt Flynn', '54245', '6/12/18', '7:00', '2:00', '5']
# index = 5
# sheet.add_rows(1)
# sheet.insert_row(row, index)
# sheet.delete_row(5)
# print(sheet.row_count)
#
# print(sheet.row_values(4))
# print(sheet.row_values(2))
# print(sheet.cell(4, 6).value[-2:])
# if sheet.cell(4, 6).value[-2:] == 'PM':
#     print('afternoon')

if sheet.cell(3, 6).value[-2:] == 'AM' or 'PM':
    print('YES')

# clock_out = sheet.col_values(6)[1:]
# for out_time in clock_out:
#     print(out_time)

micah = sheet.row_values(2)[4:6]
for times in micah:
    print(times)

num_list = [1, 2, 3]
alpha_list = ['a', 'b', 'c']

# for number in num_list:
#     print(number)
#     for letter in alpha_list:
#         print(letter)
