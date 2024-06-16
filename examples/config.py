#!/usr/bin/env -S rye run python
from typing import cast

import cspark.sdk as Spark
from dotenv import load_dotenv

load_dotenv()

spark = Spark.Client()
oauth = cast(Spark.OAuth, spark.config.auth.oauth)
oauth.retrieve_token(spark.config)  # also return `AccessToken` object.
print(f'access token: {oauth.access_token}')
