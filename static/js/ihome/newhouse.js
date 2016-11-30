function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $.get('/api/areas', function(data) {
        var areas = data.areas;
        for (var i = 0; i < areas.length; i++) {
            $('#area-id').append('<option value="' + areas[i].id + '">' + areas[i].area + '</option>');
        }

    });

    $('#form-house-info').submit(function(event) {
        event.preventDefault();
        var info = {};
        facility = [];
        $(".house-facility-list input[name='facility']:checked").each(function() {
            value = $(this).val();
            facility.push(value);
        });
        $(this).serializeArray().map(function(x) {
            info[x.name] = x.value;
        })
        info.facility = facility;
        info = JSON.stringify(info);
        console.log(info);
        $.ajax({
            url: '/api/house',
            type: 'POST',
            dataType: 'json',
            headers: {
                'Content-Type': 'application/json',
                'X-XSRFToken': getCookie('_xsrf')
            },
            data: info,
            success: function(data) {
                if (data.errorno == "0") {
                    $('#form-house-info').hide()
                    $('#form-house-image').show();
                    $("#house-id").val(data.houseID);
                    $(".error-msg").hide();
                }
            }
        })
    });

    $("#form-house-image").submit(function(event) {
        $('.popup_con').fadeIn('fast');
        var options = {
            url:"/api/house/image",
            type:"POST",
            headers:{
                "X-XSRFTOKEN":getCookie("_xsrf"),
            },
            success: function(data){
                if ("4101" == data.errorno) {
                    location.href = "/login.html";
                } else if ("0" == data.errorno) {
                    $(".house-image-cons").append('<img src="'+ data.url+'">');
                    $('.popup_con').fadeOut('fast');
                }
            }
        };
        $(this).ajaxSubmit(options);
        return false;
    });

})
