import cspark.sdk as Spark
from dotenv import load_dotenv


def list(transforms: Spark.Transforms):
    response = transforms.list('my-folder')
    print(response.data)


def validate(transforms: Spark.Transforms):
    response = transforms.validate('stringified transform content goes here')
    print(response.data)


def save(transforms: Spark.Transforms):
    transform = '{"api_version": "v4", "inputs": "my-jsonata"}'
    response = transforms.save(folder='my-folder', name='my-transform', transform=transform)
    print(response.data)


def get(transforms: Spark.Transforms):
    response = transforms.get('my-folder/my-transform')
    print(response.data)


def delete(transforms: Spark.Transforms):
    response = transforms.delete('my-folder/my-transform')
    print(response.data)


if __name__ == '__main__':
    load_dotenv()

    try:
        with Spark.Client().transforms as transforms:
            list(transforms)
            validate(transforms)
            save(transforms)
            get(transforms)
            delete(transforms)
    except Spark.SparkError as err:
        print(err.message)
        print(err.details)
    except Exception as exc:
        print(f'Unknown error: {exc}')
