$(document).ready(function() {
    // Clicking the Process Shift Data button displays a loading GIF, triggers the shift_processor method in
    // shifts_controller.py, and returns an alert with the result of the method (success/failure)
    $("#process-shifts").click(function() {
        $('#resource-exhausted').hide();
        $('#processing-complete').hide();
        $('.spinner').show();
        let input_data = {};
        $.post('/process_shifts', input_data, function(output_data) {
            $('.spinner').hide();
            if (output_data === 'shift data processing complete') {
                $('#processing-complete').show();
            } else if (output_data === 'index error') {
                $('#index-error').show();
            } else {
                $('#resource-exhausted').show();
            }
        });
    });

    // Scanning a Bethel ID on the RFID scanner sends card ID data to views.py and subsequently the student_time_clock
    // method in shifts_controller.py, where it logs the time in/out and returns from views.py as a POST. Along with a
    // loading GIF, the time in/out is appended to the table in shifts_table.html
    let input = "";
    $(document).on('keydown', function(key) {
        if (key.keyCode === 13) {
            $('#time-clock-fail').hide();
            $('#resource-exhausted').hide();
            $('.spinner').show();
            let scanned_input = {
                'scan': input
            };
            $.post('/verify_scanner', scanned_input, function (scan_success) {
                $('.spinner').hide();
                if (scan_success !== 'failed' && scan_success !== 'resource exhausted' && scan_success !== 'no match') {
                    $('#time-clock-success').fadeTo(3000, 500).slideUp(500, function () {
                        $("#time-clock-success").slideUp(500);
                    });
                    $("#student-tbody").html(scan_success);
                } else if (scan_success === 'no match') {
                    $('#time-clock-no-match').fadeTo(3000, 500).slideUp(500, function() {
                        $("#time-clock-no-match").slideUp(500);
                    });
                } else if (scan_success === 'failed') {
                    $('#time-clock-fail').fadeTo(3000, 500).slideUp(500, function() {
                        $("#time-clock-fail").slideUp(500);
                    });
                } else {
                    $('#resource-exhausted').show();
                }
                input = "";
            });
        } else {
            input = input + key.key;
        }
    });
});