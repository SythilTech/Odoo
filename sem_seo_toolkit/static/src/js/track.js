var session_id = Date.now();

var xhr = new XMLHttpRequest();
xhr.open('POST', window.tracking_url);
xhr.setRequestHeader('Content-Type', 'text/plain');
xhr.send(JSON.stringify({
    session_id: session_id,
    document_referrer: document.referrer
}));
