$(function() {
    $.get("/1/report/stats", function(data) {
        $.each(data, function(k,v) {
            $("#"+k).html(v);
        });
    });
});
