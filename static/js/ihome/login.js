function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function() {
        $("#mobile-err").hide();
    });
    $("#password").focus(function() {
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e) {
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        xsrf = getCookie("_xsrf");
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        var info = {
            "mobile": mobile,
            "passwd": passwd,
        };
        info = JSON.stringify(info);
        console.log(info);
        $.ajax({
            url: '/api/login',
            type: 'POST',
            dataType: 'json',
            headers: {
                "X-XSRFToken": xsrf,
                "Content-Type": "application/json"
            },
            data: info,
            success: function(data) {
                if ("0" == data.errorno) {
                    window.location.href = "/";
                }
            }
        })

    });
})
