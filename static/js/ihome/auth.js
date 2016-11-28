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


$(function(){
	var xsrf = getCookie('_xsrf')
	$.get('/api/profile/auth', function(data) {
		if (data.errorno == "0") {
			var name = data.name;
			var id_number = data.id_number;
			$('#real-name').val(name).attr('readonly', 'readonly');
			$('#id-card').val(id_number).attr('readonly', 'readonly');
		}
	});

	$('#form-auth').submit(function(event) {
		event.preventDefault();
		var name = $('#real-name').val();
		var id_number = $('#id-card').val();
		info = JSON.stringify({ 'real_name': name, 'id_card': id_number });
		$.ajax({
			url: '/api/profile/auth',
			type: 'POST',
			dataType: 'json',
			headers: {
				"Content-Type": "application/json",
				'X-XSRFToken': xsrf
			},
			data: info,
			success:function(data){
				if(data.errorno == "0")
				{
					window.location.href = "/auth.html";
				}
			}
		})
	});

})
