# POC Encrypted Azure Upload & Download
This is code for a POC to upload to azure with client side encryption while supporting huge files.
It exists of two components:
  - HTML site - A web frontend to upload to an Azure Blob Storage
  - Decryptor - A python script that can download the files from the Azure Blob storage and decrypt them

## Azure
For this to work you need an Azure Storage Account / Container you can create this in the Azure Portal as follow:
  - Create the resource `Storage Account` and place it in a (new) Resource Group
  - Go to the Storage Account Resource and click on `Data Storage` -> `Containers`
  - Click on the `+` to create a new container

Access to the storage account for the components requires a SAS token you can create this in the portal as follow:
  - Go to the container (Resource Group -> [Storage Account] -> Data Storage -> Containers -> [Container]
  - Click on `Settings` -> `Shared access tokens`
  - Create a new token here, the components require the SAS URL

## HTML Upload portal
To run it follow the following steps:
  - Go to the `html` directory
  - Create a container:  `podman build . -t uploadportal`
  - Start the container while exposing port 1234: `podman run --rm --publish 1234:1234 localhost/uploadportal`

To use it you can browse to the exposed port (port 1234) with a browser, you will require a SAS URL.
After uploading a file you will see somewhere in the text:
```
Private AES key (base64): xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

```
That key is required for the decryptor to download & decrypt the key.

## Decryptor
The decryptor is also a container you can build it as follow
  - Go to the decryptor directory
  - Build the container: `podman build . -t decryptor`

You can either just start it (`podman run --rm -it localhost/decryptor`) and it will ask you for the SAS url, Blob name, AES key, etc. or you can use environment variables to start it:
```
podman run --rm -it \
  --env SAS_URL='' \
  --env BLOB_NAME='<file.name>' \
  --env BLOB_AESKEY='<copied_from_upload_portal>' \
  --env OUTPUT_DIR='/output' \
  --volume ./output/:/output \
  localhost/decryptor
```

If you leave out the environment variable `OUTPUT_DIR` the file will be downloaded and decrypted and you will see the sha256 hash of it, but the file will be lost
