dump_schools = function(a, d) {
    var out = a.find(".accordion-inner");
    out.text("");
    $.each(d.schools, function(k, v) {
            out.append(k + ": " + v + ", ");
    });
};

$(function() {
    $(".collapsedistrict").on("show", function() {
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

