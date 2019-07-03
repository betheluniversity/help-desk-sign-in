$(document).ready(function() {
    // Currently does nothing but display an in-browser alert when clicked
    $("#generate-shifts").click(function() {
       let input_data = {'clicked': 'true'};
       $.post('/generate_shifts', input_data, function(output_data) {
            // alert('CLICKED')
       });
       alert('CLICK')
    });
});