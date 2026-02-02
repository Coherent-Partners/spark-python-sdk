import cspark.sdk as Spark
from dotenv import load_dotenv


def list_categories(folders: Spark.Folders):
    response = folders.categories.list()
    print(response.data)


def save_category(folders: Spark.Folders):
    response = folders.categories.save('My Category', key='my-category-key')
    print(response.data)


def delete_category(folders: Spark.Folders):
    response = folders.categories.delete('my-category-key')
    print(response.data)


def list(folders: Spark.Folders):
    response = folders.find('my-folder')
    print(response.data)


def create(folder: Spark.Folders):
    response = folder.create('my-folder', cover=open('cover.png', 'rb'))
    print(response.data)


def update(folder: Spark.Folders):
    response = folder.update('uuid', description='sample description')
    print(response.data)


def delete(folder: Spark.Folders):
    response = folder.delete('uuid')
    print(response.data)


if __name__ == '__main__':
    load_dotenv()

    try:
        with Spark.Client() as spark:
            folders = spark.folders
            list_categories(folders)
            save_category(folders)
            delete_category(folders)

            list(folders)
            create(folders)
            update(folders)
            delete(folders)
    except Spark.SparkError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
