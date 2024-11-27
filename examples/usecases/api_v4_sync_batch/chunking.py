import json
import logging
import math

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
    chunk_size = 20

    # ---------------- You do NOT need to modify below this line ----------------
    logging.basicConfig(filename='console.log', filemode='w', format=Spark.DEFAULT_LOGGER_FORMAT)
    logger = Spark.get_logger()

    writer = open(output_path, 'w')
    services = Spark.Client(base_url=base_url, token=token, timeout=90_000).services

    # 1. Read data from a source file
    dataset = read_file(source_path)
    total = len(dataset)
    batch_size = math.ceil(total / chunk_size)

    logger.info(f'{total} records found in {source_path}')
    writer.write('[\n')

    # 2. Execute sync batch and save results to a file
    for i in range(batch_size):
        start = i * chunk_size
        end = min(start + chunk_size, total)
        inputs = dataset[start:end]

        try:
            response = services.execute(service_uri, inputs=inputs)
            result = {'inputs': inputs, 'outputs': response.data['outputs']}  # type: ignore

            newline = ',\n' if i < batch_size - 1 else ''
            writer.write(json.dumps(result, indent=2) + newline)
            logger.info(f'bulk {i + 1}/{batch_size} of {len(inputs)} records processed successfully')
        except Exception as exc:
            logger.warning(f'failed to process bulk {i + 1}/{batch_size} of {len(inputs)} records')
            logger.error(exc)

    # 3. Clean up resources
    services.close()
    writer.write('\n]')
    writer.close()


if __name__ == '__main__':
    main()
