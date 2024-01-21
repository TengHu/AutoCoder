# AutoCoder: An Experimental Coding Agent

AutoCoder is a cutting-edge, experimental coding agent that leverages the power of Large Language Models (LLM), `actionweaver`, `llama_index` for Retrieval-Augmented Generation (RAG), and `langsmith` for enhanced observability.


### Important Notice
Please note that this demo app is currently in an experimental phase and is not recommended for deployment in production environments. The app has also not undergone extensive prompt engineering to date.

## Architecture 
![graph](docs/figures/workflow.png)

## Capabilities
AutoCoder is adept at a broad spectrum of tasks, which include:
-  GetIssues
    - **Description**: Fetches a list of issues from the GitHub repository.
    - **Example Question**: "Give me all active issues."
- QuestionAnswer
    - **Description**: Answers questions about the codebase.
    - **Example Question**: "How is the AutoCoder class implemented?"
- CreatePullRequest
    - **Description**: Creates a new Pull Request in a Git repository.
    - **Example Question**: "Create a PR."
- PlanAndImplementCodeChange
    - **Description**: Plans and implements code changes based on a given description.
    - **Example Question**: "Update the `autocoder/bot.py` to use AzureOpenAI instead of OpenAI."

## Local Setup Guide

### Step 1: Create a GitHub App
- Follow the instructions on creating a GitHub App on [GitHub's documentation](https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps#building-a-github-app).
- Grant the Autocoder app Read and Write access in [GitHub App settings](https://github.com/settings/installations). It should have access to administration, code, discussions, issues, pull requests, and repository projects for the intended repository.

### Step 2: Set Up Environment Variables
- **GitHub API Access**: Set `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY`.
- **OpenAI Access**: Set `OPENAI_API_KEY` and specify the model in `MODEL`, e.g., `MODEL=gpt-4-0613`.
- **Langchain Monitoring** (Optional): Set `LANGCHAIN_API_KEY`.

### Step 3: Explore the Demo Notebook or main.py
- Use `notebooks/demo.ipynb` for a practical introduction and experimentation.

## Example Pull Requests
- Fixing to-dos.
- Modifying README files.
- Renaming functions.
- Reading and interpreting LeetCode questions.
- Implementing AutoCoder class in `AutoCoder.java` or Lisp.
- Extracting classes from `autocoder/pydantic_models/file_ops.py` into new files.
- Updating `autocoder/bot.py` to use AzureOpenAI.


## Usage Tips
- Ensure accuracy in file path and detailed descriptions.
- One observation is llm like to add comment/todos, instead of finishing it
- be very descriptiv!


## Contributing
We welcome contributions from the open-source community.

## License
Apache License 2.0




