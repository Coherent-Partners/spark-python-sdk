#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()

services = Spark.Client().services
response = services.execute('my-folder-1/Subservices')
if response.status_code == 200:
    print(response.json())
else:
    print(response.text)
services.close()
