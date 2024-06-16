#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()

services = Spark.Client().services
response = services.execute('my-folder/my-service')
print(response.data)
services.close()
