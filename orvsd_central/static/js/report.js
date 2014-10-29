$(function() {
    // Get active districts
    // Data is [(dist_name, dist_shortname, dist_id), ...]
    $.get("/1/districts/active", function(data) {
        // Sort based on name for alphabetical display
        data.category.sort(function(a, b) {
            if (a[0] > b[0])
                return 1;
            if (a[0] < b[0])
                return -1;
            return 0;
        });

        // Remove 'Loading...'
        $("#report_tables").html("");

        // For each district
        $.each(data['category'], function(id, value) {
            // Apend a row for the district name and the district table
            $("#report_tables").append(
                "<div class=\"row\" data-district=\""+value[0]+"\">\
                    <h4>"+value[0]+"</h4>\
                </div>\
                <div class=\"row\" id=\""+value[1]+"\" data-district=\""+value[0]+"\">\
                    Loading...\
                </div>"
            );

            // Get the active details for the district to be displayed
            // then generate table data from the returned
            $.get(
                "/1/report/get_active_schools",
                // value[2] is the district id
                {distid: value[2]},
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
                        <td><a href=\"http://" + tdata[school]['baseurl'] + "\">" + tdata[school]['sitename'] + "</a></td>\
                        <td><a href=\"/schools/" + tdata[school]['schoolid'] + "/view\">" + tdata[school]['schoolname'] + "</a></td>\
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
                    $("#"+value[1]).html(table);
                }
            );
        });
    });
    //
    // Get the top of the reort page stats
    $.get("/1/report/stats", function(data) {
        // Since Active Sites also displays the sites count, we have a special
        // case for it
        $.each(data, function(k,v) {
            if (k === 'sites') {
                $("."+k).html(v);
            } else {
                $("#"+k).html(v);
            }
        });
    });

    // Filter districts when input is changed
    $("#filter").on('input propertychange paste', function() {
        var keyword = $(this).val().toLowerCase();
        $("#report_tables > div[data-district]").filter(function() {
            if ($(this).data('district').toLowerCase().indexOf(keyword) > -1) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
});
