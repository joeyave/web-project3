const comment_template = Handlebars.compile(document.querySelector('#comment-template').innerHTML);
const reply_form_template = Handlebars.compile(document.querySelector('#reply-form-template').innerHTML);

document.addEventListener('DOMContentLoaded', () => {
    renderComments();

    var forms = document.querySelectorAll('form');
    var replyButtons = document.querySelectorAll('#reply');

    //Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    displayReplyForm(replyButtons);
    submitComment(socket, forms);
    announceComment(socket, comment_template);


    MutationObserver = window.MutationObserver || window.WebKitMutationObserver;

    var observer = new MutationObserver(function (mutations, observer) {
        replyButtons = document.querySelectorAll('#reply');
        forms = document.querySelectorAll('form');
        submitComment(socket, forms);

        displayReplyForm(replyButtons);
    });

    // define what element should be observed by the observer
    // and what types of mutations trigger the callback
    observer.observe(document.querySelector('#comments'), {
        attributes: true,
        characterData: true,
        childList: true,
        subtree: true,
        attributeOldValue: true,
        characterDataOldValue: true
    });
});

function renderComments() {
    fetch(`${window.location}/load_comments`, {
        method: "POST",
        credentials: "include",
        body: JSON.stringify({"blog_id": blogPostId}),
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
                renderComment(commentData);
            }
        })
    })
}

function renderComment(commentData) {
    const content = comment_template({
        'comment_id': commentData['comment_path'],
        'comment_author': commentData['username'],
        'comment_timestamp': commentData['comment_date'],
        'comment_text': commentData['comment_text']
    });

    const comment = htmlToElement(content);

    if (commentData['parent_path']) {
        const parent = document.getElementById("" + commentData['parent_path']);
        comment.style.marginLeft = "2rem";
        parent.append(comment);
    } else {
        document.querySelector('#comments').prepend(comment);
    }
}

function displayReplyForm(replyButtons) {
    replyButtons.forEach(function (button) {
        button.onclick = function () {
            let comment = button.parentNode.parentNode;
            if (comment.querySelector('#reply-form')) {
                comment.querySelector('#reply-form').remove();
            } else {
                const content = reply_form_template({
                    'reply_to': comment.querySelector('#comment_author').innerHTML
                });
                const reply = htmlToElement(content);
                comment.querySelector('#reply').after(reply);
            }
        }
    });
}

function submitComment(socket, forms) {
    forms.forEach(form => {
        form.onsubmit = () => {
            const comment = form.querySelector('#comment-text');

            socket.emit('submit comment', {
                'comment_text': comment.value,
                'blog_id': blogPostId,
                'parent_path': form.parentNode.parentNode.id
            });

            if (form.id === "comment-form") {
                form.querySelector('#comment-text').value = "";
            } else if (form.id === "reply-form") {
                form.remove();
            }
            return false;
        };
    });
}

function announceComment(socket) {
    socket.on('announce comment', data => {
            renderComment(data);
        }
    );
}

function htmlToElement(html) {
    const template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}