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
    logfmt = '[%(name)s] %(asctime)s %(levelname)s - %(message)s'
    logging.basicConfig(filename='console.log', filemode='w', format=logfmt)
    logger = Spark.get_logger()

    writer = open(output_path, 'w')
    services = Spark.Client(base_url=base_url, token=token).services

    # 1. Read data from a source file
    dataset = read_file(source_path)
    total = len(dataset)

    logger.info(f'{total} records found in {source_path}')
    writer.write('[\n')

    # 2. Execute each input and save results to the output file
    for i, inputs in enumerate(dataset):
        try:
            response = services.execute(service_uri, inputs=inputs, response_format='original')
            result = {'inputs': inputs, 'outputs': response.data['response_data']['outputs']}  # type: ignore

            newline = ',\n' if i < total - 1 else ''
            writer.write(json.dumps(result, indent=2) + newline)
            logger.info(f'record {i + 1} processed successfully')
        except Exception as exc:
            logger.error(f'failed to process record {i + 1}')
            logger.error(exc)

    # 3. Clean up resources
    services.close()
    writer.write('\n]')
    writer.close()


if __name__ == '__main__':
    main()
