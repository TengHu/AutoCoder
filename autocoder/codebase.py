class Codebase:
    def __init__(self, github_api):
        self.github_api = github_api
        self.file2code = {}

    def list_files_in_main_branch(self):
        content = self.github_api.list_files_in_main_branch()
        files = content.split("\n")[1:]
        return files

    def read_file(self, filepath):
        response = None

        if filepath not in self.file2code:
            response = self.read_file_wrapper(filepath)
            if f"File not found `{filepath}`" in response:
                # raise Exception(f"{filepath} doesn't exist")
                return None
            self.file2code[filepath] = response

        response = self.file2code[filepath]

        return response

    def read_file_wrapper(self, filepath):
        response = self.github_api.read_file(filepath)

        return response
