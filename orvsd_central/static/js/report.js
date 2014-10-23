$(function() {
    $.get("/1/report/stats", function(data) {
        $.each(data, function(k,v) {
            if (k === 'sites') {
                $("."+k).html(v);
            } else {
                $("#"+k).html(v);
            }
        });
    });

    $.get("/1/districts/active", function(data) {
        $("#report_tables").html("");
        for (var id in data['category']) {
            $.get("/1/districts/"+data['category'][id], function(d) {
                $("#report_tables").append(
                    "<div class=\"row\"><strong>"+d['name']+"</strong></div>"
                );
            });
        }
    });
});
