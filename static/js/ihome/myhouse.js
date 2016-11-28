function getCookie(name) {
	var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
	return r ? r[1] : undefined;
}

$(document).ready(function(){
	$(".auth-warn").show();
	$.get('/api/profile/auth', function(data) {
		if(data.errorno=="0")
		{
			$(".auth-warn").hide();
			$(".newhouse").show(); 		
		}
	});
})
