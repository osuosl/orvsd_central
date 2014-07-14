$(document).on("ready", function() {
    // Move the selected school to the selected district.
    $("#update").on("click", function() {
        var url = "/schools" ;
        $("#schools option:selected").each(function) {
            $.get(url + "/" + $(this).val(), function(resp) {
                // Update the school with the new district id.
                resp['district_id'] = $("#districts option:selected").val();
                $.post(url + "/" + $(this).val() + "/update", resp).done(function(msg) {
                    // If message is blank there was a 404.
                    if (msg != "") {
                        $("#message").html("Migrated " + $(this).text() + " to " +
                            $("#districts option:selected").text() + "!");
                    }
                });
            });
        });

    });
});
