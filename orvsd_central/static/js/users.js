$(function() {
    $(".user").on("click", function() {
        var user_id = $(this).attr("id");
        var user_name = $(this).attr("name");
        var confirmed = confirm("Are you sure you want to delete " + user_name + "?");

        if (confirmed) {
            $.ajax({
                type: "POST",
                url: "/delete_user",
                data: {'user_id':user_id}
            });
        }
    });
});
