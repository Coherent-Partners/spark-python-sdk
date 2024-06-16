#!/usr/bin/env -S rye run python
import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()

spark = Spark.Client()
spark.config.auth.oauth.retrieve_token(spark.config)  # also return `AccessToken` object.
print(f'access token: {spark.config.auth.oauth.access_token}')
