$(function() {
    $('#site').change(function() {
        var gah = $('#site option:selected').val();
        $.get('/get_site_by/' + gah, function(data) {
            $('#address').html("Address: <i>" + data.address + "</i>");
        });
    });
});
