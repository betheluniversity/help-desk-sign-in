$(document).ready(function() {
    $("#generate-flagged").click(function() {
       let input_data = {'clicked': 'true'};
       $.post('/button_clicked', input_data, function(output_data) {
            alert('CLICKED');
       });
    });
});