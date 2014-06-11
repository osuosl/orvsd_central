dump_schools = function(a, d) {
    // Find the count details and update them
    a.find(".admins").html("(A)dmins: " + d.counts.admins);
    a.find(".users").html("(U)sers: " + d.counts.users);
    a.find(".teachers").html("(T)eachers: " + d.counts.teachers);

    // Clear the list
    var out = a.find(".accordion-inner dl");
    out.html("");

    // Add to the lists
    $.each(d.schools, function(k, v) {
        var line = "";
        if (v.sitedata != "") {
        var link = "<hr><li><a href=\"/schools/" + v.id + "/view\">" + v.name + "</a>";
        line = link + " - <b>A:</b> " + v.admincount +
                          ", <b>T</b>: " + v.teachercount +
                          ", <b>U</b>: " + v.usercount + " </li>";
            $.each(v.sitedata, function(j, l) {
                line += "<hr>";
                $.each(l, function(m, n) {
                    if (n == undefined)
                        n = "Not available";
                    line += "<dd>" + m.charAt(0).toUpperCase() + m.slice(1) + ": " + n;
                });
            });
        }
        out.append(line);
    });
};

$(function() {
    // Fill in the statistics at the top of the page.
    $(window).on("load", function() {
        $.get("/1/report/stats", function(resp) {
            for (var key in resp) {
                $("#" + key).append(resp[key]);
            }
        });
    });

    // Show the schools in a given district.
    $(".districtcollapse").on("show", function() {
        var elem = $(this);
        // Hacky way to check whether we're in the active or inactive districts
        if (elem.parent().parent().attr('id') == 'dist_accord_active') {
            $.ajax({
                type: "POST",
                url: "/1/report/get_active_schools",
                data: {'distid': $(this).attr('distid')},
                success: function(data) {
                    dump_schools(elem, data);
                }
            });
        }
        else if (elem.parent().parent().attr('id') == 'dist_accord_inactive') {
            $.ajax({
                type: "POST",
                url: "/1/report/get_inactive_schools",
                data: {'distid': $(this).attr('distid')},
                success: function(data) {
                    dump_schools(elem, data);
                }
            });
        }
    });
});
