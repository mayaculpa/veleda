To test the websocket, from a browser console run:

    let socket = new WebSocket("ws://localhost:8000/ws-api/v1/farms/controller/", ["token_XXXXXXXXXXXXXXXX"]);
    socket.onmessage = function(event) {
      console.debug("WebSocket message received:", event);
    };
    socket.send('{"type": "tel", "hello": "there"}')

To test a command via the REST API (v1/farms/controllers/<uuid:pk>/command/), POST a request:

    {
      "type": "cmd",
      "peripheral": {
        "add": [
          {
            "name": "led33",
            "type": "LED",
            "pin": 33
          }
        ]
      }
    }