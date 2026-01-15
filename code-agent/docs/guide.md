# Guide to Using Code Agent

## Introduction

Welcome to the Code Agent guide! This document provides an overview of how to effectively use the Code Agent CLI for various code-related tasks. Code Agent is designed to assist developers in analyzing, fixing, and refactoring code with the help of AI-driven agents.

## Getting Started

### Installation

To get started with Code Agent, ensure you have Python installed on your machine. You can install the required dependencies by running:

```
pip install -r requirements.txt
```

### Configuration

Before using Code Agent, you need to set up your API key. You can do this by either:

1. Setting the `OPENROUTER_API_KEY` environment variable.
2. Passing the API key as a command-line argument using the `--api-key` flag.

### Running the CLI

You can run the Code Agent CLI using the following command:

```
python main.py <task> [options]
```

Replace `<task>` with the specific task you want to perform, such as `analyze codebase`, `fix bugs`, or `refactor code`.

### Command-Line Options

- `--api-key`: Your OpenRouter API key.
- `--file`: Specify a specific file to work on.
- `--output`: Define an output file for results in JSON format.
- `--context`: Provide additional context as a JSON string.

## Features

### Analyze Codebase

Use the `analyze codebase` task to analyze your code for potential issues and improvements. The results will include an analysis summary, suggestions for best practices, and more.

### Fix Bugs

The `fix bugs` task allows you to automatically identify and fix bugs in your code. The output will include the fixed code and a summary of the changes made.

### Refactor Code

With the `refactor code` task, you can improve the structure and readability of your code. The results will provide refactored code along with suggestions for better organization.

## Viewing Results

After executing a task, the results will be printed to the console. You can also save the results to a specified output file in JSON format by using the `--output` option.

## Conclusion

The Code Agent is a powerful tool for developers looking to enhance their coding practices. By leveraging AI-driven insights, you can streamline your workflow and improve code quality. For more detailed information on the API and its endpoints, please refer to the `api.md` document in the `docs` directory. Happy coding!