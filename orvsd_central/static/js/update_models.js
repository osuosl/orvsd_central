$(document).on("ready", function() {
    $("#object_list").on("change", function() {
        // [1] will skip the first /, which returns an empty string and
        // give the category we are looking for.
        var category = window.location.pathname.split("/")[1]
        var url = "/" + category + "/" + $(this).val() + "/update";
        $.get(url, function(data) {
            $("#form").empty();
            $("#form").html(data);
        });
    });
});
