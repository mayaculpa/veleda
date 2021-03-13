# GraphQL Mutations

## Water Pump Control Example

Here are some examples of GraphQL mutations. On order to turn a pump on, first the ID of the respective water cycle component was to be queried.

```graphql
{
  allWaterCycleComponents(isWaterPump: true) {
    edges {
      node {
        id
        siteEntity {
          name
        }
        waterPump {
          power
        }
      }
    }
  }
}
```

From one of the returned water cycle components, the ID has to be taken and then input into the mutation. Below is an example of such a mutation request.

```graphql
mutation setWaterPumpPower($input: SetWaterPumpPowerInput!) {
  setWaterPumpPower(input: $input) {
    errors {
      message
    }
  }
}

{
  "input": {
    "waterCycleComponent": "V2F0ZXJDeWNsZUNvbXBvbmVudE5vZGU6MGFiNThjMjYtMjI0ZC00NTZiLWJlM2MtMTFjMWMxMjY0ZTQw",
    "power": 0.5
  }
}
```

The mutation only returns whether errors occured. If the `errors` array is empty, then the mutation was successfully requested. This means that no error occured while parsing the request. To verify that a request succeeded, create a subscription (TBD) for the data points related to the respective peripheral component.

## Controlling Peripheral Components Directly

The previous examples showed how to interact with domain specific actions such as turning a pump on and off. It is also possible to directly send tasks to controllers to create and remove peripherals as well as controlling them with controller tasks. An example of creating a polling task is given below.

```graphql
mutation createControllerTask($input: CreateControllerTaskInput!) {
  createControllerTask(input: $input) {
    controllerTask {
      controllerComponent {
        id
      }
      taskType
    }
  }
}

{
  "input": {
    "controllerComponent": "...",
    "taskType": "PollSensor",
    "parameters": "{\"some\": \"value\"}"
  }
}
```
