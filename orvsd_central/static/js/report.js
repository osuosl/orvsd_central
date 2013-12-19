dump_schools = function(a, d) {
    // Find the count details and update them
    a.find(".admins").html("Admins: " + d.counts.admins);
    a.find(".users").html("Users: " + d.counts.users);
    a.find(".teachers").html("Teachers: " + d.counts.teachers);

    // Clear the list
    var out = a.find(".accordion-inner ul");
    out.html("");

    // Add to the lists
    $.each(d.schools, function(k, v) {
        var line = "<li><a href=\"/view/schools/" + v.id + "\">" + v.name + "</a><ul>";
        $.each(v.sitedata, function(j, l) {
            if(l) {
                $.each(l, function(m, n) {
                    line += "<li>" + m + ": " + n + "</li>";
                });
            } else {
                line += "<li>No site data available</li>";
            }
        });
        line += "</ul>";
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

