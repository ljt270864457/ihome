function logout() {
    $.get("/api/logout", function(data){
        if (0 == data.errno) {
            location.href = "/";
        }
    })
}

$(document).ready(function(){
	$.get('/api/profile', function(data) {
		if(data.errorno=="0")
		{
			var userName = data.name;
			var mobile = data.mobile;
			var url = data.img_url;
			$('#user-name').text(userName);
			$('#user-mobile').text(mobile);
			$('#user-avatar').attr('src',url);
		}
	});
	// 用户点击退出登录触发
	$('.menus-list li:eq(5) div a').click(function(event) {
		$.get('/api/logout', function(data) {
			if(data.errorno=="0")
			{
				window.location.href="/login.html";
			}
		});
	});
})