function showSuccessMsg() {
    $('.popup_con').fadeIn('fast', function() {
        setTimeout(function() {
            $('.popup_con').fadeOut('fast', function() {});
        }, 1000)
    });
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function() {
    $.get('/api/profile', function(data) {
        if ("4101" == data.errorno) {
            window.location.href = '/login.html';
        }
        if ("0" == data.errorno) {
            $("#user-avatar").attr('src', data.img_url);
        }
    });


    var xsrf = getCookie('_xsrf');
    $("#form-avatar").submit(function(event) {
        event.preventDefault();
        $('.image_uploading').fadeIn('fast');
        var options = {
            url: "/api/profile/avatar",
            type: "POST",
            headers: {
                "X-XSRFToken": xsrf,
            },
            success: function(data) {
                if ("0" == data.errorno) {
                    $('.image_uploading').fadeOut('fast');
                    $("#user-avatar").attr('src', data.img_url);
                }
            }
        };
        $(this).ajaxSubmit(options);
    });

    $("#form-name").submit(function(event) {
        event.preventDefault();
        var name = $('#user-name').val();
        info = {
            "name": name,
        }
        info = JSON.stringify(info);
        $.ajax({
            url: '/api/profile/name',
            type: 'POST',
            dataType: 'json',
            data: info,
            headers: {
                "X-XSRFToken": xsrf,
                "Content-Type": 'application/json',
            },
            success: function(data) {
                if (data.errorno == "0") {
                    window.location.href = "/my.html";
                }
                if (data.errorno == "4003") {
                    $('.error-msg').show();
                }

            }
        })

    });
})
