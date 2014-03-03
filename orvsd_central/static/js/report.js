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
    $(window).on("load", function() {
        $.get("/1/report/stats", function(resp) {
            for (var key in resp) {
                $("#" + key).append(resp[key]);
            }
        });
    });

    $(".districtcollapse").on("show", function() {
        var elem = $(this);
        $.ajax({
            type: "POST",
            url: "/report/get_schools",
            data: {'distid': $(this).attr('distid')},
            success: function(data) {
                dump_schools(elem, data);
            }
        });
    });
});

