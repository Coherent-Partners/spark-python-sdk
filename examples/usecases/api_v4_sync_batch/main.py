import json
import logging

import cspark.sdk as Spark


def read_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


def main():
    source_path = 'inputs.json'
    output_path = 'outputs.json'
    base_url = 'https://spark.uat.us.coherent.global/fieldengineering'
    token = 'Bearer access_token'
    service_uri = 'my-folder/volume-cylinder'

    # ---------------- You do NOT need to modify below this line ----------------
    logging.basicConfig(filename='console.log', filemode='w', format=Spark.DEFAULT_LOGGER_FORMAT)
    logger = Spark.get_logger()

    writer = open(output_path, 'w')
    services = Spark.Client(base_url=base_url, token=token, timeout=90_000).services

    # 1. Read data from a source file
    dataset = read_file(source_path)
    total = len(dataset)

    logger.info(f'{total} records found in {source_path}')
    writer.write('[\n')

    # 2. Execute sync batch and save results to a file
    try:
        response = services.execute(service_uri, inputs=dataset)
        result = {'inputs': dataset, 'outputs': response.data['outputs']}  # type: ignore

        writer.write(json.dumps(result, indent=2))
        logger.info(f'bulk of {total} records processed successfully')
    except Exception as exc:
        logger.warning(f'failed to process bulk of {total} records')
        logger.error(exc)

    # 3. Clean up resources
    services.close()
    writer.write('\n]')
    writer.close()


if __name__ == '__main__':
    main()
