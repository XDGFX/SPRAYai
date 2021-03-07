`
connect.js

Handles WebSocket connections between the host (control server) and the client (web browser).

Callum Morrison, 2021
`

const socket = io('/host');
socket.on('connect', function () {
    console.log('Connected to WebSocket server!')
});

socket.on('my response', data => {
    console.log(data);
});