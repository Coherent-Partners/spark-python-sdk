#!/usr/bin/env -S rye run python
import cspark.sdk as Spark

# print(Spark.about)
spark = Spark.Client(env='dev', tenant='dev', token='token')
resp = spark.services.execute()
# print(resp.json())
