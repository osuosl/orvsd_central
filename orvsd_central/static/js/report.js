dump_schools = function(a, d) {
    // Find the count details and update them
    a.find(".admins").html("Admins: " + d.counts.admins);
    a.find(".users").html("Users: " + d.counts.users);
    a.find(".teachers").html("Teachers: " + d.counts.teachers);

    // Clear the list
    var out = a.find(".accordion-inner dl");
    out.html("");

    // Add to the lists
    $.each(d.schools, function(k, v) {
        var line = "";
        if (v.sitedata != "") {
        line += "<li><a href=\"/schools/" + v.id + "/view\">" + v.name + "</a></li>";
            $.each(v.sitedata, function(j, l) {
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

