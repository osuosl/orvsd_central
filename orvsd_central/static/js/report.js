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
                    "<div class=\"row\" ><strong>"+d['name']+"</strong></div>\n<div class=\"row\" id=\""+d['shortname']+"\"></div>"
                );
                $.post(
                    "/1/report/get_active_schools",
                    {distid: data['category'][id]},
                    function(tdata) {
                        var table = "<table class=\"table table-condensed table-responsive table-bordered table-hover table-striped\">";
                        table += "<tr>\
                            <th>Site</th>\
                            <th>School</th>\
                            <th>Admin</th>\
                            <th>Users</th>\
                            <th>Teachers</th>\
                            <th>Courses</th>\
                            <th>Actions</th>\
                        </tr>";
                        table += "</table>";
                        $("#"+d['shortname']).append(table);
                    }
                );
            });
        }
    });
});
