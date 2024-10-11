import cspark.wasm as Hybrid

response = Hybrid.Client.health_check()
print(response.data)
