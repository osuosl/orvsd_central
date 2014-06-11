$(document).ready(function() {

    $("#districts").change(function() {
        // Easy reference to district choice
        var dist = $(this).find(":selected").text();

        if (dist != "None") {
            // Get and fill the schools
        }

        // Set sites and courses options to All and none

    });

    $("#schools").change(function() {
        // Easy reference to school choice
        var sch = $(this).find(":selected").text();

        if (dist != "None") {
            // Get and fill the sites
        }

        // Set courses options to all and none

    });

    $("#sites").change(function() {
        // Easy reference to site choice
        var sites = $(this).find(":selected").text();

        if (dist != "None") {
            // Get and fill the courses
        }

    });

});
