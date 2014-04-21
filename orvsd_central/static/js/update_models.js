$(document).on("ready", function() {
    // [1] will skip the first /, which returns an empty string and
    // give the category we are looking for.
    var category = window.location.pathname.split("/")[1]

    // Stores the current keys and vals for the object we are looking at.
    var pairs = display_obj($("#object_list option:selected"), category);
    var url;

    $("#object_list").on("change", function() {
        pairs = display_obj($(this), category);
    });

    $("#add").on("click", function() {
        url = "/" + category;
        $.get(url + "/keys", function(resp) {
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
            $.post(url + "/object/add", data).done(function(resp) {
                $("#message").html(resp["message"]);
                $("#id").val(resp["id"]);
            });
        }
        else {
            // Posts to /update or /delete, depending on the button that
            // was clicked.
            method = $(this).attr("name");
            $.post(url + "/" + method, data).done(function(resp) {
                // If we are deleting an object, we should clear all
                // references to that data.
                if (method === "delete") {
                    $("#form").empty();
                    $("#object_list option:selected").remove();
                }
                $("#message").html(resp);
            });
        }
    });
});

function display_obj(obj, category) {
    var url = "/" + category + "/" + obj.val();
    $.get(url, function(resp) {
        var rows = "";
        for (var key in resp) {
            rows += generate_row(key, resp[key]);
        }
        $("#form").empty();
        $("#form").html(rows);
        $("#message").empty();
        return resp;
    });
}

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
