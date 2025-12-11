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


def export_entities_with(impex: Spark.ImpEx):
    downloadables = impex.exp(services=['my-folder/my-service'], max_retries=5, retry_interval=3)
    for count, download in enumerate(downloadables):
        save_file(download.buffer, f'exported-{count}.zip')


def import_entities_with(impex: Spark.ImpEx):
    destination = {'source': 'my-folder/my-service', 'target': 'this-folder/my-service', 'upgrade': 'patch'}
    response = impex.imp(destination, file=open('exported.zip', 'rb'), max_retries=7, retry_interval=3)
    print(response.data)


if __name__ == '__main__':
    load_dotenv()

    try:
        download_file()

        spark = Spark.Client()
        export_entities_with(spark.impex)
        import_entities_with(spark.impex)
        download(spark.wasm)
    except Spark.SparkError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
