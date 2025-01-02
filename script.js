let socket;
let reconnectInterval = 5000; // 5 seconds
let isSocketOpen = false;

function connectWebSocket() {
    socket = new WebSocket('ws://localhost:8001');

    socket.addEventListener('open', function (event) {
        console.log('Connection Established');
        socket.send('Connection Established');
        isSocketOpen = true;
    });

    socket.addEventListener('message', function (event) {
        console.log(event.data);
    });

    socket.addEventListener('close', function (event) {
        console.log('WebSocket closed, attempting to reconnect...');
        isSocketOpen = false;
        reconnect();
    });

    socket.addEventListener('error', function (event) {
        console.log('WebSocket error, attempting to reconnect...');
        socket.close(); // Ensure we close the socket on error, triggering reconnect logic
    });
}

function reconnect() {
    if (!isSocketOpen) {
        setTimeout(() => {
            console.log('Reconnecting to WebSocket...');
            connectWebSocket();
        }, reconnectInterval);
    }
}

document.addEventListener("keyup", (e) => {
    if (e.key == " " && isSocketOpen) {
        const d = document.querySelector(".word.active");
        if (d) {
            const content = d.textContent;
            socket.send("Word: " + content);
        }
    }
});

// Initialize WebSocket connection
connectWebSocket();
