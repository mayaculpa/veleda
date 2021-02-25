To test the creation of a LED peripheral post a request to the REST API
(v1/farms/controllers/<uuid:pk>/command/). The data point type corresponds to
one describing the LEDs brightness in percent:

    {
      "type": "cmd",
      "peripheral": {
        "add": [
          {
            "uuid": "5850349f-e633-4b4e-a387-916de884e77f",
            "type": "LED",
            "pin": 2,
            "data_point_type": "1035cd8e-e831-49c2-b0d2-5448ac22ee80"
          }
        ]
      }
    }

To turn the LED on, post a request to the same URL:

    {
      "type": "cmd",
      "task": {
        "start": [
          {
            "uuid": "01769b42-220c-43ee-831e-5571011cabf9",
            "peripheral_uuid": "5850349f-e633-4b4e-a387-916de884e77f",
            "type": "WriteActuator",
            "value": 1,
            "data_point_type": "1035cd8e-e831-49c2-b0d2-5448ac22ee80"
          }
        ]
      }
    }

To test the websocket, from a browser console run:

    let socket = new WebSocket("ws://localhost:8000/ws-api/v1/farms/controller/", ["token_XXXXXXXXXXXXXXXX"]);
    socket.onmessage = function(event) {
      console.debug("WebSocket message received:", event);
    };
    socket.send('{"type": "tel", "hello": "there"}')
