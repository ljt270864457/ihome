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
        $(".house-facility-list input[name='facility']:checked").each(function(){
        	value = $(this).val();
        	facility.push(value);
        });
        $(this).serializeArray().map(function(x) {
            info[x.name] = x.value;
        })
        info.facility = facility;
        $.ajax({
            url: '/api/house',
            type: 'POST',
            dataType: 'json',
            ContentType: 'application/json',
            headers: {
                'X-XSRFToken': getCookie('_xsrf')
            },
            data:info,
            success: function(data) {
            	if(data.errorno=="0")
            	{
            		window.location.href="/myhouse.html";
            	}
            }
        })
    });

})
