$(function() {
    // [1] will skip the first /, which returns an empty string and
    // give the category we are looking for.
    var category = window.location.pathname.split("/")[1];
    var base_url = "/1/" + category;
    var pairs;

    // Set the current form element keys, and generate the form
    // off the first selected object.
    var object_list_length = $("#object_list option").length;
    if (object_list_length > 0) {
        var $selected = $("#object_list option:selected");
        pairs = display_obj($selected, category);
    }
    else {
        pairs = display_blank_obj(category);
    }

    // Change which object we display when the selected option changes.
    $("#object_list").on("change", function() {
        pairs = display_obj($(this), category);
    });

    // Add new object.
    $("#add").on("click", function() {
        // Generate empty form for object.
        if ($("#add").val() === "Add") {
            $.get(base_url + "/keys", function(resp) {
                var rows = "";
                // Generate a new form with keys corresponding to a Model's
                // attributes.
                for (var key in resp) {
                    rows += generate_row(key, "");
                }
                $("#form").find("input[type=text]").val("");
                pairs = resp;
            });
            $("#add").val("Submit");
            var option = document.createElement("option");
            $("#object_list").prepend(option);
            $(option).attr('selected', 'selected');
        }
        // Add new object to database.
        else {
            var data = get_form_data($(this));
            $.post(base_url + "/object/add", data).done(function(resp) {
                $("#message").html(resp["message"]);
                $("#id").val(resp["id"]);

                // 'identifier' determines which key we use to identify an
                // element.
                var name = resp[resp["identifier"]];
                insert_and_sort_list(name, resp["id"]);
                reset_add_if_submit();
            });
        }
    });

    $("input[type=submit]").on("click", function() {
        // First, let's clear the message for the next action
        $("#message").val("");

        var data = get_form_data($(this));

        // Data 'id' will be blank if we are adding a new object.
        // A user may either use the 'Submit' or 'Update' functionality for
        // adding a new item.
        if (data["id"] == "" && $(this).val() !== "Delete") {
            $.post(base_url + "/object/add", data).done(function(resp) {
                $("#message").html(resp["message"]);
                $("#id").val(resp["id"]);

                // 'identifier' determines which key we use to identify an
                // element.
                var name = resp[resp["identifier"]]
                insert_and_sort_list(name, resp["id"]);

            });
            reset_add_if_submit();
        }
        // Delete an object.
        else if (data["id"] == "" && $(this).val() === "Delete") {
                var message = "You may not delete elements that do not exist!";
                $("#message").html(message);
        }
        else {
            // Posts to /update or /delete, depending on the button that
            // was clicked.
            var method = $(this).attr("name");
            var url = base_url + "/" + data['id'] + "/" + method;
            $.post(url, data).done(function(resp) {
                if (method === "delete") {
                    // Remove all references to old object
                    $("#form").find("input[type=text]").val("");

                    // Record the next object before we delete the current.
                    var next = $('#object_list option:selected').next()

                    $("#object_list option:selected").remove();
                    next.attr('selected', 'selected');

                    // Edge case for last element
                    if (next.val() === undefined) {
                        next = $("#object_list option:selected");
                    }

                    object_list_length = $("#object_list option").length;
                    if (object_list_length > 0) {
                        pairs = display_obj(next, category);
                    }
                    else {
                        pairs = display_blank_obj(category);
                    }
                }
                else {
                    var name = resp[resp["identifier"]];
                    console.log(resp);
                    $("#object_list option:selected").text(name);
                    $("#message").html(resp["message"]);
                }
                $("#message").html(resp["message"]);
            });
            reset_add_if_submit();
        }
    });

    // Display an object for a given category, and return that object's keys.
    function display_obj(obj, category) {
        var url = base_url + "/" + obj.val();
        $.get(url, function(resp) {
            var rows = "";
            for (var key in resp) {
                rows += generate_row(key, resp[key]);
            }
            $("#form").html(rows);
            pairs = resp
        });
        // Return keys and vals for the object we recieved.
        return pairs;
    }

    function display_blank_obj(category) {
        var url = '/1/' + category + '/keys';
        $.get(url, function(resp) {
            var rows = "";
            // Generate a new form with keys corresponding to a Model's
            // attributes.
            for (var key in resp) {
                rows += generate_row(key, "");
            }
            $("#form").html(rows);
            pairs = resp;
        });
        // This is so new objects can be created immediately.
        $("#add").val("Submit");
        return pairs;
    }

    // Get the data from the current form elements.
    function get_form_data(obj) {
        data = new Object();
        data[obj.val()] = obj.val();
        // Generate our JSON from the form to be sent back to the server.
        for (var key_name in pairs) {
            data[key_name] = $("#"+key_name).val();
        }
        return data;
    }

    // Used for adding new objects. Adds the new object and re-sorts the list
    // so it's in the correct spot.
    function insert_and_sort_list(name, value) {
        var object_list_length = $("#object_list option").length;
        if (object_list_length === 0) {
            option = $('<option>');
            $("#object_list").append(option);
        }
        else {
            option = $("#object_list option:selected");
        }
        option.val(value);
        option.text(name);

        // Sorts the option list. Not the most efficient, but our data
        // set is small, so it shouldn't cause performance issues.
        $("#object_list").html($('#object_list option').sort(function(x, y) {
             return $(x).text() < $(y).text() ? -1 : 1;
        }));
    }
    // Reset the button text to 'Add' if it's currently 'Submit'.
    function reset_add_if_submit() {
        if ($("#add").val() === "Submit") {
            $("#add").val("Add");
        }
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

// Capitalize a string.
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
