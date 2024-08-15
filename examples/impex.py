#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv


def save_file(content: bytes, filename: str):
    with open(filename, 'wb') as file:
        file.write(content)
        print(f'{filename} downloaded successfully 🎉')


def download_file():
    content = Spark.Client.download('https://httpbin.org/robots.txt')
    save_file(content, 'robots.txt')


def download(wasm: Spark.Wasm):
    response = wasm.download(version_id='uuid')
    save_file(response.buffer, 'wasm.zip')


if __name__ == '__main__':
    load_dotenv()
    download_file()

    spark = Spark.Client()
    with spark.wasm as wasm:
        download(wasm)
