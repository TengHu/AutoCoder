# AutoCoder: An Experimental Coding Agent

AutoCoder is a cutting-edge, experimental coding agent that leverages the power of LLM, [ActionWeaver](https://github.com/TengHu/ActionWeaver) for function calling & orchestration, [LLamaIndex](https://www.llamaindex.ai/) for Retrieval-Augmented Generation (RAG), [Langchain](https://www.langchain.com/) community and [Langsmith](https://www.langchain.com/langsmith) for observability.

Please note that this demo app is not intended for production use.

## Architecture 
![graph](docs/figures/workflow.png)

## Capabilities
AutoCoder is capable of following tasks:
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

- **Example Pull Request - Fixing to-dos**
   - **Title**: Fix Minor TODOs in AutoCoder Project
   - **Description**: This PR fixes a number of small to-dos scattered across the codebase of the AutoCoder project to improve code readability and maintainability.
   - **Labels**: 'enhancement', 'code quality'
   - **Reviewers**: Mention team members who would be best-suited to review your changes.

- **Example Pull Request - Modifying README files**
   - **Title**: Revamp README for better Project Understanding
   - **Description**: This PR updates the README file, enhancing the project description and adding sections for setup instructions and contributor guidelines.
   - **Labels**: 'documentation'
   - **Reviewers**: Usually, a member familiar with the project's documentation would be ideal for review.

- **Example Pull Request - Renaming functions**
   - **Title**: Refactor Function Naming for Code Clarity
   - **Description**: This PR includes renaming functions to reflect their functionality accurately for better code readability and maintainability.
   - **Labels**: 'refactor', 'code quality'
   - **Reviewers**: Ideally, somebody who is familiar with the codebase should review these changes.

- **Example Pull Request - Reading and interpreting LeetCode questions**
   - **Title**: LeetCode Question Interpreter
   - **Description**: This PR introduces an enhancement where the code can read and interpret LeetCode questions.
   - **Labels**: 'new feature'
   - **Reviewers**: Developers familiar with both LeetCode and the existing codebase would make good reviewers.

- **Example Pull Request - Implementing AutoCoder class in `AutoCoder.java` or Lisp**
   - **Title**: Implement AutoCoder Class in Java
   - **Description**: This PR includes the implementation of the 'AutoCoder' class for the Java programming language.
   - **Labels**: 'new feature', 'Java'
   - **Reviewers**: Developers proficient in Java who are familiar with the original 'AutoCoder' class.

- **Example Pull Request - Extracting classes from `autocoder/pydantic_models/file_ops.py` into new files**
   - **Title**: Refactor `file_ops.py` for Better Code Organisation
   - **Description**: This PR entails extracting classes from `file_ops.py` into separate files for better structure and maintainability.
   - **Labels**: 'refactor'
   - **Reviewers**: Developers familiar with the `file_ops.py` codebase would make good reviewers.

- **Example Pull Request - Updating `autocoder/bot.py` to use AzureOpenAI**
   - **Title**: Update AutoCoder to use AzureOpenAI
   - **Description**: This PR updates `autocoder/bot.py` to use AzureOpenAI, a change that affects the bot's ability to execute tasks.
   - **Labels**: 'enhancement', 'AzureOpenAI'
   - **Reviewers**: Reviewers should be familiar with both the old and new systems in order to compare their effectiveness.


## Tips

- **Precision in Requests**: When requesting the bot to perform tasks, be precise with file paths and provide detailed, descriptive information instead of one-liner.
- **Handling Partial Implementations**: The bot may occasionally insert comments such as "to-be-implemented" rather than fully writing out the code. In such cases, you can guide the bot towards the desired outcome through multiple rounds of conversation.


## Contributing
We welcome contributions from the open-source community.

## License
Apache License 2.0




