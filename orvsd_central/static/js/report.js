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
        $.each(data['category'], function(id, value) {
            $.get("/1/districts/"+value, function(d) {
                $("#report_tables").append(
                    "<div class=\"row\" data-district=\""+d['name']+"\">\
                        <h4>"+d['name']+"</h4>\
                    </div>\
                    <div class=\"row\" id=\""+d['shortname']+"\" data-district=\""+d['name']+"\">\
                        Loading...\
                    </div>"
                );
                $.post(
                    "/1/report/get_active_schools",
                    {distid: value},
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
                        for (var school in tdata) {
                            table += "<tr>\
                            <td><a>"+tdata[school]['sitename']+"</a></td>\
                            <td><a>"+tdata[school]['schoolname']+"</a></td>\
                            <td>"+tdata[school]['admin']+"</td>\
                            <td>"+tdata[school]['users']+"</td>\
                            <td>"+tdata[school]['teachers']+"</td>\
                            <td>"+tdata[school]['courses']+"</td>\
                            <td>\
                                <a>Add Course</a><br />\
                                <a>Add User</a><br />\
                                <a>Edit</a>\
                            </td></tr>";
                        }
                        table += "</table>";
                        $("#"+d['shortname']).html(table);
                    }
                );
            });
        });
    });


    $("#filter").on('input propertychange paste', function() {
        var keyword = $(this).val();
        $("#report_tables > div[data-district]").filter(function() {
            if ($(this).data('district').indexOf(keyword) > -1) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
});
