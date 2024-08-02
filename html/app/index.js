const { BlobServiceClient } = require("@azure/storage-blob");

const blockIdPrefix = 'block-';
const selectButton = document.getElementById("select-button");
const fileInput = document.getElementById("file-input");
const status = document.getElementById("status");
const sasInput = document.getElementById("sasurl-input");
const chunkSizeSelect = document.getElementById("chunk-size-select");

const reportStatus = message => {
  status.innerHTML += `${message}<br/>`;
  status.scrollTop = status.scrollHeight;
}

function buf2b64(buf) {
  return btoa(new Uint8Array(buf).reduce((data, byte) => data + String.fromCharCode(byte), ''));
}

function buf2hex(buf) {
  return [...new Uint8Array(buf)].map(x => x.toString(16).padStart(2, '0')).join('');
}

function getInt64Bytes(x) {
  let y= Math.floor(x/2**32);
  return [y,(y<<8),(y<<16),(y<<24), x,(x<<8),(x<<16),(x<<24)].map(z=> z>>>24)
}

const uploadFiles = async () => {
  const sasURL = sasInput.value
  var matches = sasURL.match(/https?:\/\/([^\.]*).*\/([^?]*)\?(.*)/)
  console.log(matches)
  const accountName = matches[1]
  const containerName = matches[2]
  const sasToken = matches[3]
  const blockSize = Number(chunkSizeSelect.value)

  reportStatus(`Connect to https://${accountName}.blob.core.windows.net?${sasToken}`)
  const blobServiceClient = new BlobServiceClient(`https://${accountName}.blob.core.windows.net?${sasToken}`);
  reportStatus(`Connecting to container ${containerName}`)
  const containerClient = blobServiceClient.getContainerClient(containerName);

  try {
    reportStatus(`Uploading files (chunk size: ${blockSize})...`);
    // const promises = [];
    // Encryption setup
    const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 },  true, ["encrypt", "decrypt"]);
    const exported = await crypto.subtle.exportKey("raw", key);
    reportStatus("Private AES key (base64): " + buf2b64(exported));
    reportStatus("Private AES key (hex): " + buf2hex(exported));

    for (const file of fileInput.files) {
      reportStatus(`Uploading ${file.name}`)
      const blockBlobClient = containerClient.getBlockBlobClient(file.name);
      const totalBlocks = Math.ceil(file.size / blockSize);
      for (let i =0; i<totalBlocks; i++) {
        const start = i * blockSize;
        const end = Math.min(start + blockSize, file.size);
        const blockContent = file.slice(start, end);

        const blockArrayBuffer = await blockContent.arrayBuffer();
        //reportStatus("Block data (base64): " + buf2b64(blockArrayBuffer))

        // Encryption
        const iv = crypto.getRandomValues(new Uint8Array(12)); 
        //reportStatus("IV (base64): " + buf2b64(iv))
        //reportStatus("IV (hex): " + buf2hex(iv))
        alg = { name: "AES-GCM", iv: iv}
        const encrypted = await crypto.subtle.encrypt(alg, key, blockArrayBuffer)
        //reportStatus("Encrypted (base64): " + buf2b64(encrypted))
        //reportStatus("Encrypted (hex): " + buf2hex(encrypted))

        const blockId = blockIdPrefix + i.toString().padStart(6, '0');
        const base64BlockId = btoa(blockId);

        // Combine all the data
        const combinedBuffer = new Uint8Array(8 + iv.byteLength + encrypted.byteLength)
        combinedBuffer.set(getInt64Bytes(iv.byteLength + encrypted.byteLength))
        combinedBuffer.set(iv, 8);
        combinedBuffer.set(new Uint8Array(encrypted), iv.byteLength + 8);
        //reportStatus("Combined Buffer (base64): " + buf2b64(combinedBuffer))
        //reportStatus("Combined Buffer (hex): " + buf2hex(combinedBuffer))

        reportStatus(`Upload block ${i+1}/${totalBlocks}`)
        await blockBlobClient.stageBlock(base64BlockId, combinedBuffer.buffer, combinedBuffer.byteLength);
      }
      reportStatus(`Upload of ${file.name} completed`)
      const blockList = Array.from({ length: totalBlocks }, (_, i) => blockIdPrefix + i.toString().padStart(6, '0')).map(btoa);
      await blockBlobClient.commitBlockList(blockList);
      reportStatus("Commit completed")
    }
  } catch (error) {
    reportStatus(error.message);
  }
}

selectButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", uploadFiles);
