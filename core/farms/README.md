To test the websocket, from a browser console run:

    let socket = new WebSocket("ws://localhost:8000/ws-api/v1/farms/controller/", ["Token", "754face72b9cd94b9a31ce81961da3f0387d0d10"]);
    socket.onmessage = function(event) {
      console.debug("WebSocket message received:", event);
    };
    socket.send('{"type": "tel", "hello": "there"}')