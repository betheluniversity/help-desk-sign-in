$(document).ready(function() {
    // Clicking the Process Shift Data button displays a loading GIF, triggers the shift_processor method in
    // shifts_controller.py, and returns an alert with the result of the method (success/failure)
    $("#process-shifts").click(function() {
        $('.alert').hide();
        $('.spinner').show();
        let input_data = {};
        $.post('/process_shifts', input_data, function(data) {
            $('#show-alert').html(data);
            $('.spinner').hide();
            $('.alert').fadeTo(3000, 500).slideUp(500, function() {
                $('.alert').slideUp(500);
            });
        });
    });

    // Scanning a Bethel ID on the RFID scanner sends card ID data to views.py and subsequently the student_time_clock
    // method in shifts_controller.py, where it logs the time in/out and returns from views.py as a POST. Along with a
    // loading GIF, the time in/out is appended to the table in shifts_table.html
    let input = "";
    $(document).on('keydown', function(key) {
        if (key.keyCode === 13) {
            $('.alert').hide();
            $('.spinner').show();
            let scanned_input = {
                'scan': input
            };
            $.post('/verify_scanner', scanned_input, function(data) {
                $("#table-refresh").html(data);
                $('.spinner').hide();
                $('.alert').fadeTo(3000, 500).slideUp(500, function() {
                    $('.alert').slideUp(500);
                });
                input = "";
            });
        } else {
            input = input + key.key;
        }
    });
});