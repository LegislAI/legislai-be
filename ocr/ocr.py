import asyncio
import os
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import dspy
from dotenv import load_dotenv
from RAG.Retriever.retriever import Retriever


class DecisionType(Enum):
    KEEP_CONTEXT = "manter_contexto"
    GENERATE_QUERY = "gerar_consulta"
    SKIP_CHUNK = "ignorar_excerto"
    ELABORATE_RATIONALE = "elaborar_fundamento"
    EXTRACT_INFORMATION = "extrair_informacao"
    CROSS_REFERENCE = "cruzar_referencia"

@dataclass
class DocumentReference:
    page: int
    paragraph: int
    content: str
    extracted_info: Dict[str, Any]
    context: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "paragraph": self.paragraph,
            "content": self.content,
            "extracted_info": self.extracted_info,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }

@dataclass
class ActionResult:
    action: DecisionType
    outcome: Optional[Dict[str, Any]] = None
    rationale: str = ""
    relevance_score: float = 0.0


@dataclass
class KnowledgeItem:
    content: str
    source_references: List[DocumentReference]
    confidence: float
    last_updated: datetime = field(default_factory=datetime.now)
    related_items: List[str] = field(default_factory=list)


# @dataclass
# class ProcessingStep:
#     step_num: int
#     chunk: str
#     current_context: str
#     decision: DecisionType
#     rationale: str
#     knowledge_updates: List[Dict[str, Any]]
#     cross_references: List[DocumentReference] = field(default_factory=list)
#     generated_query: Optional[str] = None
#     rag_response: Optional[str] = None
#     extracted_info: Optional[Dict[str, Any]] = None
#     relevance_score: float = 0.0
@dataclass
class ProcessingStep:
    step_num: int
    chunk: str
    actions: List[ActionResult]
    current_context: str
    knowledge_updates: List[Dict[str, Any]]
    cross_references: List[DocumentReference] = field(default_factory=list)
    generated_query: Optional[str] = None

class QueryAnalyzer(dspy.Signature):
    """Analisa a questão do utilizador para determinar a estratégia de extração."""

    query = dspy.InputField(desc="User's query about the document")

    query_type = dspy.OutputField(
        desc="Type of query (general_analysis, specific_info, etc.)"
    )
    extraction_strategy = dspy.OutputField(
        desc="Strategy for extracting relevant information"
    )
    required_fields = dspy.OutputField(desc="List of specific fields to extract")


class ChunkAnalyzer(dspy.Signature):
    """Analisa excertos de texto com base na questão do utilizador. Com isto deves decidir que ação tomar, esta pode ser, elaborar uma questão, guardar a informação como contexto, gerar um pensamento intermédio e seguir para o excerto seguinte"""

    context = dspy.InputField(desc="Current accumulated context")
    chunk = dspy.InputField(desc="New text chunk to analyze")
    query = dspy.InputField(desc="User's query about the document")
    query_strategy = dspy.InputField(desc="Extraction strategy from QueryAnalyzer")
    required_fields = dspy.InputField(desc="Required fields to extract")

    decision: DecisionType = dspy.OutputField(desc="Decision Type")
    rationale = dspy.OutputField(desc="Reasoning behind the decision")
    generated_query = dspy.OutputField(desc="Query for RAG if applicable")
    extracted_info = dspy.OutputField(desc="Extracted information relevant to query")
    relevance_score = dspy.OutputField(desc="Relevance score of chunk to query (0-1)")


class ThoughtGenerator(dspy.Signature):
    """Gera raciocínio e elações intermédias relativamente à questão do utilizador com base em todo o contexto que tens."""

    context = dspy.InputField(desc="Current context")
    query = dspy.InputField(desc="Original user query")
    recent_decision = dspy.InputField(desc="Last processing step details")
    extraction_strategy = dspy.InputField(desc="Current extraction strategy")

    thought = dspy.OutputField(desc="Generated thought or analysis")
    updated_context = dspy.OutputField(desc="New context incorporating the thought")
    query_progress : Optional[str] = dspy.OutputField(desc="Progress towards answering the query")


class ThoughtProcess:
    def __init__(self):
        self.thoughts: List[str] = []

    def add_thought(self, thought: str) -> str:
        formatted_thought = f"### Pensamento {len(self.thoughts) + 1}\n{thought}\n"
        self.thoughts.append(formatted_thought)
        return formatted_thought

    def get_formatted_thoughts(self) -> str:
        return "\n".join(self.thoughts)

class CrossReferenceAnalyzer(dspy.Signature):
    """Analisa potenciais conexões com seções anteriores do documento ou raciocínios."""

    current_chunk = dspy.InputField(desc="Current text chunk")
    knowledge_base = dspy.InputField(desc="Existing knowledge base")
    query = dspy.InputField(desc="User's query")

    related_knowledge = dspy.OutputField(desc="Related previous knowledge")
    connection_type = dspy.OutputField(desc="Type of connection found")
    confidence = dspy.OutputField(desc="Confidence in the connection")
    suggested_action = dspy.OutputField(desc="Suggested action based on connection")


class KnowledgeBase:
    def __init__(self):
        self.knowledge: Dict[str, KnowledgeItem] = {}
        self.references: Dict[str, DocumentReference] = {}

    def add_reference(
        self,
        page: int,
        paragraph: int,
        content: str,
        extracted_info: Dict[str, Any],
        context: str,
    ) -> str:
        ref_id = f"p{page}_par{paragraph}"
        self.references[ref_id] = DocumentReference(
            page=page,
            paragraph=paragraph,
            content=content,
            extracted_info=extracted_info,
            context=context,
        )
        return ref_id

    def add_knowledge(
        self, key: str, content: str, source_ref_id: str, confidence: float
    ) -> None:
        if key not in self.knowledge:
            self.knowledge[key] = KnowledgeItem(
                content=content,
                source_references=[self.references[source_ref_id]],
                confidence=confidence,
            )
        else:
            existing = self.knowledge[key]
            existing.source_references.append(self.references[source_ref_id])
            existing.confidence = max(existing.confidence, confidence)
            existing.last_updated = datetime.now()

    def find_related_references(
        self, content: str, threshold: float = 0.7
    ) -> List[DocumentReference]:
        # Simple similarity check - in practice, implement proper semantic similarity
        related = []
        for ref in self.references.values():
            if any(word in ref.content.lower() for word in content.lower().split()):
                related.append(ref)
        return related


class OCRagent:
    def __init__(self, api_key: str):
        self.llm = dspy.LM(
            "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", api_key=api_key
        )
        self.knowledge_base = KnowledgeBase()
        self.retriever = Retriever()
        self.thought_process = ThoughtProcess()

        # Initialize DSPy modules
        dspy.configure(lm=self.llm)
        self.query_analyzer = dspy.Predict(QueryAnalyzer)
        self.chunk_analyzer = dspy.Predict(ChunkAnalyzer)
        self.thought_generator = dspy.Predict(ThoughtGenerator)
        self.cross_reference_analyzer = dspy.Predict(CrossReferenceAnalyzer)

        self.processing_steps: List[ProcessingStep] = []
        self.current_context = ""
        self.extracted_information = {}

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analisa a pergunta do utilizador para determinar a estratégia de extração de informação."""
        analysis = self.query_analyzer(query=query)
        return {
            "query_type": analysis.query_type,
            "extraction_strategy": analysis.extraction_strategy,
            "required_fields": analysis.required_fields,
        }

    def query_law_database(self, query: str, top_k: int = 5):
            """Consulta a base de dados de leis portuguesas."""
            print("Query: ", query)
            results = self.retriever.query(
                query=query,
                topk=top_k,
                queue=None
            )

            thought = self.thought_process.add_thought(
                f"🔍 **Consultando a nossa base de dados legal**\n"
                f"- Consulta: '{query}'\n"
                f"- Encontrados {len(results)} resultados relevantes\n"
            )

            yield {
                "type": "thought_update",
                "data": {"thought": thought}
            }

            return results

    async def integrate_law_knowledge(self, query_results: List[Dict]):
        """Integra o conhecimento legal recuperado."""
        for result in query_results:
            knowledge_key = f"lei_{result['id']}"
            self.knowledge_base.add_knowledge(
                key=knowledge_key,
                content=result['text'],
                source_ref_id=result['id'],
                confidence=result['score']
            )

            thought = self.thought_process.add_thought(
                f"📚 **Integrando conhecimento legal**\n"
                f"- Fonte: {result['law_name']}\n"
                f"- Relevância: {result['score']:.2f}\n"
                f"- Tema: {result['theme']}\n"
            )

            yield {
                "type": "thought_update",
                "data": {"thought": thought}
            }


    def analyze_cross_references(self, chunk: str, query: str) -> Dict[str, Any]:
        """Analisa conexões potenciais com seções anteriores do documento."""

        try:
            analysis = self.cross_reference_analyzer(
                current_chunk=chunk,
                knowledge_base=self.knowledge_base.knowledge,
                query=query,
            )
            return {
                "related_knowledge": analysis.related_knowledge,
                "connection_type": analysis.connection_type,
                "confidence": float(analysis.confidence.strip("%")),
                "suggested_action": analysis.suggested_action,
            }

        except Exception:
            return {
                "related_knowledge": [],
                "connection_type": "No connection found",
                "confidence": 0.0,
                "suggested_action": "No action suggested",
            }

    async def process_chunk(
        self,
        chunk: str,
        query: str,
        page: int,
        paragraph: int,
        query_strategy: Dict[str, Any],
    ) -> ProcessingStep:

        actions = []
        cross_ref_analysis = self.analyze_cross_references(chunk, query)

        # Action 1: Analyze chunk
        analysis = self.chunk_analyzer(
            context=self.current_context,
            chunk=chunk,
            query=query,
            query_strategy=query_strategy["extraction_strategy"],
            required_fields=query_strategy["required_fields"],
        )
        actions.append(
            ActionResult(
                action=DecisionType(analysis.decision),
                outcome={
                    "extracted_info": analysis.extracted_info,
                    "generated_query": analysis.generated_query,
                },
                rationale=analysis.rationale,
                relevance_score=float(analysis.relevance_score),
            )
        )

        # Update knowledge base with chunk information
        ref_id = self.knowledge_base.add_reference(
            page=page,
            paragraph=paragraph,
            content=chunk,
            extracted_info=analysis.extracted_info or {},
            context=self.current_context,
        )

        # Action 2: Handle RAG queries if necessary
        if analysis.decision == DecisionType.GENERATE_QUERY and analysis.generated_query:
            results = self.query_law_database(analysis.generated_query)
            async for result in results:
                actions.append(
                    ActionResult(
                        action=DecisionType.GENERATE_QUERY,
                        outcome=result,
                        rationale="Querying RAG database for additional context.",
                    )
                )

        # Action 3: Perform cross-referencing if relevant
        if cross_ref_analysis["confidence"] > 0.7:
            related_refs = self.knowledge_base.find_related_references(chunk)
            if related_refs:
                cross_references = [ref.to_dict() for ref in related_refs]
                actions.append(
                    ActionResult(
                        action=DecisionType.CROSS_REFERENCE,
                        outcome={
                            "related_refs": cross_references,
                            "analysis": cross_ref_analysis,
                        },
                        rationale="Cross-referencing with existing knowledge base.",
                    )
                )

                # Generate new thoughts based on cross-referencing
                new_knowledge = self.thought_generator(
                    context=self.current_context,
                    query=query,
                    recent_decision={
                        "chunk": chunk,
                        "related_refs": cross_references,
                        "cross_ref_analysis": cross_ref_analysis,
                    },
                    extraction_strategy=query_strategy["extraction_strategy"],
                )

                knowledge_key = f"knowledge_{len(self.knowledge_base.knowledge)}"
                self.knowledge_base.add_knowledge(
                    key=knowledge_key,
                    content=new_knowledge.thought,
                    source_ref_id=ref_id,
                    confidence=cross_ref_analysis["confidence"],
                )

                actions.append(
                    ActionResult(
                        action=DecisionType.ELABORATE_RATIONALE,
                        outcome={"thought": new_knowledge.thought},
                        rationale="Generated rationale based on cross-references.",
                    )
                )

        # Action 4: Update context based on the decision
        if analysis.decision in [DecisionType.KEEP_CONTEXT, DecisionType.CROSS_REFERENCE]:
            self.current_context += f"\n{chunk}"
            actions.append(
                ActionResult(
                    action=DecisionType.KEEP_CONTEXT,
                    outcome={"updated_context": self.current_context},
                    rationale="Updating current context with chunk.",
                )
            )

        step = ProcessingStep(
            step_num=len(self.processing_steps) + 1,
            chunk=chunk,
            actions=actions,
            current_context=self.current_context,
            knowledge_updates=[
                action.outcome for action in actions if action.action == DecisionType.ELABORATE_RATIONALE
            ],
            cross_references=[
                ref for action in actions if action.action == DecisionType.CROSS_REFERENCE
                for ref in action.outcome.get("related_refs", [])
            ],
            generated_query=analysis.generated_query,
        )

        self.processing_steps.append(step)
        return step

    async def analyse_document(self, document_text: Dict, query: str):
        # Analyze the query to determine the strategy
        query_strategy = self.analyze_query(query)
        yield {"type": "query_analysis", "data": query_strategy}

        # Iterate through each page and paragraph in the document
        for page_num, page in document_text.get("page", {}).items():
            for para_num, paragraph in page.get("paragraph", {}).items():
                # Process each paragraph chunk
                step = await self.process_chunk(
                    chunk=paragraph,
                    query=query,
                    page=int(page_num),
                    paragraph=int(para_num),
                    query_strategy=query_strategy,
                )

                end_of_step_thought = self.thought_generator(
                    context=step.current_context,
                    query=query,
                    recent_decision=step,
                    extraction_strategy=query_strategy["extraction_strategy"],
                )

                # Prepare the step update payload with details of all actions
                step_update = {
                    "type": "step_update",
                    "data": {
                        "step_num": step.step_num,
                        "chunk": step.chunk,
                        "actions": [
                            {
                                "action": action.action.value,
                                "outcome": action.outcome,
                                "rationale": action.rationale,
                                "relevance_score": action.relevance_score,
                            }
                            for action in step.actions
                        ],
                        "current_context": step.current_context,
                        "knowledge_updates": step.knowledge_updates,
                        "cross_references": step.cross_references,
                        "generated_query": step.generated_query,
                        "summary_thought": end_of_step_thought.thought,
                    },
                }


                yield step_update

        final_thought = self.thought_generator(
            context=self.current_context,
            query=query,
            recent_decision=self.processing_steps[-1] if self.processing_steps else None,
            extraction_strategy=query_strategy["extraction_strategy"],
        )

        # Prepare the final response payload
        final_response = {
            "type": "final_response",
            "data": {
                "query": query,
                "final_answer": final_thought.thought,
                "extracted_information": self.extracted_information,
                "knowledge_base": {
                    key: {
                        "content": item.content,
                        "confidence": item.confidence,
                        "sources": [
                            f"Page {ref.page}, Paragraph {ref.paragraph}"
                            for ref in item.source_references
                        ],
                    }
                    for key, item in self.knowledge_base.knowledge.items()
                },
                "context": self.current_context,
                "steps": [
                    {
                        "step_num": step.step_num,
                        "actions": [
                            {
                                "action": action.action.value,
                                "outcome": action.outcome,
                                "rationale": action.rationale,
                                "relevance_score": action.relevance_score,
                            }
                            for action in step.actions
                        ],
                        "knowledge_updates": step.knowledge_updates,
                        "cross_references": step.cross_references,
                        "generated_query": step.generated_query,
                    }
                    for step in self.processing_steps
                ],
            },
        }

        yield final_response


async def main():
    load_dotenv()
    api_key = os.getenv("TOGETHER_API_KEY")

    agent = OCRagent(api_key=api_key)

    mock_document =""

    mock_query = ""

    async for update in agent.analyse_document(mock_document, mock_query):
        try:
            print(update)
            if update["type"] == "step_update":
                print(f"Processing step {update['data']['step_num']}...")
                print(f"Step thougth: {update["data"]["summary_thought"]}")
                # print(f"Decision: {update['data']['actions']}")
                # print(f"Rationale: {update['data']['rationale']}\n")
            elif update["type"] == "query_analysis":
                print("Query Analysis:", update["data"])
            elif update["type"] == "final_response":
                print("Final response:", update["data"]["final_answer"])
            else:
                print("Unknown update type:", update["type"])
        except KeyError as e:
            print(f"Error processing update: {e}")
            print("Update structure:", update)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
# import asyncio
# import os
# from dataclasses import dataclass
# from dataclasses import field
# from datetime import datetime
# from enum import Enum
# from typing import Any, Dict, List, Optional, Generator
# from queue import Queue
# import markdown
# import dspy
# from dotenv import load_dotenv


# class DecisionType(Enum):
#     KEEP_CONTEXT = "manter_contexto"
#     GENERATE_QUERY = "gerar_consulta"
#     SKIP_CHUNK = "ignorar_trecho"
#     ELABORATE_RATIONALE = "elaborar_fundamento"
#     EXTRACT_INFORMATION = "extrair_informacao"
#     CROSS_REFERENCE = "referencia_cruzada"


# @dataclass
# class DocumentReference:
#     page: int
#     paragraph: int
#     content: str
#     extracted_info: Dict[str, Any]
#     context: str
#     timestamp: datetime = field(default_factory=datetime.now)

#     def to_dict(self) -> dict:
#         """Converte a referência do documento em um dicionário."""
#         return {
#             "page": self.page,
#             "paragraph": self.paragraph,
#             "content": self.content,
#             "extracted_info": self.extracted_info,
#             "context": self.context,
#             "timestamp": self.timestamp.isoformat(),
#         }


# @dataclass
# class KnowledgeItem:
#     content: str
#     source_references: List[DocumentReference]
#     confidence: float
#     last_updated: datetime = field(default_factory=datetime.now)
#     related_items: List[str] = field(default_factory=list)


# @dataclass
# class ProcessingStep:
#     step_num: int
#     chunk: str
#     current_context: str
#     decision: DecisionType
#     rationale: str
#     knowledge_updates: List[Dict[str, Any]]
#     cross_references: List[DocumentReference] = field(default_factory=list)
#     generated_query: Optional[str] = None
#     rag_response: Optional[List[Dict]] = None
#     extracted_info: Optional[Dict[str, Any]] = None
#     relevance_score: float = 0.0


# class QueryAnalyzer(dspy.Signature):
#     """Analisa a consulta do usuário para determinar a estratégia de extração."""

#     query = dspy.InputField(desc="Consulta do usuário sobre o documento")
#     query_type = dspy.OutputField(desc="Tipo de consulta (análise_geral, info_específica, etc.)")
#     extraction_strategy = dspy.OutputField(desc="Estratégia para extrair informações relevantes")
#     required_fields = dspy.OutputField(desc="Lista de campos específicos para extrair")


# class ChunkAnalyzer(dspy.Signature):
#     """Analisa trechos de texto no contexto da consulta."""

#     context = dspy.InputField(desc="Contexto acumulado atual")
#     chunk = dspy.InputField(desc="Novo trecho de texto para análise")
#     query = dspy.InputField(desc="Consulta do usuário sobre o documento")
#     query_strategy = dspy.InputField(desc="Estratégia de extração do QueryAnalyzer")
#     required_fields = dspy.InputField(desc="Campos necessários para extrair")

#     decision = dspy.OutputField(desc="Tipo de Decisão")
#     rationale = dspy.OutputField(desc="Fundamentação da decisão")
#     generated_query = dspy.OutputField(desc="Consulta para RAG se aplicável")
#     extracted_info = dspy.OutputField(desc="Informações extraídas relevantes para a consulta")
#     relevance_score = dspy.OutputField(desc="Pontuação de relevância do trecho para a consulta (0-1)")


# class ThoughtGenerator(dspy.Signature):
#     """Gera pensamentos intermediários e raciocínio."""

#     context = dspy.InputField(desc="Contexto atual")
#     query = dspy.InputField(desc="Consulta original do usuário")
#     recent_decision = dspy.InputField(desc="Detalhes do último passo de processamento")
#     extraction_strategy = dspy.InputField(desc="Estratégia de extração atual")

#     thought = dspy.OutputField(desc="Pensamento ou análise gerada")
#     updated_context = dspy.OutputField(desc="Novo contexto incorporando o pensamento")
#     query_progress = dspy.OutputField(desc="Progresso em direção à resposta da consulta")


# class CrossReferenceAnalyzer(dspy.Signature):
#     """Analisa possíveis conexões com seções anteriores do documento."""

#     current_chunk = dspy.InputField(desc="Trecho atual de texto")
#     knowledge_base = dspy.InputField(desc="Base de conhecimento existente")
#     query = dspy.InputField(desc="Consulta do usuário")

#     related_knowledge = dspy.OutputField(desc="Conhecimento anterior relacionado")
#     connection_type = dspy.OutputField(desc="Tipo de conexão encontrada")
#     confidence = dspy.OutputField(desc="Confiança na conexão")
#     suggested_action = dspy.OutputField(desc="Ação sugerida com base na conexão")


# class ThoughtProcess:
#     def __init__(self):
#         self.thoughts: List[str] = []

#     def add_thought(self, thought: str) -> str:
#         """Adiciona um pensamento formatado em markdown."""
#         formatted_thought = f"### Pensamento {len(self.thoughts) + 1}\n{thought}\n"
#         self.thoughts.append(formatted_thought)
#         return formatted_thought

#     def get_formatted_thoughts(self) -> str:
#         """Retorna todos os pensamentos formatados."""
#         return "\n".join(self.thoughts)


# class KnowledgeBase:
#     def __init__(self):
#         self.knowledge: Dict[str, KnowledgeItem] = {}
#         self.references: Dict[str, DocumentReference] = {}

#     def add_reference(
#         self,
#         page: int,
#         paragraph: int,
#         content: str,
#         extracted_info: Dict[str, Any],
#         context: str,
#     ) -> str:
#         ref_id = f"p{page}_par{paragraph}"
#         self.references[ref_id] = DocumentReference(
#             page=page,
#             paragraph=paragraph,
#             content=content,
#             extracted_info=extracted_info,
#             context=context,
#         )
#         return ref_id

#     def add_knowledge(
#         self, key: str, content: str, source_ref_id: str, confidence: float
#     ) -> None:
#         if key not in self.knowledge:
#             self.knowledge[key] = KnowledgeItem(
#                 content=content,
#                 source_references=[self.references[source_ref_id]],
#                 confidence=confidence,
#             )
#         else:
#             existing = self.knowledge[key]
#             existing.source_references.append(self.references[source_ref_id])
#             existing.confidence = max(existing.confidence, confidence)
#             existing.last_updated = datetime.now()

#     def find_related_references(
#         self, content: str, threshold: float = 0.7
#     ) -> List[DocumentReference]:
#         related = []
#         for ref in self.references.values():
#             if any(word in ref.content.lower() for word in content.lower().split()):
#                 related.append(ref)
#         return related


# class OCRagent:
#     def __init__(self, api_key: str):
#         self.llm = dspy.LM(
#             "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
#             api_key=api_key
#         )
#         self.knowledge_base = KnowledgeBase()
#         self.retriever = Retriever()
#         self.thought_process = ThoughtProcess()

#         dspy.configure(lm=self.llm)
#         self.query_analyzer = dspy.Predict(QueryAnalyzer)
#         self.chunk_analyzer = dspy.Predict(ChunkAnalyzer)
#         self.thought_generator = dspy.Predict(ThoughtGenerator)
#         self.cross_reference_analyzer = dspy.Predict(CrossReferenceAnalyzer)

#         self.processing_steps: List[ProcessingStep] = []
#         self.current_context = ""
#         self.extracted_information = {}

#     async def query_law_database(self, query: str, top_k: int = 5) -> List[Dict]:
#         """Consulta a base de dados de leis portuguesas."""
#         results = self.retriever.query(
#             query=query,
#             topk=top_k,
#             queue=None
#         )

#         thought = self.thought_process.add_thought(
#             f"🔍 **Consultando base de dados legal**\n"
#             f"- Consulta: '{query}'\n"
#             f"- Encontrados {len(results)} resultados relevantes\n"
#         )

#         yield {
#             "type": "thought_update",
#             "data": {"thought": thought}
#         }

#         return results

#     async def integrate_law_knowledge(self, query_results: List[Dict]) -> None:
#         """Integra o conhecimento legal recuperado."""
#         for result in query_results:
#             knowledge_key = f"lei_{result['id']}"
#             self.knowledge_base.add_knowledge(
#                 key=knowledge_key,
#                 content=result['text'],
#                 source_ref_id=result['id'],
#                 confidence=result['score']
#             )

#             thought = self.thought_process.add_thought(
#                 f"📚 **Integrando conhecimento legal**\n"
#                 f"- Fonte: {result['law_name']}\n"
#                 f"- Relevância: {result['score']:.2f}\n"
#                 f"- Tema: {result['theme']}\n"
#             )

#             yield {
#                 "type": "thought_update",
#                 "data": {"thought": thought}
#             }

#     async def analyze_cross_references(self, chunk: str, query: str) -> Dict[str, Any]:
#         """Analisa conexões com conhecimento anterior."""
#         try:
#             analysis = self.cross_reference_analyzer(
#                 current_chunk=chunk,
#                 knowledge_base=self.knowledge_base.knowledge,
#                 query=query,
#             )
#             return {
#                 "related_knowledge": analysis.related_knowledge,
#                 "connection_type": analysis.connection_type,
#                 "confidence": float(analysis.confidence.strip("%")),
#                 "suggested_action": analysis.suggested_action,
#             }
#         except Exception:
#             return {
#                 "related_knowledge": [],
#                 "connection_type": "Nenhuma conexão encontrada",
#                 "confidence": 0.0,
#                 "suggested_action": "Nenhuma ação sugerida",
#             }

#     async def process_chunk(
#         self,
#         chunk: str,
#         query: str,
#         page: int,
#         paragraph: int,
#         query_strategy: Dict[str, Any],
#     ) -> ProcessingStep:
#         """Processa um trecho do documento com suporte a consultas RAG."""
#         cross_ref_analysis = await self.analyze_cross_references(chunk, query)

#         analysis = self.chunk_analyzer(
#             context=self.current_context,
#             chunk=chunk,
#             query=query,
#             query_strategy=query_strategy["extraction_strategy"],
#             required_fields=query_strategy["required_fields"],
#         )

#         if analysis.decision == DecisionType.GENERATE_QUERY:
#             thought = self.thought_process.add_thought(
#                 f"🤔 **Necessidade de consulta identificada**\n"
#                 f"- Contexto atual: '{chunk[:100]}...'\n"
#                 f"- Motivo: {analysis.rationale}\n"
#             )

#             yield {
#                 "type": "thought_update",
#                 "data": {"thought": thought}
#             }

#             law_results = await self.query_law_database(analysis.generated_query)
#             async for update in self.integrate_law_knowledge(law_results):
#                 yield update
#         else:
#             law_results = None

#         ref_id = self.knowledge_base.add_reference(
#             page=page,
#             paragraph=paragraph,
#             content=chunk,
#             extracted_info=analysis.extracted_info or {},
#             context=self.current_context,
#         )

#         knowledge_updates = []
#         cross_references = []
#         if cross_ref_analysis["confidence"] > 0.7:
#             related_refs = self.knowledge_base.find_related_references(chunk)
#             cross_references.extend(related_refs)

#             if related_refs:
#                 new_knowledge = self.thought_generator(
#                     context=self.current_context,
#                     query=query,
#                     recent_decision={
#                         "chunk": chunk,
#                         "related_refs": [ref.to_dict() for ref in related_refs],
#                         "cross_ref_analysis": cross_ref_analysis,
#                     },
#                     extraction_strategy=query_strategy["extraction_strategy"],
#                 )

#                 knowledge_key = f"conhecimento_{len(self.knowledge_base.knowledge)}"
#                 self.knowledge_base.add_knowledge(
#                     key=knowledge_key,
#                     content=new_knowledge.thought,
#                     source_ref_id=ref_id,
#                     confidence=cross_ref_analysis["confidence"],
#                 )

#                 knowledge_updates.append({
#                     "key": knowledge_key,
#                     "content": new_knowledge.thought,
#                     "confidence": cross_ref_analysis["confidence"],
#                 })

#         step = ProcessingStep(
#             step_num=len(self.processing_steps) + 1,
#             chunk=chunk,
#             current_context=self.current_context,
#             decision=DecisionType(analysis.decision),
#             rationale=analysis.rationale,
#             knowledge_updates=knowledge_updates,
#             cross_references=cross_references,
#             generated_query=analysis.generated_query if analysis.decision == DecisionType.GENERATE_QUERY else None,
#             rag_response=law_results,
#             extracted_info=analysis.extracted_info,
#             relevance_score=float(analysis.relevance_score),
#         )

#         if step.decision in [DecisionType.KEEP_CONTEXT, DecisionType.CROSS_REFERENCE]:
#             self.current_context += f"\n{chunk}"

#         thought = self.thought_process.add_thought(
#             f"✍️ **Análise de trecho**\n"
#             f"- Decisão: {step.decision.value}\n"
#             f"- Fundamentação: {step.rationale}\n"
#             f"- Relevância: {step.relevance_score:.2f}\n"
#             + (f"- Consulta gerada: {step.generated_query}\n" if step.generated_query else "")
#         )

#         yield {
#             "type": "step_update",
#             "data": {
#                 "step_num": step.step_num,
#                 "chunk": step.chunk,
#                 "decision": step.decision.value,
#                 "rationale": step.rationale,
#                 "knowledge_updates": step.knowledge_updates,
#                 "cross_references": [
#                     {
#                         "page": ref.page,
#                         "paragraph": ref.paragraph,
#                         "content": ref.content,
#                     }
#                     for ref in step.cross_references
#                 ],
#                 "extracted_info": step.extracted_info,
#                 "relevance_score": step.relevance_score,
#                 "current_context": self.current_context,
#                 "thought": thought
#             }
#         }

#         self.processing_steps.append(step)
#         return step
