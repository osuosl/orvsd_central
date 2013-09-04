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
     $("#filter").on("change", function() {
        var filter = $(this).val()
        $.post("/courses/filter", $(this)).done(function(data) {
            $("#course").empty();
            generate_course_list(data);
        });
    });
});

function generate_course_list(resp) {
    var json = JSON.parse(JSON.stringify(resp));
    var html = "";
    $(json.courses).each(function(i, val) {
        $('#course').append($("<option></option>")
                    .attr("value",val.id)
                    .text(val.name));
        });
}

