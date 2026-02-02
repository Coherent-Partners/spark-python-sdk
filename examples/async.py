import asyncio

from cspark.sdk import AsyncClient


async def main():
    resp = await AsyncClient.health_check('uat.us')
    print(resp.data)


if __name__ == '__main__':
    asyncio.run(main())
