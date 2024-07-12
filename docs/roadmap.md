# Roadmap

The SDK is currently in its early stages of development. The following points
outline the roadmap for the SDK:

- **Analysis**
  - [x] Roadmap for the SDK
  - [x] Developer experience
  - [x] Partial parity with the core APIs
  - [x] Python version for development: 3.11
  - [x] Python versions to support: 3.7+
  - [x] PyPI vs Anaconda: PyPI
  - [x] OSI License: Apache 2.0
  - [ ] End of life (EOL) policy: TBD

- **Architecture**
  - [x] Basic project structure (src, test, docs, examples, etc.)
  - [x] Distribution layers
    - [x] SDK layer: exposes basic API client and resources
    - [ ] Utils layer: exposes data (de)serialization, (de)compression, memoization, among other helpers.
  - [x] Core HTTP module built on top of [httpx](https://pypi.org/project/httpx/)
    - [x] Support synchronous requests
    - [ ] Support asynchronous requests
  - [x] Client configuration
    - [x] Support for environment variables (e.g., `.env`)
    - [ ] Support for configuration files
      - [ ] Configuration file types: `.yaml` and `.json`
      - [ ] Configuration file schema (JSON schema)
  - [x] Security schemes
    - [x] API key (long-lived token)
    - [x] Bearer token (short-lived token)
    - [x] OAuth2.0 client credentials grant
  - [ ] Logging for debugging and visibility
  - [x] Graceful error handling
  - [ ] Date and time handling
  - [x] Dependency management and build system: [rye](https://rye.astral.sh/)

- **Development**
  - [x] Git repository on GitHub
    - [x] Branch protection rules: main, dev
    - [ ] Environment variables and secrets for CI/CD
  - [x] Git commit [message convention](https://www.conventionalcommits.org/)
  - [ ] Git hooks (pre-commit, pre-push, etc.)
  - [x] Code linting
  - [x] Code formatting
  - [ ] Code documentation

- **Testing**
  - [x] Unit tests for utility functions
  - [x] Unit tests for API resources
  - [ ] Test coverage: 80%+
  - [ ] Usability testing (early adopters)

- **Deployments**
  - [x] Scripts for building and packaging
  - [x] CI/CD with GitHub Actions
    - [ ] Run jobs on push, pull request and cron schedule
    - [ ] Job for environment setup (Python versions, dependencies, etc.)
    - [x] Job for source code robustness (linting, formatting, etc.)
    - [ ] Job for automated releases with [release-please](https://github.com/googleapis/release-please-action)

  - [x] PyPI distribution
    - [x] Account and ownership (authors)
    - [x] Technical governance (collaborators)
    - [x] Publications
      - [x] Manual releases
      - [ ] Automated releases
    - [ ] Branding and marketing

- **Documentation**
  - [x] Contribution guide (developer setup, testing, etc.)
  - [x] Usage guide (installation, API reference, etc.)
  - [x] Basic examples
  - [ ] Sample code snippets per use case

- **Community**
  - [x] Code of conduct
  - [x] Contributing guidelines
  - [ ] Issue templates
  - [ ] Pull request templates
  - [ ] Security policy
  - [x] Support channels
    - [ ] Company promoted support (website, forums, etc.)
    - [x] GitHub Discussions
    - [ ] Slack workspace
    - [ ] Reddit
    - [ ] Twitter
    - [ ] Stack Overflow
  - [ ] Community events (webinars, developer conference, etc.)

## Phase 1: Distribute a beta version

Here's a high-level plan for the first phase of development:

- Authentication API
  - Authenticate using an API key
  - Authenticate using a bearer token
  - Authenticate using OAuth2.0 client credentials
  - Refresh a bearer token upon expiry

- Services API
  - Execute a Spark service
  - Get all the versions of a service
  - Get the schema for a given service
  - Get the metadata of a service

- Batches API
  - Describe the batch pipelines across a tenant
  - Create a new batch pipeline
  - Start a client-side batch pipeline by ID
  - Retrieve the details of a batch pipeline
  - Get the status of a batch pipeline
  - Add input data to a batch pipeline
  - Retrieve the output data from a batch pipeline
  - Close a batch pipeline
  - Cancel a batch pipeline

### Collect feedback and apply improvements

### Release a stable version

## Phase 2: Add utils layer

## Phase 3: Add support for asynchronous requests
