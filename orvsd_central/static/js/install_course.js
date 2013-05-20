$(function() {
    $('#course').change(function() {
        var html = "";
        $('#course option:selected').each(function() {
            html += $(this).text() + "<br />";
        });
        $("#selected-courses").html(html);
    });
});
