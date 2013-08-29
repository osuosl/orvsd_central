$(function() {
    $('#site').change(function() {
        $("#selected-names").empty();
        $('#site option:selected').each(function() {
            $.get('/get_site_by/' + $(this).val(), function(data) {
                $("#selected-names").append("Name: <i>" + data.name + "</i></br>");
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
