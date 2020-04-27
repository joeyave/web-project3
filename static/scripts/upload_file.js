document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#files').onchange = () => {
        const request = new XMLHttpRequest();
        const files = document.querySelector('#files').files;
        request.open('POST', '/upload_file');

        request.onload = () => {
            const data = JSON.parse(request.responseText);

            let img_links = "";

            for (let link of data.links) {
                img_links += "\n![](" + link + ")\n";
            }

            document.querySelector('#blog_post').value += img_links;
            document.querySelector('#files').value = "";
        };

        const data = new FormData();
        for (let i = 0; i < files.length; i++) {
            let file = files[i];
            data.append('files', file);
        }

        request.send(data);
        return false;
    }
});