const sidebar_comment_template = Handlebars.compile(document.querySelector('#sidebar-comment-template').innerHTML);

document.addEventListener('DOMContentLoaded', () => {
    navToggle();
    renderSidebarComments();
});

function navToggle() {
    document.querySelector('#nav-toggle').addEventListener('click', () => {
        document.querySelector('#nav').classList.toggle('nav--active');
    });
}

function renderSidebarComments() {
    fetch("/load_sidebar_comments", {
        method: "POST",
        credentials: "include",
        cache: "no-cache",
        headers: new Headers({
            "content-type": "application/json"
        })
    }).then(function (response) {

        if (response.status !== 200) {
            console.log(`Response status was not 200: ${response.status}`);
            return;
        }

        response.json().then(function (data) {
            for (const commentData of data) {
                renderSidebarComment(commentData);
            }
        })
    })
}

function renderSidebarComment(commentData) {
    const content = sidebar_comment_template({
        'comment_author': commentData['username'],
        'comment_timestamp': commentData['comment_date'],
        'comment_text': commentData['comment_text']
    });

    const comment = htmlToElement(content);
    document.querySelector('#sidebar-comments').prepend(comment);

    comment.addEventListener('click', function () {
        location.href = "/blog/" + commentData['comment_blog_post_id'];
    })
}

function htmlToElement(html) {
    const template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}