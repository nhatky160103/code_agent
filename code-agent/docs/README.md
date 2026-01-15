# Code Agent

Code Agent is a multi-agent AI system designed to assist with various code-related tasks, including code analysis, bug fixing, and refactoring. This project aims to streamline the development process by leveraging AI capabilities to enhance code quality and productivity.

## Features

- **Task Management**: Execute various tasks such as analyzing codebases, fixing bugs, and refactoring code.
- **Logging**: Structured logging to track the workflow and results.
- **API Integration**: Utilize the OpenRouter API for enhanced functionality.

## Getting Started

To get started with Code Agent, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/code-agent.git
   cd code-agent
   ```

2. **Install Dependencies**:
   Make sure you have Python installed, then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Configuration**:
   Configure your OpenRouter API key in `config/config_legacy.py` or set it as an environment variable.

4. **Run the CLI**:
   Use the command line to execute tasks. For example:
   ```bash
   python main.py analyze codebase --file path/to/your/file.py
   ```

## Documentation

- **User Guide**: For detailed instructions on using Code Agent, refer to [guide.md](guide.md).
- **API Documentation**: For developers looking to integrate or extend functionality, see [api.md](api.md).

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.