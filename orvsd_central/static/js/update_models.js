$(document).on("ready", function() {
    // [1] will skip the first /, which returns an empty string and
    // give the category we are looking for.
    var category = window.location.pathname.split("/")[1];
    var base_url = "/" + category;
    var pairs;

    pairs = display_obj($("#object_list option:selected"), category);

    // Stores the current keys and vals for the object we are looking at.

    $("#object_list").on("change", function() {
        pairs = display_obj($(this), category);
    });

    $("#add").on("click", function() {
        $.get(base_url + "/keys", function(resp) {
            var rows = "";
            // Generate a new form with keys corresponding to a Model's
            // attributes.
            for (var key in resp) {
                rows += generate_row(key, "");
            }
            $("#form").empty();
            $("#form").html(rows);
            pairs = resp;
        });
    });

    $("input[type=submit]").on("click", function() {
        data = new Object();
        data[$(this).val()] = $(this).val();
        // Generate our JSON from the form to be sent back to the server.
        for (var key_name in pairs) {
            data[key_name] = $("#"+key_name).val();
        }
        // Data 'id' will be blank if we are adding a new object.
        if (data["id"] == "") {
            console.log("posting to add");
            $.post(base_url + "/object/add", data).done(function(resp) {
                $("#message").html(resp["message"]);
                $("#id").val(resp["id"]);
            });
        }
        else {
            // Posts to /update or /delete, depending on the button that
            // was clicked.
            var method = $(this).attr("name");
            var url = base_url + "/" + data['id'] + "/" + method;
            $.post(url, data).done(function(resp) {
                if (method === "delete") {
                    // Remove all references to old object
                    $("#form").empty();$

                    // Record the next object before we delete the current.
                    var next = $('#object_list option:selected').next()

                    $("#object_list option:selected").remove();
                    next.attr('selected', 'selected');

                    // Edge case for last element
                    if (next.val() === undefined) {
                        next = $("#object_list option:selected");
                    }
                    pairs = display_obj(next, category);
                }
                $("#message").html(resp);
            });
        }
    });

    function display_obj(obj, category) {
        var url = base_url + "/" + obj.val();
        $.get(url, function(resp) {
            var rows = "";
            for (var key in resp) {
                rows += generate_row(key, resp[key]);
            }
            $("#form").empty();
            $("#form").html(rows);
            $("#message").empty();
            pairs = resp
        });
        // Return keys and vals for the object we recieved.
        return pairs;
    }
});

// Used to generate the html for an input field for an attribute.
function generate_row(key, value) {
    html =  "<div class=\"control-group pull-left\">\n" +
            "<label for=\""+key+"\" class=\"control-label min-padding\">\n"+capitalize(key)+":\n</label>\n" +
            "<div class=\"controls\">\n" +
            "<input id=\""+key+"\" name=\"" + key + "\" type=\"text\" value=\"" + value + "\"";
    if (key == "id") {
    html += " readonly";
    }
    html += ">\n" +
            "</div>\n" +
            "</div>\n";
    return html;
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
