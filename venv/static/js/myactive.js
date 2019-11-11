function ajaxload() {
    $('.bigblack').show();
    $.ajax({
        url: '/login',
        cache: true,
        async: false,
        success: function(html) {
            $('#loginbox').html(html);
        }
    });
    $('#loginbox').fadeIn();
    var btn2 = document.getElementById('close');
    var login1 = document.getElementById('phonenumber');
    var submit1 = document.getElementById('correctcode');

    btn2.addEventListener('click', close, false);
    login1.addEventListener('change', verify, false);
    submit1.addEventListener('change', verify2, false);
    $('#getcode').attr('onclick', 'sendSMSCode()');
    $('#loginsubmit').attr('onclick', 'sendtheuser()');
}

function close() {
    $('.bigblack').hide();
    $('#loginbox').fadeOut();
}

function verify() {
    var phonenumber = $('#phonenumber ').val();
    var p1 = /^(13[0-9]\d{8}|15[0-35-9]\d{8}|18[0-9]\d{8}|14[57]\d{8})$/
    if (p1.test(phonenumber) == false) {
        alert('请填写正确电话号码!!');
        document.getElementById('phonenumber').value = '';
        $('#getcode').attr('disabled', true);
    } else {

        $('#getcode').attr('disabled', false);
    }
}

function verify2() {
    var correctcode = $('#correctcode').val();
    var p1 = /^\d{6}$/
    if (p1.test(correctcode) == false) {
        alert('请填写正确验证码!!');
        document.getElementById('correctcode').value = '';
        $('#loginsubmit').attr('disabled', true);
    } else {

        $('#loginsubmit').attr('disabled', false);
    }
}

function sendSMSCode() {
    var phonenumber = $('#phonenumber').val();
    var params = {
        'mobile': phonenumber,
    }
    $.ajax({
        url: '/sms_code',
        type: 'post',
        data: JSON.stringify(params),
        contentType: 'application/json',
        success: function(resp) {
            if (resp.errno == 'ok') {
                $('#login-sms-code-err').html(resp.errmsg);
                $('#getcode').attr('disabled', true);
                var num = 60;
                var t = setInterval(function() {
                    if (num == 1) {

                        clearInterval(t);
                        $('#getcode').attr('disabled', false);
                        $('#getcode').html('获取验证码');
                        $('#getcode').attr('onclick', 'sendSMSCode()');

                    } else {
                        num -= 1;
                        $('#getcode').html(num + '秒')
                    }
                }, 1000)

            } else {
                $('#login-sms-code-err').html(resp.errmsg);
                $('#getcode').attr('onclick', 'sendSMSCode()');
            }
        }
    })
}

function sendtheuser() {
    var phonenumber = $('#phonenumber').val();
    var sms_code = $('#correctcode').val();
    var params = {
        'mobile': phonenumber,
        'sms_code': sms_code,
    }
    $.ajax({
        url: '/login/in',
        type: 'post',
        data: JSON.stringify(params),
        contentType: 'application/json',
        success: function(resp) {
            if (resp.errno == 'notok') {
                $('#login-sms-code-err').html(resp.errmsg);
            } else {
                location.reload();
            }

        }
    })
}