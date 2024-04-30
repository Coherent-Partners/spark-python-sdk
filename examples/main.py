#!/usr/bin/env -S rye run python
import cspark.sdk as Spark

error = Spark.SparkError('sample error message')
print(str(error))
