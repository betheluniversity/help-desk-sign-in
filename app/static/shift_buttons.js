// nothing here currently
// all JS code is currently in the HTML files for student_index, staff_index, and users_index
// could be moved here instead of how it currently resides in HTML files as <script>
$(document).ready(function() {
    $("#generate-shifts").click(function() {
        $('#spinner').show();
        let input_data = {};
        $.post('/generate_shifts', input_data, function() {
            $('#spinner').hide();
            $('.alert').show();
        });
    });
    let input = "";
    $(document).on('keydown', function (key) {
        if (key.keyCode == 13) {
            $('#failed-alert').hide();
            $('#spinner').show();
            let scannedInput = {
                'scan': input
            };
            $.post('/verify_scanner', scannedInput, function (success) {
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