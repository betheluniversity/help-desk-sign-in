$(document).ready(function() {
    // Clicking the Process Shift Data button displays a loading GIF, triggers the shift_processor method in
    // shifts_controller.py, and returns an alert with the result of the method (success / failure & why)
    $("#process-shifts").click(function() {
        $('#spinner').show();
        let input_data = {};
        $.post('/process_shifts', input_data, function() {
            $('#spinner').hide();
            $('.alert').show();
        });
    });

    // Scanning a Bethel ID on the RFID scanner sends card ID data to views.py and subsequently the student_time_clock
    // method in shifts_controller.py, where it logs the time in/out and returns from views.py as a POST. Along with a
    // loading GIF, the time in/out is appended to the table in student_table.html
    let input = "";
    $(document).on('keydown', function (key) {
        if (key.keyCode == 13) {
            $('#failed-alert').hide();
            $('#spinner').show();
            let scanned_input = {
                'scan': input
            };
            $.post('/verify_scanner', scanned_input, function (success) {
                $('#spinner').hide();
                if (success != 'failed') {
                    $("#student-tbody").html(success);
                    input = "";
                } else {
                    $('#failed-alert').show();
                    input = "";
                }
            });
        } else {
            input = input + key.key;
        }
    });
});