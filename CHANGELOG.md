# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version)
for commit guidelines.

## 0.1.4 (2024-08-15)

- Add support for downloading WebAssembly modules
- Add support for downloading Spark files

## 0.1.3 (2024-08-06)

- Fix publish issue with Rye
- Add members `env` and `service` to `BaseUrl` class

## 0.1.2 (2024-07-19)

- Fix `TypeError: 'type' object is not subscriptable` error for Python 3.7.x
- Refactor in `response_format` to handle only `original` and `alike` formats in Services API
- Apply documentation improvements
- Add fixtures to enable testing for API resources
- Add tests for Services API

## 0.1.1 (2024-07-03)

- Add support for Services API
  - Execute a Spark service
  - Get all the versions of a service
  - Get the schema for a given service
  - Get the metadata of a service
- Add support for Batches API
  - Describe the batch pipelines across a tenant
  - Create a new batch pipeline
  - Start a client-side batch pipeline by ID
  - Retrieve the details of a batch pipeline
  - Get the status of a batch pipeline
  - Add input data to a batch pipeline
  - Retrieve the output data from a batch pipeline
  - Close a batch pipeline
  - Cancel a batch pipeline
- Add support for 3 authentication schemes (API key, Bearer token, and OAuth2.0 client credentials)
- Document supported APIs
- Add basic examples

## 0.1.0-beta.0 (2024-05-30)

Initial beta release.
