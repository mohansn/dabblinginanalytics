$(document).ready (function () {
    $('body').append('<div class="greet"></div>');
    $('body').append('<div class="friendcount"></div>');
    $('body').append('<div class="friends"></div>');
    $('.friends').html ('<ul></ul>');
    var access_token = docCookies.getItem ('access_token');
    var access_token_secret = docCookies.getItem ('access_token_secret');
    /* Get user info */
    $.ajax({
        url: '/get_userinfo',
        type: 'get',
        data: {
            'access_token':access_token,
            'access_token_secret':access_token_secret,
            async:false
        },
        success : function(data) {
            console.log (data);
            var info = JSON.parse(data);
            console.log (info);
            $('.greet').html("Hello " + info.name + "! You are user# " + info.id + "  ");

            /* get friends */
            friendcount = -1;
            $.ajax ({
                url: '/get_friendcount',
                type: 'get',
                data : {
                    'access_token':access_token,
                    'access_token_secret':access_token_secret,
                    async:false
                },
                success : function (data) {
                    friendcount = parseInt (data);
                    $('.friendcount').html ("You have " + parseInt (data) + " friends.");

                    /* Now, display friend list */
                    var num_pages = Math.ceil (friendcount / 30); /* 30 friends per page */
                    for (var i = 0; i < num_pages; i++) {
                        $.ajax ({
                            url: "/get_friends",
                            type: 'get',
                            data : {
                                'access_token':access_token,
                                'access_token_secret':access_token_secret,
                                'page_number':(i+1),
                                async:false
                            },
                            success : function (data) {
                                console.log (num_pages);
                                var fids = JSON.parse (data);
                                console.log (fids);
                                if (fids == []) {
                                    $('.friends').html ("No friends to show");
                                } else {
                                    var info = JSON.parse (data);
                                    for (item in info) {
                                        var friend = JSON.parse (item);
                                        $('.friends ul').append ("<li>" + friend.name + ", " + friend.id + "  </li>");
                                    }
                                }
                            },
                            done : function (data) {
                                console.log ("Hi!");
                            }
                        }); /* ajax : /get_friends */
                    }                    
                },
                error : function (data) {
                    friendcount = 0;
                }
            }); /* ajax: /get_friendcount */
        }
    }); /* ajax: /get_userinfo */
});

