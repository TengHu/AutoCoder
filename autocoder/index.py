import logging
from dataclasses import dataclass
logging.basicConfig(filename='logfile.log', level=logging.INFO, filemode='a')
from typing import Optional

from llama_index import Document, ServiceContext, VectorStoreIndex
from llama_index.embeddings import OpenAIEmbedding
from llama_index.indices.query.query_transform import HyDEQueryTransform
from llama_index.llms import OpenAI
from llama_index.node_parser import CodeSplitter
from llama_index.postprocessor import LLMRerank
from llama_index.query_engine.transform_query_engine import TransformQueryEngine
from llama_index.retrievers import TransformRetriever
from llama_index.schema import QueryBundle


@dataclass
class QueryResult:
    file_path: str
    content: str
    id: str
    score: Optional[float] = None
    metadata: Optional[dict] = None
    start_char_idx: Optional[int] = None
    end_char_idx: Optional[int] = None


class RepositoryIndex:
    logger = logging.getLogger(__name__)

    def __init__(self, github_repository, codebase):
        self.codebase = codebase
        self.github_repository = github_repository
        self.logger.info('Initializing RepositoryIndex with github_repository: ' + github_repository + ', codebase: ' + codebase)

        self.llm = OpenAI(model="gpt-3.5-turbo-16k", temperature=0.1, max_tokens=256)
        self.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")
        self.setup()

    def setup(self):
        files = self.codebase.list_files_in_bot_branch()
        self.files = [file for file in files if ".py" in file]
        self.logger.info('Files in bot branch: ' + str(self.files))

        self.documents = []
        for i, file in enumerate(self.files):
            text = self.codebase.read_file(file)
            self.documents.append(Document(text=text, metadata={"file": file}))

        code_splitter = CodeSplitter(language="python", chunk_lines=40, chunk_lines_overlap=25, max_chars=1500)
        self.service_context = ServiceContext.from_defaults(llm=self.llm, embed_model=self.embed_model, text_splitter=code_splitter)
        self.index = VectorStoreIndex.from_documents(self.documents, service_context=self.service_context)
        self.logger.info('Index setup complete')

    def _retrieve_with_transform(self, query_bundle: QueryBundle):
        base_retriever = self.index.as_retriever(similarity_top_k=50, response_mode="no_text")
        self.logger.info('Base retriever created')

        hyde = HyDEQueryTransform(include_original=True, llm=self.llm)
        self.logger.info('HyDEQueryTransform created')

        transform_retriever = TransformRetriever(base_retriever, hyde)
        self.logger.info('TransformRetriever created')

        retrieved_nodes = transform_retriever.retrieve(query_bundle)
        self.logger.info('Retrieved nodes: ' + str(retrieved_nodes))
        return retrieved_nodes

    def _prune(self, retrieved_nodes, top_k=5):
        # retrieved_nodes = retrieved_nodes[
        #     : len(
        #         self.find_numbers_before_drop(
        #             [rn.score for rn in retrieved_nodes], margin=0.03
        #         )
        #     )
        # ]
        retrieved_nodes = [rn for rn in retrieved_nodes if rn.score > 0.65]
        processed_nodes = []
        for node in retrieved_nodes[:top_k]:
            processed_nodes.append(node)

        return processed_nodes

    def query(self, question: str):
        query_bundle = QueryBundle(question)
        retrieved_nodes = self._retrieve_with_transform(query_bundle)
        retrieved_nodes = self._rerank(retrieved_nodes, query_bundle)
        retrieved_nodes = self._prune(retrieved_nodes, top_k=5)

        nodes_dict = [node.to_dict() for node in retrieved_nodes]

        # Parse nodes into query results
        query_results = []
        for node in nodes_dict:
            query_results.append(
                QueryResult(
                    id=node["node"]["id_"],
                    file_path=node["node"]["metadata"]["file"],
                    content=node["node"]["text"],
                    score=node["score"],
                    start_char_idx=node["node"]["start_char_idx"],
                    end_char_idx=node["node"]["end_char_idx"],
                    metadata={},
                )
            )

        # merge code snippets
        snippet_by_file = defaultdict(list)
        for qr in query_results:
            snippet_by_file[qr.file_path].append((qr.start_char_idx, qr.end_char_idx))

        final_query_results = []
        for file_path, snippets in snippet_by_file.items():
            # merge snippets
            snippet_by_file[file_path] = self._merge_intervals(snippets, margin=25)

            file_content = self.codebase.read_file(file_path)
            for processed_snippet in snippet_by_file[file_path]:
                # drop small snippet
                if processed_snippet[1] - processed_snippet[0] > 25:
                    final_query_results.append(
                        QueryResult(
                            id=f"{file_path}_{processed_snippet[0]}_{processed_snippet[1]}",
                            file_path=file_path,
                            content=file_content[
                                processed_snippet[0] : processed_snippet[1]
                            ],
                            start_char_idx=processed_snippet[0],
                            end_char_idx=processed_snippet[1],
                            metadata={},
                        )
                    )
        return final_query_results

    def _rerank(self, nodes, query_bundle):
        def calculate_score(node):
            return node.node.end_char_idx - node.node.start_char_idx

        # reranker = LLMRerank(
        #     choice_batch_size=5,
        #     top_n=10,
        #     service_context=self.service_context,
        # )
        # retrieved_nodes = reranker.postprocess_nodes(nodes, query_bundle)
        # return retrieved_nodes

        # nodes.sort(key=lambda x: calculate_score(x), reverse=True)

        return nodes

    def _merge_intervals(self, intervals, margin=25):
        if not intervals:
            return []

        intervals.sort(key=lambda x: x[0])
        merged_intervals = [intervals[0]]

        for interval in intervals[1:]:
            current_start, current_end = (
                merged_intervals[-1][0],
                merged_intervals[-1][1],
            )
            new_start, new_end = (
                interval[0],
                interval[1],
            )

            if current_end + margin >= new_start:
                merged_intervals[-1] = (current_start, max(current_end, new_end))
            else:
                merged_intervals.append(interval)

        return merged_intervals

    def find_numbers_before_drop(self, arr, margin=0.03):
        result = []
        for i in range(len(arr) - 1):
            if arr[i] > arr[i + 1] + margin:
                # Found a big drop, consider all numbers before this point
                result.extend(arr[: i + 1])
                break
        return result
