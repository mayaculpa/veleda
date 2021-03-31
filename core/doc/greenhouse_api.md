# Greenhouse API

## REST API

In order to upload plant images, use the `CORE_DOMAIN/greenhouse/api/plant_image/` URL. To test the upload feature, use the following command:

    curl -H "Authorization: Token ABC123" -F "plant=PLANT_COMPONENT_UUID" -F "image=@/path/to/image.jpg" http://localhost:8000/greenhouse/api/plant_image/