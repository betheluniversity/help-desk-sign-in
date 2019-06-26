// Not currently working

$(document).ready(function() {
    $("#generate-shifts").click(function() {
       let input_data = {'clicked': 'true'};
       $.post('/generate_shifts', input_data, function(output_data) {
            // alert('CLICKED')
       });
       alert('CLICK')
    });
});