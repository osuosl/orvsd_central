$(function() {
    $('#site').change(function() {
        $("#selected-addresses").empty();
        $('#site option:selected').each(function() {
            $.get('/get_site_by/' + $(this).val(), function(data) {
                $("#selected-addresses").append("Address: <i>" + data.address + "</i></br>");
            });
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
