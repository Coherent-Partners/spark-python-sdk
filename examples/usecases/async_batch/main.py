from helpers import logger, run_batch


def main():
    """Main function to run batch and then do post processing."""
    logger.info('Running batch process...')

    # Step 1: Run batch processing
    run_batch()

    # Step 2: Do your post-processing here, for example aggregrations
    # the batch results are a series of CSV files found in ../outputs

    logger.info('Batch process completed!')


if __name__ == '__main__':
    main()
