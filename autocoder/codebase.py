from typing import List

from autocoder.telemetry import traceable


# TODO: print messages when Codebase class is instantiated or when a method is called
class Codebase:
    def __init__(self, github_api):
        self.github_api = github_api
        self.file2code = {}
        print('Codebase class instantiated')

    def list_files_in_bot_branch(self):
        print('list_files_in_bot_branch called with no parameters')
        content = self.github_api.list_files_in_bot_branch()
        files = content.split('\n')[1:]
        return files

    def set_active_branch(self, branch):
        print(f'set_active_branch called with parameters {branch}')
        return self.github_api.set_active_branch(branch)

    def clear_cache(self):
        print('clear_cache called with no parameters')
        self.file2code = {}

    def create_pull_request(self, pr_query):
        print(f'create_pull_request called with parameters {pr_query}')
        return self.github_api.create_pull_request(pr_query)

    def get_active_branch(self):
        print('get_active_branch called with no parameters')
        return self.github_api.active_branch

    def get_issues(self):
        print('get_issues called with no parameters')
        return self.github_api.get_issues()

    def create_branch(self, branch: str):
        print(f'create_branch called with parameters {branch}')
        return self.github_api.create_branch(branch)

    def read_file(self, filepath, add_line_index=False):
        print(f'read_file called with parameters {filepath}, {add_line_index}')
        response = None
        if filepath not in self.file2code:
            response = self.read_file_wrapper(filepath)
            if f'File not found `{filepath}`' in response:
                raise FileNotFoundError(f'File not found `{filepath}`')
            self.file2code[filepath] = response
        response = self.file2code[filepath]
        if add_line_index:
            lines = response.split('\n')
            response = '\n'.join([f'{line_idx}. ' + lines[line_idx] for line_idx in range(0, len(lines))])
        return response

    def read_file_wrapper(self, filepath):
        print(f'read_file_wrapper called with parameters {filepath}')
        response = self.github_api.read_file(filepath)
        return response

    def read_files(self, files: List[str]) -> List[str]:
        print(f'read_files called with parameters {files}')
        response = {}
        for file in files:
            read_file_response = self.read_file(file)
            if read_file_response:
                response[file] = read_file_response
        return response

    def create_file(self, file_query):
        print(f'create_file called with parameters {file_query}')
        return self.github_api.create_file(file_query)

    @traceable(name="update_file_in_codebase", run_type="tool")
    def update_file(self, content):
        print(f'update_file called with parameters {content}')
        file_path = content.split('\n')[0]
        self.file2code.pop(file_path, None)
        return self.github_api.update_file(content)

    def map_char_idx_to_line_idx(self, file_path, start_char_idx, end_char_idx):
        content = self.github_api.read_file(file_path)

        # Split the content into lines
        content_lines = content.split("\n")

        start_line_idx = end_line_idx = -1
        total_chars = 0

        # Iterate through each line and calculate the cumulative character count
        for line_idx, line in enumerate(content_lines):
            line_length = len(line) + 1  # Add 1 for the newline character
            total_chars += line_length

            # Check if the start character index falls within this line
            if start_char_idx < total_chars and start_line_idx == -1:
                start_line_idx = line_idx

            # Check if the end character index falls within this line
            if end_char_idx <= total_chars and end_line_idx == -1:
                end_line_idx = line_idx
                break

        return content_lines, start_line_idx, end_line_idx
