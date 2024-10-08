# Changelog

All notable changes to this project will be documented in this file.
See [standard-version](https://github.com/conventional-changelog/standard-version)
for commit guidelines.

## 0.1.7 (2024-10-08)

- Add support for ImpEx API
  - Export Spark entities (versions, services, or folders)
  - Import Spark entities
- Add support for service creation
  - Upload and compile a service
  - Poll its status until completion
  - Publish the service

## 0.1.6 (2024-09-13)

- Add support for deleting a service
- Remove `httpx` logging handler
- Add logger options for more personalized logging

## 0.1.5 (2024-09-02)

- Execute a service using Transforms API
- Add support for Validation API
- Apply minor improvements
- Add GitHub issue templates

## 0.1.4 (2024-08-15)

- Add support for:
  - downloading WebAssembly modules and Spark files
  - rehydrating service execution logs into the original Excel file
  - recompiling services
- Fix copy issue in `BaseUrl` and `Config` classes
- Enable `gzip` and `deflate` encoding for request payload during service execution

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
