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
        var link = "<li><a href=\"/schools/" + v.id + "/view\">" + v.name + "</a>";
        var line = link + " - <b>A:</b> " + v.admincount +
                          ", <b>T</b>: " + v.teachercount +
                          ", <b>U</b>: " + v.usercount + " </li>";
        if (v.sitedata != "") {
            $.each(v.sitedata, function(j, l) {
                $.each(l, function(m, n) {
                    if (n == undefined)
                        n = "Not available";
                    line += "<dd>" + m.charAt(0).toUpperCase() + m.slice(1) + ": " + n;
                });
            });
        }  else {
            line += "<dd>No site data available";
        }
        out.append(line);
    });
};

$(function() {
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

