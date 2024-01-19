from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.node_parser import CodeSplitter


class RepositoryIndex:
    """
    Represents an indexed view of a GitHub repository's Python files.

    This class is responsible for indexing the Python files within a specified GitHub repository. The files are indexed using a code splitter for large documents and stored in a vector index for facilitating efficient code querying based on textual similarity.

    Attributes:
        github_api (GitHubAPIWrapper): An instance of the wrapper for GitHub API operations.
        github_repository (str): The full name of the GitHub repository to be indexed.
        files (List[str]): A list of file paths, filtered to include only Python files.
        documents (List[Document]): A list of Document objects representing the content and metadata of the indexed files.
        index (VectorStoreIndex): An index structure for storing and querying the documents based on vector similarity.

    Methods:
        __init__(self, github_api, github_repository): Initializes the repository index by fetching and indexing the Python files in the given repository.
        query(self, text: str) -> List[Node]: Performs a query on the indexed documents, returning a list of Node objects sorted by relevance and lines of code.
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
            # TODO: incorporate last_update_time and number_of_commits in metadata
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

        # ranking by score and line of codes
        nodes.sort(key=lambda n: n.score + n.metadata["loc"], reverse=True)
        return nodes
