from typing import List


# TODO: print messages when Codebase class is instantiated or when a method is called
class Codebase:
    def __init__(self, langchain_github_api):
6.         self.langchain_github_api = langchain_github_api
7.         self.file2code = {}

9.     def list_files_in_bot_branch(self):
10.         content = self.langchain_github_api.list_files_in_bot_branch()
11.         files = content.split("\n")[1:]
12.         return files

14.     def clear_cache(self):
15.         self.file2code = {}

17.     def create_pull_request(self, pr_query):
18.         return self.langchain_github_api.create_pull_request(pr_query)

20.     def get_active_branch(self):
21.         return self.langchain_github_api.active_branch

23.     def get_issues(self):
24.         return self.langchain_github_api.get_issues()

26.     def create_branch(self, branch: str):
27.         return self.langchain_github_api.create_branch(branch)

29.     def read_file(self, filepath):
30.         response = None

32.         if filepath not in self.file2code:
33.             response = self.read_file_wrapper(filepath)

35.             # TODO: throw an exception if the file is not found
36.             if f"File not found `{filepath}`" in response:
37.                 return None
38.             self.file2code[filepath] = response

40.         response = self.file2code[filepath]

42.         return response

44.     def read_file_wrapper(self, filepath):
45.         response = self.langchain_github_api.read_file(filepath)

47.         return response

49.     def read_files(self, files: List[str]) -> List[str]:
50.         response = {}
51.         for file in files:
52.             read_file_response = self.read_file(file)

54.             if read_file_response:
55.                 response[file] = read_file_response
56.         return response

58.     def create_file(self, file_query):
59.         return self.langchain_github_api.create_file(file_query)

61.     def update_file(self, content):
62.         file_path = content.split("\n")[0]
63.         self.file2code.pop(file_path, None)

65.         return self.langchain_github_api.update_file(content)

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

        # line index are 1-indexed
        return content_lines, start_line_idx + 1, end_line_idx + 1
