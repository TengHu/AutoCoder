from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.node_parser import CodeSplitter


class RepositoryIndex:
    """
    The RepositoryIndex class is responsible for indexing the codebase of a GitHub repository.

    It interacts with the GitHub API to retrieve file information and uses the Llama Index to create a searchable vector index of the code.

    Attributes:
        github_api: An instance of GitHubAPIWrapper used to interact with the GitHub API.
        github_repository: The name of the GitHub repository being indexed.
        files: A list of file paths in the repository, filtered to include only Python files.
        documents: A list of Document objects representing the indexed files.
        index: An instance of VectorStoreIndex that allows querying the indexed documents.

    Methods:
        __init__(self, github_api, github_repository): Initializes the RepositoryIndex with the GitHub API and repository name.
        query(self, text: str): Queries the index with a given text and returns matching nodes.

    Example:
        >>> github_api = GitHubAPIWrapper(...)
        >>> repo_index = RepositoryIndex(github_api, 'my_repository')
        >>> nodes = repo_index.query('search query')
    """
    def __init__(self, github_api, github_repository):
        self.github_api = github_api

        content = self.github_api.list_files_in_main_branch()
        files = content.split("\n")[1:]
        self.files = [file for file in files if ".py" in file]

        print(f"Indexing codebase {github_repository}")
        self.documents = []
        for i, file in enumerate(self.files):
            print(f"Indexing {file}")
            text = self.github_api.read_file(file)
            loc = len([line for line in text.split("\n") if bool(line)])
            # TODO: get last update time,  number of commits
            self.documents.append(
                Document(text=text, metadata={"file": file, "loc": loc})
            )

        code_splitter = CodeSplitter(language="python", chunk_lines_overlap=25)
        service_context = ServiceContext.from_defaults(text_splitter=code_splitter)
        self.index = VectorStoreIndex.from_documents(
            self.documents, service_context=service_context
        )

    def query(self, text: str):
        query_engine = self.index.as_query_engine(
            similarity_top_k=10, response_mode="no_text"
        )
        response = query_engine.query(text)

        nodes = response.source_nodes

        # TODO: ranking by last update time, score, length, number of commits
        nodes.sort(key=lambda n: -n.score)
        return nodes
