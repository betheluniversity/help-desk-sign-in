// Not currently working

$(document).ready(function() {
    let input = "";

    // RFID scanner info
    $(document).on('keydown', function(key) {
        if(key.keyCode == 13) {
            let url = "{{ url_for('ShiftsView:verify_scanner') }}";
            let scannedInput = {
                'scan': input
            };
            $.post(url, scannedInput, function(success) {
                if(success != 'failed') {
                    window.location.replace("{{ lab_base_url }}/session/no-cas/checkin/{{ session_info.id }}/{{ session_info.hash }}/" + success);
                } else {
                    input = "";
                }
            });
        } else {
            input = input + key.key;
        }
    });

    $("#generate-shifts").click(function() {
       let input_data = {'clicked': 'true'};
       $.post('/generate_shifts', input_data, function(output_data) {
            // alert('CLICKED')
       });
       alert('CLICK')
    });
});