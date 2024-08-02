from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
import sys
import re
import hashlib

def get_account_settings(_sas_url = None):
  account_name = os.getenv('ACCOUNT_NAME')
  container_name = os.getenv('CONTAINER_NAME')
  blob_name = os.getenv('BLOB_NAME')
  sas_token = os.getenv('SAS_TOKEN')
  sas_url = os.getenv('SAS_URL', _sas_url)
  blob_aeskey = os.getenv('BLOB_AESKEY')
  output_dir = os.getenv('OUTPUT_DIR', '.')

  if account_name is None and sas_url is not None:
    print("* Getting account name from sas_url")
    m = re.match('^https?://([^.]*)', sas_url)
    account_name = m.group(1)

  if container_name is None and sas_url is not None:
    print("* Getting container name from sas_url")
    m = re.match('^.*/([^?]*)', sas_url)
    container_name = m.group(1)

  if sas_token is None and sas_url is not None:
    print("* Getting SAS token from sas_url")
    m = re.match('^[^?]*.(.*)', sas_url)
    sas_token = m.group(1)

  if account_name is None and container_name is None and sas_token is None:
    sas_url = input("Please provide the SAS url: ")
    return get_account_settings(sas_url)

  if account_name is None:
    account_name = input("Please enter the account name: ")

  if container_name is None:
    container_name = input("Please enter the container name: ")

  if sas_token is None:
    sas_token = input("Please enter the SAS token: ")

  if blob_name is None:
    blob_name = input("Please enter the name of the BLOB: ")

  if blob_aeskey is None:
    blob_aeskey = input("Please enter the AES key (base64): ")

  return {"account_name": account_name, "container_name": container_name, "blob_name": blob_name, "sas_token": sas_token, "sas_url": sas_url, "blob_aeskey": base64.b64decode(blob_aeskey), "outdir": output_dir}

def decrypt_chunk(chunk_data, key):
  iv = chunk_data[:12]
  ciphertext = chunk_data[12:-16]
  tag = chunk_data[-16:]
  #print("IV (" + str(len(iv)) + "): (hex): " + ''.join(format(x, '02x') for x in iv))
  #print("Ciphertext (" + str(len(ciphertext)) + ") (hex): " + ''.join(format(x, '02x') for x in ciphertext))
  #print("Tag (" + str(len(tag)) + ") (hex): " + ''.join(format(x, '02x') for x in tag))

  print("    Decrypting chunk...")
  decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
  plaintext_chunk = decryptor.update(ciphertext) + decryptor.finalize()
  return plaintext_chunk

def sha256sum(filename):
  with open(filename, "rb", buffering=0) as f:
    return hashlib.file_digest(f, 'sha256').hexdigest()

def download_blob(container_name, blob_name, blob_service_client, aeskey, output_dir):
  print(f'* Connecting to container {container_name}')
  container_client = blob_service_client.get_container_client(container_name)

  print(f'* Connecting to blob {blob_name}')
  blob_client = container_client.get_blob_client(blob_name)
  
  blob_properties = blob_client.get_blob_properties()
  print("* Size of blob: " + str(blob_properties.size))

  # Initialize variables
  offset = 0
  chunk_count = 0

  # Read chunks, decrypt them and write them to the filesystem
  with open(output_dir + "/" + blob_name, "wb") as f:
    while offset < blob_properties.size:
      chunk_count += 1
      chunk_length = int.from_bytes(blob_client.download_blob(offset, 8).readall(), "big")
      offset += 8
      print("  Reading chunk " + str(chunk_count) + " (" + str(chunk_length) + " bytes)")
      chunk_data = blob_client.download_blob(offset, chunk_length).readall()
      offset += chunk_length
      plaintext = decrypt_chunk(chunk_data, aeskey)
      f.write(plaintext)
  print(f"  Download and decryption of {blob_name} complete.")
  print("Generating sha256 hash...")
  sha256 = sha256sum(output_dir + "/" + blob_name)
  print(f"  SHA256: {sha256}")

def main():
  account_settings = get_account_settings()

  # Blob Service Client
  blob_url = f'https://{account_settings["account_name"]}.blob.core.windows.net'
  print(f'* Setup Blob Service Client ({blob_url})')
  blob_service_client = BlobServiceClient(account_url=blob_url, credential=account_settings["sas_token"])

  # Download the blob
  download_blob(account_settings["container_name"], account_settings["blob_name"], blob_service_client, account_settings["blob_aeskey"], account_settings["outdir"])

if __name__ == "__main__":
  main()
