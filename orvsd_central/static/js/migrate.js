$(document).on("ready", function() {
    $("#update").on("click", function() {
        var url = "/schools" ;
        $.get(url + "/" + $("#schools option:selected").val(), function(resp) {
            resp['district_id'] = $("#districts option:selected").val();
            $.post(url + "/" + $("#schools option:selected").val() + "/update", resp).done(function(msg) {
                // If message is blank there was a 404.
                if (msg != "") {
                    $("#message").html("Migrated " + $("#schools option:selected").text() + " to " +
                        $("#districts option:selected").text() + "!");
                }
            });
        });
    });
});
