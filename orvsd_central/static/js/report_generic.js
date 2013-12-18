dump_category = function(a, d) {
    // Find the count details and update them
    a.find(".admins").html("Admins: " + d.counts.adminusers);
    a.find(".users").html("Users: " + d.counts.totalusers);
    a.find(".teachers").html("Teachers: " + d.counts.teachers);

    console.log(a.attr('data-category') + a.attr('data-id'));
    // Clear the list
    var out = a.find(".accordion-inner").find("#"+a.attr('data-category') + "_" + a.attr('data-id'));
    console.log(out);
    out.html("");
    var accordian_id = d.category + "_";

    // Add to the lists
    $.each(d.associated_objs, function(k, v) {
        $.post("/1/" + a.attr('data-category') + "/" + v[0] + "/accordion",
            {'parent_id': a.attr('data-id')}, function (data) {
                console.log(data)
                out.append(data);
        });
        // TODO: Add in action buttons
   });
};

$(function() {
    $(".categorycollapse").on("show", function() {
        var elem = $(this);
        console.log("/1/" + elem.attr('data-category') + "/" +
                elem.attr('data-id') + "/associated_objs")
        $.ajax({
            type: "GET",
            url: "/1/" + elem.attr('data-category') + "/" +
                elem.attr('data-id') + "/associated_objs",
            success: function(data) {
                dump_category(elem, data);
            }
        });
    });
});
