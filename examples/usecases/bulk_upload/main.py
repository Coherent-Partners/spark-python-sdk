from dotenv import load_dotenv
from helpers.config import load_config
from helpers.manager import Manager


def main():
    load_dotenv()

    config = load_config()
    manager = Manager(config)
    try:
        services, size = config.get('services', []), config.get('bulk_size', 5)
        for group in manager.group(services, by=size):
            manager.run(group)
    finally:
        manager.dispose()


if __name__ == '__main__':
    main()
