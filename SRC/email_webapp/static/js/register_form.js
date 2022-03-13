$(function () {
    $("#recovery").change(function () {
        if ($(this).val() == "Phone") {
            $("#Phone").removeAttr("disabled");
            $("#Phone").attr("required", "required");
            $("#Email").val("")
            $("#Email").attr("disabled", "disabled");
            $("#Phone").focus();
        }
    });
});
$(function () {
    $("#recovery").change(function () {
        if ($(this).val() == "Email") {
            $("#Email").removeAttr("disabled");
            $("#Email").attr("required", "required");
            $("#Phone").attr("disabled", "disabled");
            $("#Phone").val("")
            $("#Email").focus();
        }
    });
});