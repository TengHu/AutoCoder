from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.node_parser import CodeSplitter


class RepositoryIndex:
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
            last_update_time = self.github_api.get_last_update_time(file)
            number_of_commits = self.github_api.get_number_of_commits(file)
            self.documents.append(
                Document(text=text, metadata={"file": file, "loc": loc, "last_update_time": last_update_time, "number_of_commits": number_of_commits})
            )
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

        nodes.sort(key=lambda n: (-n.metadata.get('last_update_time', 0), -n.score, -n.metadata.get('length', 0), -n.metadata.get('number_of_commits', 0)))
        return nodes
