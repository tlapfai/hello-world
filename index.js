document.addEventListener('DOMContentLoaded', function() {

    // Use buttons to toggle between views
    document.querySelector('#post').addEventListener('click', post);
    $('#following_posts').click(()=>load_posts('following'));
    

    // By default, load the inbox
    load_posts('all');
    $('.full-screen').hide();
});

function post() {
    const $body = document.querySelector('#input-area').value;
    console.log($body)
    fetch('/new_post', {
        method: 'POST',
        body: JSON.stringify({
            body: $body
        })
    })
    .then(response => response.json())
    .then(result => {
        // Print result
        console.log(result);
    });

}

function load_posts(range) {

    $('#all-posts').empty();

    fetch('/posts/' + range)
        .then(response => response.json())
        .then(posts => {
            for (let i=0; i<posts.length; i++) {
                $('#all-posts').append(
                    $("<div class='div-post'></div>").append(
                        $(`<table class='post-list' id='post-${i}'></table>`).append(
                            $("<b></b>").html(`${posts[i].content}<br/>`)
                        )
                    )
                );
                $('#post-' + i).append($(`<a></a>`).html(`Edit<br/>`));
                $('#post-' + i).append($(`<a class="follow-${posts[i].user}" href="#"></a>`).html(`${posts[i].user}\n`));
                $('.follow-' + posts[i].user).click( () => {
                    fetch('/follow_user/' + posts[i].user)
                        .then(response => response.json())
                        .then(response => {
                            $('.full-screen').empty();
                            $('.full-screen').append($(`<div class='text'></div>`).html(`${response.message}.<br><a href="#" class="btn-close">Close</a>`));
                            $('.full-screen').show();
                            $('.btn-close').click( () => { $('.full-screen').hide(); });
                        } );
                });
                $('#post-' + i).append($(`<p></p>`).html(`${posts[i].timestamp}\n`));
                if (posts[i].liked) {
                    $('#post-' + i).append($(`<a id='like-${posts[i].id}' href="#"></a>`).html(`Unlike`));
                } else {
                    $('#post-' + i).append($(`<a id='like-${posts[i].id}' href="#"></a>`).html(`Like`));
                }
                $('#like-' + posts[i].id).click( () => {
                    fetch('/like_post/' + posts[i].id);
                    if ($('#like-' + posts[i].id).text() == 'Like') {
                        $('#like-' + posts[i].id).text('Unlike');
                        $('#like-num-' + posts[i].id).text(parseInt($('#like-num-' + posts[i].id).text()) + 1);
                    } else {
                        $('#like-' + posts[i].id).text('Like');
                        $('#like-num-' + posts[i].id).text(parseInt($('#like-num-' + posts[i].id).text()) - 1);
                    }
                });
                $('#post-' + i).append(`<br>Likes: `);
                $('#post-' + i).append($(`<span id='like-num-${posts[i].id}'></span>`).text(`${posts[i].likes}`));
            }
        })
        .then(result => {
            console.log(result);
        });
}
