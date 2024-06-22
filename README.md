# Overview

This API is built with FastAPI to offer a performant and user-friendly interface for data management and retrieval. This project was part of the 3S learning community Grounded Project 133. The goal of the API is to create a link between the database and the front end, improving the efficiency of data operations.

# Key Features
* Routes for Different Types of Data
  * Root Router: /
    * Methods: GET
    * Description: Initializes the root of the API with a simple check to ensure that the API started correctly and is working.
  * Ground Data Router: /schemas
    * Methods: GET
    * Description: Manages operations related to public ground data, exposing public schemas, listing tables under a schema, and retrieving data from specified tables with filtering and restriction capabilities.
  * User Data Router: /user-data
    * Methods: GET, POST, PATCH, DELETE
    * Description: Provides endpoints for users to manage their data stored in their private schema. Includes basic operations and helper endpoints like getting all tables available in the user schema and retrieving table structure.
  * Authentication Router: /auth
    * Methods: GET, POST
    * Description: Handles user authentication and account creation, and provides a way to check the current user to ensure the login worked.
* Protected Routes
  * Dependency Injection: Implemented to secure certain routes or endpoints, ensuring that only authorized users can access them.
* Reusable Functions
  * Modular Code: Functions are designed to be reusable, facilitating easier future development and maintenance.
* Pydantic Models
  * Request and Response Models: For consistent data validation and structure.
  * User Authentication and Signup Models: To handle user data securely and efficiently.
  * Token Schema and Token Payload: For managing authentication tokens.

# Running the API
To get the API up and running locally using Docker, follow these steps:

1. Pull the latest image from the GitHub Container Registry:
   ```
   docker pull ghcr.io/0unkn0wn/3s-api:latest
   ```
2. Run the API in a Docker container:
   ```
   docker run -d --name api-container -p 8000:8000 ghcr.io/0unkn0wn/3s-api:latest
   ```
3. View the logs to monitor and check for any errors:
   ```
   docker logs api-container
   ```
4. Navigate to `0.0.0.0:8000/docs` to try the API and see the available endpoints.

# Future Development
Potential future improvements for the API include:

* Single Sign-On (SSO) Integration: Enhance security and user experience by implementing SSO using the [FastAPI SSO library](https://github.com/tomasvotava/fastapi-sso). This will allow users to log in using various identity providers.
* File Upload Capability: Add support for file uploads to expand functionality and use cases.
