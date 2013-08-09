$(document).on("ready", function() {
    var pairs;
    var category = window.location.pathname.split("/")[1]
    var url;
    $("#object_list").on("change", function() {
        // [1] will skip the first /, which returns an empty string and
        // give the category we are looking for.
        url = "/" + category + "/" + $(this).val();
        $.get(url, function(resp) {
            var rows = "";
            for (var key in resp) {
                rows += generate_row(key, resp[key]);
            }
            $("#form").empty();
            $("#form").html(rows);
            pairs = resp;
        });
    });
    $("input[type=submit]").on("click", function() {
        data = new Object();
        data[$(this).val()] = $(this).val();
        for (var key_name in pairs) {
            data[key_name] = $("#"+key_name).val();
        }
        console.log($(this).attr("name"));
        $.post(url + "/" + $(this).attr("name"), data).done(function(resp) {
            $("#message").html(resp);
        });
    });
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
