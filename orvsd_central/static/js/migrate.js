$(document).on("ready", function() {
    // Move the selected school to the selected district.
    $("#update").on("click", function() {
        var url = "/1/schools/";

        migrate_success = "";
        migrate_fail = "";

        $("#schools option:selected").each(function() {
            var school = $(this);

            $.ajax({
                // Using a GET to verify the existance of the school
                type: "GET",
                url: url + school.val(),
                dataType: "json",
                success: function(data, textStatus, jqXHR) {
                    // Update the district id for the school
                    data.district_id = $("#districts option:selected").val();

                    // POST the fixed data
                    $.ajax({
                        type: "POST",
                        url: url + school.val() + "/update",
                        data: data,
                        success: function(data, textStatus, jqXHR) {
                            school.remove();
                        },
                    });
                },
            });
        });
    });
});
