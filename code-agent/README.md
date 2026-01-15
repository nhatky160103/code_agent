# Code Agent

Code Agent is a multi-agent AI system designed to assist with various code-related tasks, including code analysis, bug fixing, and code refactoring. This project provides a command-line interface (CLI) for users to interact with the Code Agent and leverage its capabilities.

## Features

- Analyze codebases to identify issues and suggest improvements.
- Automatically fix bugs in the code.
- Refactor code to enhance readability and maintainability.
- Generate test code and evaluate test results.
- Provide structured logging for better traceability.

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To use the Code Agent, run the following command in your terminal:

```
python main.py <task> [options]
```

### Arguments

- `task`: The task you want the Code Agent to perform (e.g., `analyze codebase`, `fix bugs`, `refactor code`).
- `--api-key`: Your OpenRouter API key (optional, can also be set via environment variable).
- `--file`: Specify a specific file to work on (optional).
- `--output`: Specify an output file for results in JSON format (optional).
- `--context`: Provide additional context as a JSON string (optional).

## Logging

The application supports structured logging. Logs are saved in the specified log directory, and you can configure the log level and log file location in the settings.

## Documentation

For detailed usage instructions and API documentation, please refer to the following files in the `docs` directory:

- [Guide](docs/guide.md): A comprehensive guide on how to use the Code Agent and its features.
- [API Documentation](docs/api.md): Detailed information about the API endpoints and their usage.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.