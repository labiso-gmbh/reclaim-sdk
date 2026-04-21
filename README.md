# reclaim-sdk - Python SDK for Reclaim.ai

> **Migrating from 0.6.x to 0.7.0?** See `CHANGELOG.md` — enums moved, `user` param auto-resolved, new required Task fields.

⚠️ **WARNING: Major Changes in Version 0.5+** ⚠️

The codebase has undergone substantial modifications starting from version 0.5. These updates introduce breaking changes that may impact existing implementations. Please consult the documentation thoroughly before upgrading from earlier versions.

reclaim-sdk is a Python SDK designed for the Reclaim.ai API. It offers a straightforward and developer-friendly interface for managing tasks within Reclaim.ai. Please note that this SDK is not officially affiliated with Reclaim.ai and has been reverse-engineered from the Reclaim.ai web app, as well as utilizing the Swagger Spec provided by AJ from Reclaim.ai =>[Swagger Spec](https://api.app.reclaim.ai/swagger/reclaim-api-0.1.yml). Consequently, there may be bugs, and the API is subject to change without notice. Version stability is not guaranteed.

## Features
At present, reclaim-sdk exclusively supports task management. Its primary function is to integrate various tools with Reclaim.ai, enabling the efficient handling of tasks from project management, calendars, and similar applications within Reclaim.ai. For other features, such as managing habits or custom hours, users should utilize the Reclaim.ai web app directly.

**If something is missing for you, please open an issue or a pull request.**

## Installation
To install reclaim-sdk, simply run the following command:
```bash
pip install reclaim-sdk
```

## Configuration
You can get an API key from [here](https://app.reclaim.ai/settings/developer).

There are now two ways to configure the SDK with your API key:

1. Using the `RECLAIM_TOKEN` environment variable:
   ```python
   import os
   os.environ["RECLAIM_TOKEN"] = "YOUR_API_KEY"
   ```

2. Using the new `configure` method:
   ```python
   from reclaim_sdk.client import ReclaimClient
   
   ReclaimClient.configure(token="YOUR_API_KEY")
   ```

The `configure` method allows you to set up the client with your API token (and optionally a base URL) at any point in your code before making API calls.

## Usage
The SDK uses Pydantic models for better type checking and data validation. Please refer to code examples below:

- [Task Management](/examples/task_management.py)

## Contributing
Contributions are welcome. Please open an issue or a pull request. If you want to add a new resource, please have a look at the [`BaseResource` class](/reclaim_sdk/resources/base.py). The [`Task` class](/reclaim_sdk/resources/task.py) is a good example of how to implement a new resource. Reference the [Swagger Spec](https://api.app.reclaim.ai/swagger/reclaim-api-0.1.yml) for the available endpoints and also use the network tab in the browser to see the request and response payloads, as the Swagger Spec may not always be up-to-date or complete.

## License
[MIT License](https://choosealicense.com/licenses/mit/)

Copyright (c) 2022 Laurence Labusch

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.