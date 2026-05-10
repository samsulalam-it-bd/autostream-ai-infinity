const https = require('https');

const data = JSON.stringify({
    model: 'provider-5/gemini-2.5-flash',
    messages: [{ role: 'user', content: 'Say "Working!" if you can read this.' }]
});

const options = {
    hostname: 'api.a4f.co',
    path: '/v1/chat/completions',
    method: 'POST',
    headers: {
        'Authorization': 'Bearer ddc-a4f-67aacd9fef244c039646390085e90cc0',
        'Content-Type': 'application/json',
        'Content-Length': data.length
    }
};

const req = https.request(options, res => {
    let body = '';
    console.log(`statusCode: ${res.statusCode}`);

    res.on('data', d => {
        body += d;
    });

    res.on('end', () => {
        console.log(body);
    });
});

req.on('error', error => {
    console.error(error);
});

req.write(data);
req.end();
