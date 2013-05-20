$(function() {
    $('#site').change(function() {
        var site_id = $('#site option:selected').val();
        $.get('/get_site_by/' + site_id, function(data) {
            $('#address').html("Address: <i>" + data.address + "</i>");
        });
    });

    $('#course').change(function() {
        var html = "";
        $('#course option:selected').each(function() {
            html += $(this).text() + "<br />";
        });
        $("#selected-courses").html(html);
    });
});
