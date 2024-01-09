lass RepositoryIndex:
    def __init__(self, github_api):
        self.github_api =  github_api

        content = self.github_api.list_files_in_main_branch()
        files = content.split('
')[1:]
        self.files = [file for file in files if '.py' in file]

        print (f"Indexing codebase {github_repository}")
        self.documents = []
        for i, file in enumerate(self.files):
            print (f"Indexing {file}")
            text = self.github_api.read_file(file)
            loc = len([line for line in text.split('
') if bool(line)])
            # TODO: get last update time,  number of commits
            self.documents.append(Document(text=text, metadata={"file": file, "loc": loc}))

        code_splitter = CodeSplitter(language='python', chunk_lines_overlap=25)
        service_context = ServiceContext.from_defaults(text_splitter=code_splitter)
        self.index = VectorStoreIndex.from_documents(
            self.documents, service_context=service_context
        )


    def query(self, text: str):
        query_engine = self.index.as_query_engine(similarity_top_k=10, response_mode="no_text")
        response = query_engine.query(text)

        nodes = response.source_nodes
        
        # TODO: ranking by last update time, score, length, number of commits
        nodes.sort(key=lambda n: -n.score)
        return nodes