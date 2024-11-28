# import asyncio
# import os
import re
from typing import Optional

from ocr.ExtractFromImage.main import ImageProcessor
from ocr.ExtractFromPDF.main import PDFProcessor
from rag.retriever.main import Retriever

# from dataclasses import dataclass
# from dataclasses import field
# from datetime import datetime
# from enum import Enum
# from typing import Any
# from typing import Dict
# from typing import List
# import dspy
# from dotenv import load_dotenv

# @dataclass
# class DocumentReference:
#     page: int
#     paragraph: int
#     content: str
#     extracted_info: Dict[str, Any]
#     context: str
#     timestamp: datetime = field(default_factory=datetime.now)
#     def to_dict(self) -> dict:
#         return {
#             "page": self.page,
#             "paragraph": self.paragraph,
#             "content": self.content,
#             "extracted_info": self.extracted_info,
#             "context": self.context,
#             "timestamp": self.timestamp.isoformat(),
#         }
# @dataclass
# class ActionResult:
#     action: DecisionType
#     outcome: Optional[Dict[str, Any]] = None
#     rationale: str = ""
#     relevance_score: float = 0.0
# @dataclass
# class KnowledgeItem:
#     content: str
#     source_references: List[DocumentReference]
#     confidence: float
#     last_updated: datetime = field(default_factory=datetime.now)
#     related_items: List[str] = field(default_factory=list)
# # @dataclass
# # class ProcessingStep:
# #     step_num: int
# #     chunk: str
# #     current_context: str
# #     decision: DecisionType
# #     rationale: str
# #     knowledge_updates: List[Dict[str, Any]]
# #     cross_references: List[DocumentReference] = field(default_factory=list)
# #     generated_query: Optional[str] = None
# #     rag_response: Optional[str] = None
# #     extracted_info: Optional[Dict[str, Any]] = None
# #     relevance_score: float = 0.0
# @dataclass
# class ProcessingStep:
#     step_num: int
#     chunk: str
#     actions: List[ActionResult]
#     current_context: str
#     knowledge_updates: List[Dict[str, Any]]
#     cross_references: List[DocumentReference] = field(default_factory=list)
#     generated_query: Optional[str] = None
# class ProblemIdentification(dspy.Signature):
#     "Começa por compreender o documento na integra, e qual é o seu objetivo. Decompõe o documento em argumentos centrais."
#     document = dspy.InputField(desc="Documento a analisar")
#     objetivo = dspy.OutputField(desc="Objetivo do documento")
#     core_arguments = dspy.OutputField(desc="Argumentos centrais presentes no documento")
# class IdentifyKnowledgeGaps(dspy.Signature):
#     """
#     Com base na tua leitura inicial do documento e da questão do utilizador, parte extrai um conjunto de ações e possíveis questões a realizar de forma a compreender o excerto ou responder à questão do utilizador.
#     Gera um conjunto de questões a realizar para preencher as lacunas de conhecimento.
#     """
#     chunk = dspy.InputField(desc="Pedaço de documento a analisar")
#     query = dspy.InputField(desc="Questão do utilizador")
#     acoes: List[DecisionType] = dspy.OutputField(desc="Objetivo do documento")
# class Research(dspy.Signature):
#     "Com base na questão do utilizador e no excerto do documento, parte o mesmo num grupo de questões legais de forma a pesquisares numa biblioteca legal as mesmas."
#     chunk = dspy.InputField(desc="Pedaço de documento a analisar")
#     query = dspy.InputField(desc="Questão do utilizador")
#     queries: List[str] = dspy.OutputField(desc="Lista de questões a colocar")
# class QueryAnalyzer(dspy.Signature):
#     """Analisa a questão do utilizador para determinar a estratégia de extração."""
#     query = dspy.InputField(desc="User's query about the document")
#     query_type = dspy.OutputField(
#         desc="Type of query (general_analysis, specific_info, etc.)"
#     )
#     extraction_strategy = dspy.OutputField(
#         desc="Strategy for extracting relevant information"
#     )
#     required_fields = dspy.OutputField(desc="List of specific fields to extract")
# class ChunkAnalyzer(dspy.Signature):
#     """Analisa excertos de texto com base na questão do utilizador. Com isto deves decidir que ação tomar, esta pode ser, elaborar uma questão, guardar a informação como contexto, gerar um pensamento intermédio e seguir para o excerto seguinte"""
#     context = dspy.InputField(desc="Current accumulated context")
#     chunk = dspy.InputField(desc="New text chunk to analyze")
#     query = dspy.InputField(desc="User's query about the document")
#     query_strategy = dspy.InputField(desc="Extraction strategy from QueryAnalyzer")
#     required_fields = dspy.InputField(desc="Required fields to extract")
#     decision: DecisionType = dspy.OutputField(desc="Decision Type")
#     rationale = dspy.OutputField(desc="Reasoning behind the decision")
#     generated_query = dspy.OutputField(desc="Query for RAG if applicable")
#     extracted_info = dspy.OutputField(desc="Extracted information relevant to query")
#     relevance_score = dspy.OutputField(desc="Relevance score of chunk to query (0-1)")
# class ThoughtGenerator(dspy.Signature):
#     """Gera raciocínio e elações intermédias relativamente à questão do utilizador com base em todo o contexto que tens."""
#     context = dspy.InputField(desc="Current context")
#     query = dspy.InputField(desc="Original user query")
#     recent_decision = dspy.InputField(desc="Last processing step details")
#     extraction_strategy = dspy.InputField(desc="Current extraction strategy")
#     thought = dspy.OutputField(desc="Generated thought or analysis")
#     updated_context = dspy.OutputField(desc="New context incorporating the thought")
#     query_progress: Optional[str] = dspy.OutputField(
#         desc="Progress towards answering the query"
#     )
# class ThoughtProcess:
#     def __init__(self):
#         self.thoughts: List[str] = []
#     def add_thought(self, thought: str) -> str:
#         formatted_thought = f"### Pensamento {len(self.thoughts) + 1}\n{thought}\n"
#         self.thoughts.append(formatted_thought)
#         return formatted_thought
#     def get_formatted_thoughts(self) -> str:
#         return "\n".join(self.thoughts)
# class CrossReferenceAnalyzer(dspy.Signature):
#     """Analisa potenciais conexões com seções anteriores do documento ou raciocínios."""
#     current_chunk = dspy.InputField(desc="Current text chunk")
#     knowledge_base = dspy.InputField(desc="Existing knowledge base")
#     query = dspy.InputField(desc="User's query")
#     related_knowledge = dspy.OutputField(desc="Related previous knowledge")
#     connection_type = dspy.OutputField(desc="Type of connection found")
#     confidence = dspy.OutputField(desc="Confidence in the connection")
#     suggested_action = dspy.OutputField(desc="Suggested action based on connection")
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
#         # Simple similarity check - in practice, implement proper semantic similarity
#         related = []
#         for ref in self.references.values():
#             if any(word in ref.content.lower() for word in content.lower().split()):
#                 related.append(ref)
#         return related
# class OCRagent:
#     def __init__(self, api_key: str):
#         self.llm = dspy.LM(
#             "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", api_key=api_key
#         )
#         self.knowledge_base = KnowledgeBase()
#         self.retriever = Retriever()
#         self.thought_process = ThoughtProcess()
#         # Initialize DSPy modules
#         dspy.configure(lm=self.llm)
#         self.query_analyzer = dspy.Predict(QueryAnalyzer)
#         self.chunk_analyzer = dspy.Predict(ChunkAnalyzer)
#         self.thought_generator = dspy.Predict(ThoughtGenerator)
#         self.cross_reference_analyzer = dspy.Predict(CrossReferenceAnalyzer)
#         self.processing_steps: List[ProcessingStep] = []
#         self.current_context = ""
#         self.extracted_information = {}
#     def analyze_query(self, query: str) -> Dict[str, Any]:
#         """Analisa a pergunta do utilizador para determinar a estratégia de extração de informação."""
#         analysis = self.query_analyzer(query=query)
#         return {
#             "query_type": analysis.query_type,
#             "extraction_strategy": analysis.extraction_strategy,
#             "required_fields": analysis.required_fields,
#         }
#     def query_law_database(self, query: str, top_k: int = 5):
#         """Consulta a base de dados de leis portuguesas."""
#         print("Query: ", query)
#         results = self.retriever.query(query=query, topk=top_k, queue=None)
#         thought = self.thought_process.add_thought(
#             f"🔍 **Consultando a nossa base de dados legal**\n"
#             f"- Consulta: '{query}'\n"
#             f"- Encontrados {len(results)} resultados relevantes\n"
#         )
#         yield {"type": "thought_update", "data": {"thought": thought}}
#         return results
#     async def integrate_law_knowledge(self, query_results: List[Dict]):
#         """Integra o conhecimento legal recuperado."""
#         for result in query_results:
#             knowledge_key = f"lei_{result['id']}"
#             self.knowledge_base.add_knowledge(
#                 key=knowledge_key,
#                 content=result["text"],
#                 source_ref_id=result["id"],
#                 confidence=result["score"],
#             )
#             thought = self.thought_process.add_thought(
#                 f"📚 **Integrando conhecimento legal**\n"
#                 f"- Fonte: {result['law_name']}\n"
#                 f"- Relevância: {result['score']:.2f}\n"
#                 f"- Tema: {result['theme']}\n"
#             )
#             yield {"type": "thought_update", "data": {"thought": thought}}
#     def analyze_cross_references(self, chunk: str, query: str) -> Dict[str, Any]:
#         """Analisa conexões potenciais com seções anteriores do documento."""
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
#                 "connection_type": "No connection found",
#                 "confidence": 0.0,
#                 "suggested_action": "No action suggested",
#             }
#     async def process_chunk(
#         self,
#         chunk: str,
#         query: str,
#         page: int,
#         paragraph: int,
#         query_strategy: Dict[str, Any],
#     ) -> ProcessingStep:
#         actions = []
#         cross_ref_analysis = self.analyze_cross_references(chunk, query)
#         # Action 1: Analyze chunk
#         analysis = self.chunk_analyzer(
#             context=self.current_context,
#             chunk=chunk,
#             query=query,
#             query_strategy=query_strategy["extraction_strategy"],
#             required_fields=query_strategy["required_fields"],
#         )
#         actions.append(
#             ActionResult(
#                 action=DecisionType(analysis.decision),
#                 outcome={
#                     "extracted_info": analysis.extracted_info,
#                     "generated_query": analysis.generated_query,
#                 },
#                 rationale=analysis.rationale,
#                 relevance_score=float(analysis.relevance_score),
#             )
#         )
#         # Update knowledge base with chunk information
#         ref_id = self.knowledge_base.add_reference(
#             page=page,
#             paragraph=paragraph,
#             content=chunk,
#             extracted_info=analysis.extracted_info or {},
#             context=self.current_context,
#         )
#         # Action 2: Handle RAG queries if necessary
#         if (
#             analysis.decision == DecisionType.GENERATE_QUERY
#             and analysis.generated_query
#         ):
#             results = self.query_law_database(analysis.generated_query)
#             async for result in results:
#                 actions.append(
#                     ActionResult(
#                         action=DecisionType.GENERATE_QUERY,
#                         outcome=result,
#                         rationale="Querying RAG database for additional context.",
#                     )
#                 )
#         # Action 3: Perform cross-referencing if relevant
#         if cross_ref_analysis["confidence"] > 0.7:
#             related_refs = self.knowledge_base.find_related_references(chunk)
#             if related_refs:
#                 cross_references = [ref.to_dict() for ref in related_refs]
#                 actions.append(
#                     ActionResult(
#                         action=DecisionType.CROSS_REFERENCE,
#                         outcome={
#                             "related_refs": cross_references,
#                             "analysis": cross_ref_analysis,
#                         },
#                         rationale="Cross-referencing with existing knowledge base.",
#                     )
#                 )
#                 # Generate new thoughts based on cross-referencing
#                 new_knowledge = self.thought_generator(
#                     context=self.current_context,
#                     query=query,
#                     recent_decision={
#                         "chunk": chunk,
#                         "related_refs": cross_references,
#                         "cross_ref_analysis": cross_ref_analysis,
#                     },
#                     extraction_strategy=query_strategy["extraction_strategy"],
#                 )
#                 knowledge_key = f"knowledge_{len(self.knowledge_base.knowledge)}"
#                 self.knowledge_base.add_knowledge(
#                     key=knowledge_key,
#                     content=new_knowledge.thought,
#                     source_ref_id=ref_id,
#                     confidence=cross_ref_analysis["confidence"],
#                 )
#                 actions.append(
#                     ActionResult(
#                         action=DecisionType.ELABORATE_RATIONALE,
#                         outcome={"thought": new_knowledge.thought},
#                         rationale="Generated rationale based on cross-references.",
#                     )
#                 )
#         # Action 4: Update context based on the decision
#         if analysis.decision in [
#             DecisionType.KEEP_CONTEXT,
#             DecisionType.CROSS_REFERENCE,
#         ]:
#             self.current_context += f"\n{chunk}"
#             actions.append(
#                 ActionResult(
#                     action=DecisionType.KEEP_CONTEXT,
#                     outcome={"updated_context": self.current_context},
#                     rationale="Updating current context with chunk.",
#                 )
#             )
#         step = ProcessingStep(
#             step_num=len(self.processing_steps) + 1,
#             chunk=chunk,
#             actions=actions,
#             current_context=self.current_context,
#             knowledge_updates=[
#                 action.outcome
#                 for action in actions
#                 if action.action == DecisionType.ELABORATE_RATIONALE
#             ],
#             cross_references=[
#                 ref
#                 for action in actions
#                 if action.action == DecisionType.CROSS_REFERENCE
#                 for ref in action.outcome.get("related_refs", [])
#             ],
#             generated_query=analysis.generated_query,
#         )
#         self.processing_steps.append(step)
#         return step
#     async def analyse_document(self, document_text: Dict, query: str):
#         # Analyze the query to determine the strategy
#         query_strategy = self.analyze_query(query)
#         yield {"type": "query_analysis", "data": query_strategy}
#         # Iterate through each page and paragraph in the document
#         for page_num, page in document_text.get("page", {}).items():
#             for para_num, paragraph in page.get("paragraph", {}).items():
#                 # Process each paragraph chunk
#                 step = await self.process_chunk(
#                     chunk=paragraph,
#                     query=query,
#                     page=int(page_num),
#                     paragraph=int(para_num),
#                     query_strategy=query_strategy,
#                 )
#                 end_of_step_thought = self.thought_generator(
#                     context=step.current_context,
#                     query=query,
#                     recent_decision=step,
#                     extraction_strategy=query_strategy["extraction_strategy"],
#                 )
#                 # Prepare the step update payload with details of all actions
#                 step_update = {
#                     "type": "step_update",
#                     "data": {
#                         "step_num": step.step_num,
#                         "chunk": step.chunk,
#                         "actions": [
#                             {
#                                 "action": action.action.value,
#                                 "outcome": action.outcome,
#                                 "rationale": action.rationale,
#                                 "relevance_score": action.relevance_score,
#                             }
#                             for action in step.actions
#                         ],
#                         "current_context": step.current_context,
#                         "knowledge_updates": step.knowledge_updates,
#                         "cross_references": step.cross_references,
#                         "generated_query": step.generated_query,
#                         "summary_thought": end_of_step_thought.thought,
#                     },
#                 }
#                 yield step_update
#         final_thought = self.thought_generator(
#             context=self.current_context,
#             query=query,
#             recent_decision=self.processing_steps[-1]
#             if self.processing_steps
#             else None,
#             extraction_strategy=query_strategy["extraction_strategy"],
#         )
#         # Prepare the final response payload
#         final_response = {
#             "type": "final_response",
#             "data": {
#                 "query": query,
#                 "final_answer": final_thought.thought,
#                 "extracted_information": self.extracted_information,
#                 "knowledge_base": {
#                     key: {
#                         "content": item.content,
#                         "confidence": item.confidence,
#                         "sources": [
#                             f"Page {ref.page}, Paragraph {ref.paragraph}"
#                             for ref in item.source_references
#                         ],
#                     }
#                     for key, item in self.knowledge_base.knowledge.items()
#                 },
#                 "context": self.current_context,
#                 "steps": [
#                     {
#                         "step_num": step.step_num,
#                         "actions": [
#                             {
#                                 "action": action.action.value,
#                                 "outcome": action.outcome,
#                                 "rationale": action.rationale,
#                                 "relevance_score": action.relevance_score,
#                             }
#                             for action in step.actions
#                         ],
#                         "knowledge_updates": step.knowledge_updates,
#                         "cross_references": step.cross_references,
#                         "generated_query": step.generated_query,
#                     }
#                     for step in self.processing_steps
#                 ],
#             },
#         }
#         yield final_response
class OCR:
    def __init__(self):
        # self.agent = OCRagent(api_key=os.getenv("TOGETHER_API_KEY"))
        pass

    def __convert_to_text(self, base64_encoded_document: str) -> dict:
        png_regex = r"data:image/png;base64"
        pdf_regex = r"data:application/pdf;base64"
        try:
            if re.match(png_regex, base64_encoded_document):
                image_processor = ImageProcessor()
                return image_processor.extract_from_image(base64_encoded_document)
            elif re.match(pdf_regex, base64_encoded_document):
                pdf_processor = PDFProcessor()
                return pdf_processor.extract_from_pdf(base64_encoded_document)
            else:
                raise ValueError("Invalid document format.")
        except Exception as e:
            print(f"Error converting base64 to text: {e}")
            return {}

    def process_document(
        self,
        base64_encoded_document: str,
        query: Optional[str] = "Analisa o seguinte documento",
    ):
        document_text = self.__convert_to_text(base64_encoded_document)
        print(document_text)
        # return self.agent.analyse_document(document_text, query)


# test_pdf = "data:application/pdf;base64,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bnREZXNjcmlwdG9yL0ZvbnROYW1lL0JDREVFRStBcHRvcy9GbGFncyAzMi9JdGFsaWNBbmdsZSAwL0FzY2VudCA5MzkvRGVzY2VudCAtMjgyL0NhcEhlaWdodCA5MzkvQXZnV2lkdGggNTYxL01heFdpZHRoIDE2ODIvRm9udFdlaWdodCA0MDAvWEhlaWdodCAyNTAvU3RlbVYgNTYvRm9udEJCb3hbIC01MDAgLTI4MiAxMTgyIDkzOV0gL0ZvbnRGaWxlMiA2NCAwIFI+Pg0KZW5kb2JqDQoxMCAwIG9iag0KPDwvVHlwZS9FeHRHU3RhdGUvQk0vTm9ybWFsL2NhIDE+Pg0KZW5kb2JqDQoxMSAwIG9iag0KPDwvVHlwZS9FeHRHU3RhdGUvQk0vTm9ybWFsL0NBIDE+Pg0KZW5kb2JqDQoxMiAwIG9iag0KPDwvVHlwZS9Gb250L1N1YnR5cGUvVHJ1ZVR5cGUvTmFtZS9GMi9CYXNlRm9udC9CQ0RGRUUrQXB0b3MvRW5jb2RpbmcvV2luQW5zaUVuY29kaW5nL0ZvbnREZXNjcmlwdG9yIDEzIDAgUi9GaXJzdENoYXIgMzIvTGFzdENoYXIgMzIvV2lkdGhzIDY2IDAgUj4+DQplbmRvYmoNCjEzIDAgb2JqDQo8PC9UeXBlL0ZvbnREZXNjcmlwdG9yL0ZvbnROYW1lL0JDREZFRStBcHRvcy9GbGFncyAzMi9JdGFsaWNBbmdsZSAwL0FzY2VudCA5MzkvRGVzY2VudCAtMjgyL0NhcEhlaWdodCA5MzkvQXZnV2lkdGggNTYxL01heFdpZHRoIDE2ODIvRm9udFdlaWdodCA0MDAvWEhlaWdodCAyNTAvU3RlbVYgNTYvRm9udEJCb3hbIC01MDAgLTI4MiAxMTgyIDkzOV0gL0ZvbnRGaWxlMiA2NCAwIFI+Pg0KZW5kb2JqDQoxNCAwIG9iag0KPDwvQXV0aG9yKP7/AEcAbwBuAOcAYQBsAG8AIABMAG8AYgBvACAARgByAGUAaQB0AGEAcykgL0NyZWF0b3IoTWljcm9zb2Z0IFdvcmQpIC9DcmVhdGlvbkRhdGUoRDoyMDI0MTEyMDIzMTgwMyswMCcwMCcpIC9Nb2REYXRlKEQ6MjAyNDExMjAyMzE4MDMrMDAnMDAnKSA+Pg0KZW5k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93P3S9XlfgcZ97IPumfcr/4HIYOv1w0KZW5kc3RyZWFtDQplbmRvYmoNCjY1IDAgb2JqDQpbIDBbIDQ3MV0gIDFbIDU4OV0gIDQwWyA1NTZdICA3MFsgNzA3XSAgOTdbIDc5MCA3MDZdICAxMDVbIDczMl0gIDEzMlsgNTc3XSAgMTM0WyA3MzJdICAxMzlbIDU2Nl0gIDE3MVsgNTg1XSAgMjA1WyA1MzEgNTMxXSAgMjI3WyA1MzFdICAyMzBbIDU2MV0gIDIzMlsgNTI1XSAgMjM1WyA1MjVdICAyMzhbIDU2MV0gIDI0NFsgNTI3IDUyN10gIDI2N1sgMzAxIDQ4NF0gIDI3NVsgNTUxXSAgMjc4WyAyMzldICAyOTJbIDIzOV0gIDI5OVsgMjYwXSAgMzA1WyA4NTMgNTUxXSAgMzE0WyA1NTIgNTUyXSAgMzM5WyA1NTJdICAzNDFbIDU2MV0gIDM0M1sgNTYxIDMzNF0gIDM0OFsgNDg2XSAgMzU3WyAzMjNdICAzNjJbIDU1OSA1NTldICAzODFbIDQ1Ml0gIDM4OFsgNDQyXSAgMzk5WyA0MzhdICA0MzNbIDU0MF0gIDk4NVsgMjAzXSAgOTkxWyAyODYgMjg2IDI4NiAyODZdICA5OThbIDUwMV0gIDEwMzRbIDQ1MiA0NTNdICAxMDQzWyAzNzBdIF0gDQplbmRvYmoNCjY2IDAgb2JqDQpbIDIwM10gDQplbmRvYmoNCjY3IDAgb2JqDQo8PC9UeXBlL01ldGFkYXRhL1N1YnR5cGUvWE1ML0xlbmd0aCAzMDE0Pj4NCnN0cmVhbQ0KPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz48eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSIzLjEtNzAxIj4KPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgIHhtbG5zOnBkZj0iaHR0cDovL25zLmFkb2JlLmNvbS9wZGYvMS4zLyI+CjwvcmRmOkRlc2NyaXB0aW9uPgo8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIj4KPGRjOmNyZWF0b3I+PHJkZjpTZXE+PHJkZjpsaT5Hb27Dp2FsbyBMb2JvIEZyZWl0YXM8L3JkZjpsaT48L3JkZjpTZXE+PC9kYzpjcmVhdG9yPjwvcmRmOkRlc2NyaXB0aW9uPgo8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiAgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIj4KPHhtcDpDcmVhdG9yVG9vbD5NaWNyb3NvZnQgV29yZDwveG1wOkNyZWF0b3JUb29sPjx4bXA6Q3JlYXRlRGF0ZT4yMDI0LTExLTIwVDIzOjE4OjAzKzAwOjAwPC94bXA6Q3JlYXRlRGF0ZT48eG1wOk1vZGlmeURhdGU+MjAyNC0xMS0yMFQyMzoxODowMyswMDowMDwveG1wOk1vZGlmeURhdGU+PC9yZGY6RGVzY3JpcHRpb24+CjxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyI+Cjx4bXBNTTpEb2N1bWVudElEPnV1aWQ6NjE2RUUzMzgtQ0U3Ri00NzI0LTk4RkQtQTU0NUYxNEYzMjE0PC94bXBNTTpEb2N1bWVudElEPjx4bXBNTTpJbnN0YW5jZUlEPnV1aWQ6NjE2RUUzMzgtQ0U3Ri00NzI0LTk4RkQtQTU0NUYxNEYzMjE0PC94bXBNTTpJbnN0YW5jZUlEPjwvcmRmOkRlc2NyaXB0aW9uPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKPC9yZGY6UkRGPjwveDp4bXBtZXRhPjw/eHBhY2tldCBlbmQ9InciPz4NCmVuZHN0cmVhbQ0KZW5kb2JqDQo2OCAwIG9iag0KPDwvRGlzcGxheURvY1RpdGxlIHRydWU+Pg0KZW5kb2JqDQo2OSAwIG9iag0KPDwvVHlwZS9YUmVmL1NpemUgNjkvV1sgMSA0IDJdIC9Sb290IDEgMCBSL0luZm8gMTQgMCBSL0lEWzwzOEUzNkU2MTdGQ0UyNDQ3OThGREE1NDVGMTRGMzIxND48MzhFMzZFNjE3RkNFMjQ0Nzk4RkRBNTQ1RjE0RjMyMTQ+XSAvRmlsdGVyL0ZsYXRlRGVjb2RlL0xlbmd0aCAxNzU+Pg0Kc3RyZWFtDQp4nDXQtxHCUAyAYZmcjG2SMTlnMwQHA9CwDTUzULMC29BTQMsdFQcP/aBC30k6qZCIiffbMtkT+XKCi2I9lNweXoodwBlo5m+K04EdMHPvIhFz05cZzGEBIUwhA7+FpVn3jv/KgghEIQZxSEASUpAGD7KQAxvy4IALNShAEUpQhgr4UIUAulCHBjShBW3owAh60IcBDGECY/OXcqjf9Q/K6qmsr8rGUrY1kQ+pfBkcDQplbmRzdHJlYW0NCmVuZG9iag0KeHJlZg0KMCA3MA0KMDAwMDAwMDAxNSA2NTUzNSBmDQowMDAwMDAwMDE3IDAwMDAwIG4NCjAwMDAwMDAxNjMgMDAwMDAgbg0KMDAwMDAwMDIxOSAwMDAwMCBuDQowMDAwMDAwNTAwIDAwMDAwIG4NCjAwMDAwMDMxOTcgMDAwMDAgbg0KMDAwMDAwMzMyNSAwMDAwMCBuDQowMDAwMDAzMzUzIDAwMDAwIG4NCjAwMDAwMDM1MDggMDAwMDAgbg0KMDAwMDAwMzU4MSAwMDAwMCBuDQowMDAwMDAzODE4IDAwMDAwIG4NCjAwMDAwMDM4NzIgMDAwMDAgbg0KMDAwMDAwMzkyNiAwMDAwMCBuDQowMDAwMDA0MDkzIDAwMDAwIG4NCjAwMDAwMDQzMzEgMDAwMDAgbg0KMDAwMDAwMDAxNiA2NTUzNSBmDQowMDAwMDAwMDE3IDY1NTM1IGYNCjAwMDAwMDAwMTggNjU1MzUgZg0KMDAwMDAwMDAxOSA2NTUzNSBmDQowMDAwMDAwMDIwIDY1NTM1IGYNCjAwMDAwMDAwMjEgNjU1MzUgZg0KMDAwMDAwMDAyMiA2NTUzNSBmDQowMDAwMDAwMDIzIDY1NTM1IGYNCjAwMDAwMDAwMjQgNjU1MzUgZg0KMDAwMDAwMDAyNSA2NTUzNSBmDQowMDAwMDAwMDI2IDY1NTM1IGYNCjAwMDAwMDAwMjcgNjU1MzUgZg0KMDAwMDAwMDAyOCA2NTUzNSBmDQowMDAwMDAwMDI5IDY1NTM1IGYNCjAwMDAwMDAwMzAgNjU1MzUgZg0KMDAwMDAwMDAzMSA2NTUzNSBmDQowMDAwMDAwMDMyIDY1NTM1IGYNCjAwMDAwMDAwMzMgNjU1MzUgZg0KMDAwMDAwMDAzNCA2NTUzNSBmDQowMDAwMDAwMDM1IDY1NTM1IGYNCjAwMDAwMDAwMzYgNjU1MzUgZg0KMDAwMDAwMDAzNyA2NTUzNSBmDQowMDAwMDAwMDM4IDY1NTM1IGYNCjAwMDAwMDAwMzkgNjU1MzUgZg0KMDAwMDAwMDA0MCA2NTUzNSBmDQowMDAwMDAwMDQxIDY1NTM1IGYNCjAwMDAwMDAwNDIgNjU1MzUgZg0KMDAwMDAwMDA0MyA2NTUzNSBmDQowMDAwMDAwMDQ0IDY1NTM1IGYNCjAwMDAwMDAwNDUgNjU1MzUgZg0KMDAwMDAwMDA0NiA2NTUzNSBmDQowMDAwMDAwMDQ3IDY1NTM1IGYNCjAwMDAwMDAwNDggNjU1MzUgZg0KMDAwMDAwMDA0OSA2NTUzNSBmDQowMDAwMDAwMDUwIDY1NTM1IGYNCjAwMDAwMDAwNTEgNjU1MzUgZg0KMDAwMDAwMDA1MiA2NTUzNSBmDQowMDAwMDAwMDUzIDY1NTM1IGYNCjAwMDAwMDAwNTQgNjU1MzUgZg0KMDAwMDAwMDA1NSA2NTUzNSBmDQowMDAwMDAwMDU2IDY1NTM1IGYNCjAwMDAwMDAwNTcgNjU1MzUgZg0KMDAwMDAwMDA1OCA2NTUzNSBmDQowMDAwMDAwMDU5IDY1NTM1IGYNCjAwMDAwMDAwNjAgNjU1MzUgZg0KMDAwMDAwMDA2MSA2NTUzNSBmDQowMDAwMDAwMDYyIDY1NTM1IGYNCjAwMDAwMDAwMDAgNjU1MzUgZg0KMDAwMDAwNTQyMSAwMDAwMCBuDQowMDAwMDA2MDIzIDAwMDAwIG4NCjAwMDAwMTcxNDMgMDAwMDAgbg0KMDAwMDAxNzYzOCAwMDAwMCBuDQowMDAwMDE3NjY1IDAwMDAwIG4NCjAwMDAwMjA3NjIgMDAwMDAgbg0KMDAwMDAyMDgwNyAwMDAwMCBuDQp0cmFpbGVyDQo8PC9TaXplIDcwL1Jvb3QgMSAwIFIvSW5mbyAxNCAwIFIvSURbPDM4RTM2RTYxN0ZDRTI0NDc5OEZEQTU0NUYxNEYzMjE0PjwzOEUzNkU2MTdGQ0UyNDQ3OThGREE1NDVGMTRGMzIxND5dID4+DQpzdGFydHhyZWYNCjIxMTgzDQolJUVPRg0KeHJlZg0KMCAwDQp0cmFpbGVyDQo8PC9TaXplIDcwL1Jvb3QgMSAwIFIvSW5mbyAxNCAwIFIvSURbPDM4RTM2RTYxN0ZDRTI0NDc5OEZEQTU0NUYxNEYzMjE0PjwzOEUzNkU2MTdGQ0UyNDQ3OThGREE1NDVGMTRGMzIxND5dIC9QcmV2IDIxMTgzL1hSZWZTdG0gMjA4MDc+Pg0Kc3RhcnR4cmVmDQoyMjc0MA0KJSVFT0Y="

# ocr_agent = OCR()
# text = ocr_agent.process_document(base64_encoded_document=test_image)
# ocr_processor = OCR()
# ocr_processor.process_document(test_image, query="")
# async def main():
#     load_dotenv()
#     api_key = os.getenv("TOGETHER_API_KEY")
#     agent = OCRagent(api_key=api_key)
#     mock_document = ""
#     mock_query = ""
#     async for update in agent.analyse_document(mock_document, mock_query):
#         try:
#             print(update)
#             if update["type"] == "step_update":
#                 print(f'Processing step {update["data"]["step_num"]}...')
#                 print(f'Step thougth: {update["data"]["summary_thought"]}')
#                 # print(f"Decision: {update['data']['actions']}")
#                 # print(f"Rationale: {update['data']['rationale']}\n")
#             elif update["type"] == "query_analysis":
#                 print("Query Analysis:", update["data"])
#             elif update["type"] == "final_response":
#                 print("Final response:", update["data"]["final_answer"])
#             else:
#                 print("Unknown update type:", update["type"])
#         except KeyError as e:
#             print(f"Error processing update: {e}")
#             print("Update structure:", update)
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
####
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

# class DetailedAnalyzer(dspy.Signature):
#     """Deep analysis of content."""

#     content = dspy.InputField(desc="Content to analyze")
#     initial_understanding = dspy.InputField(desc="Initial comprehension")
#     context = dspy.InputField(desc="Accumulated context")
#     questions = dspy.InputField(desc="Questions to address")

#     analysis_steps = dspy.OutputField(
#         desc="List of specific insights and observations about the content"
#     )
#     knowledge_gaps = dspy.OutputField(
#         desc="List of questions or areas needing clarification"
#     )
#     conclusions = dspy.OutputField(desc="Summary of key conclusions from the analysis")
#     confidence = dspy.OutputField(desc="Confidence score between 0 and 1")
#     rag_queries = dspy.OutputField(
#         desc="List of specific questions to query the RAG system"
#     )


# class CrossReferenceAnalyzer(dspy.Signature):
#     """Analyzes relationships between different parts."""

#     current_content = dspy.InputField(desc="Current text chunk")
#     previous_analyses = dspy.InputField(
#         desc="List of previous chunk analyses in dict format"
#     )
#     context = dspy.InputField(desc="Overall accumulated context")

#     connections = dspy.OutputField(
#         desc="List of connections found with previous chunks"
#     )
#     impact = dspy.OutputField(
#         desc="Description of how these connections affect understanding"
#     )
#     suggested_updates = dspy.OutputField(
#         desc="List of suggested updates to previous analyses"
#     )

#     async def analyze_chunk(
#         self, chunk: str, chunk_id: str, query: str
#     ) -> ChunkAnalysis:
#         """Perform detailed analysis of a single chunk."""
#         steps = []

#         # Initial understanding
#         understanding = self.understanding(
#             content=chunk, query=query, previous_context=self.cognitive_state["context"]
#         )

#         # Extract confidence from relevance score
#         try:
#             relevance_score_regex = re.search(
#                 r"(\d*\.?\d+)", str(understanding.relevance)
#             )
#             confidence = (
#                 float(relevance_score_regex.group(0)) if relevance_score_regex else 0.5
#             )
#         except (ValueError, AttributeError):
#             confidence = 0.5

#         # Add initial understanding step
#         steps.append(
#             ReasoningStep(
#                 action=CognitiveAction.UNDERSTAND_CONTEXT,
#                 thought=understanding.initial_thoughts,
#                 confidence=confidence,
#                 supporting_evidence=[
#                     point for point in understanding.main_points if point
#                 ],
#             )
#         )

#         # Generate initial questions
#         if understanding.questions_raised:
#             steps.append(
#                 ReasoningStep(
#                     action=CognitiveAction.IDENTIFY_KNOWLEDGE_GAP,
#                     thought="Identified areas requiring further investigation",
#                     confidence=confidence,
#                     queries_generated=understanding.questions_raised
#                     if isinstance(understanding.questions_raised, list)
#                     else [understanding.questions_raised],
#                 )
#             )

#         # Detailed analysis
#         analysis = self.analyzer(
#             content=chunk,
#             initial_understanding=understanding.initial_thoughts,
#             context=self.cognitive_state["context"],
#             questions=understanding.questions_raised,
#         )

#         # Process analysis steps
#         analysis_thoughts = []
#         if isinstance(analysis.analysis_steps, str):
#             # Split by periods and newlines
#             thoughts = re.split(r"[.\n]+", analysis.analysis_steps)
#             analysis_thoughts = [t.strip() for t in thoughts if t.strip()]
#         elif isinstance(analysis.analysis_steps, list):
#             analysis_thoughts = [t for t in analysis.analysis_steps if t]

#         # Extract analysis confidence
#         try:
#             analysis_confidence_regex = re.search(
#                 r"(\d*\.?\d+)", str(analysis.confidence)
#             )
#             analysis_confidence = (
#                 float(analysis_confidence_regex.group(0))
#                 if analysis_confidence_regex
#                 else confidence
#             )
#         except (ValueError, AttributeError):
#             analysis_confidence = confidence

#         # Add analysis steps
#         for thought in analysis_thoughts:
#             steps.append(
#                 ReasoningStep(
#                     action=CognitiveAction.EVALUATE_ARGUMENTS,
#                     thought=thought,
#                     confidence=analysis_confidence,
#                     queries_generated=[],
#                 )
#             )

#         # Process knowledge gaps
#         if analysis.knowledge_gaps:
#             gaps = (
#                 analysis.knowledge_gaps
#                 if isinstance(analysis.knowledge_gaps, list)
#                 else [analysis.knowledge_gaps]
#             )
#             for gap in gaps:
#                 steps.append(
#                     ReasoningStep(
#                         action=CognitiveAction.IDENTIFY_KNOWLEDGE_GAP,
#                         thought=f"Knowledge gap identified: {gap}",
#                         confidence=analysis_confidence,
#                         queries_generated=analysis.rag_queries
#                         if isinstance(analysis.rag_queries, list)
#                         else [analysis.rag_queries],
#                     )
#                 )

#         # Add RAG queries to global state
#         if analysis.rag_queries:
#             queries = (
#                 analysis.rag_queries
#                 if isinstance(analysis.rag_queries, list)
#                 else [analysis.rag_queries]
#             )
#             self.cognitive_state["rag_queries"].update(queries)

#         return ChunkAnalysis(
#             chunk_id=chunk_id,
#             content=chunk,
#             steps=steps,
#             final_understanding=analysis.conclusions,
#             relevance_score=confidence,
#             knowledge_gaps=gaps if analysis.knowledge_gaps else [],
#         )

#     async def process_cross_references(self):
#         """Analyze relationships between chunks."""
#         for idx, current_analysis in enumerate(self.cognitive_state["chunk_analyses"]):
#             if idx > 0:  # Only process if we have previous chunks
#                 # Convert previous analyses to dictionary format
#                 previous_analyses = [
#                     {
#                         "chunk_id": analysis.chunk_id,
#                         "content": analysis.content,
#                         "understanding": analysis.final_understanding,
#                     }
#                     for analysis in self.cognitive_state["chunk_analyses"][:idx]
#                 ]

#                 cross_ref = self.cross_referencer(
#                     current_content=current_analysis.content,
#                     previous_analyses=previous_analyses,
#                     context=self.cognitive_state["context"],
#                 )

#                 self.cognitive_state["cross_references"].append(
#                     {
#                         "source_chunk": current_analysis.chunk_id,
#                         "connections": cross_ref.connections,
#                         "impact": cross_ref.impact,
#                     }
#                 )

#     def generate_markdown_response(self) -> str:
#         """Generate final markdown response."""
#         synthesis = self.synthesizer(
#             analyses=self.cognitive_state["chunk_analyses"],
#             query=self.current_query,
#             context=self.cognitive_state["context"],
#             cross_references=self.cognitive_state["cross_references"],
#         )

#         # Format confidence metrics
#         confidence_stats = {
#             "overall": float(synthesis.confidence_assessment),
#             "by_section": [
#                 {"section": analysis.chunk_id, "confidence": analysis.relevance_score}
#                 for analysis in self.cognitive_state["chunk_analyses"]
#             ],
#         }

#         # Build markdown structure
#         markdown_sections = [
#             "# Document Analysis Results\n",
#             f"## Query\n{self.current_query}\n",
#             "## Key Findings\n"
#             + "\n".join([f"- {finding}" for finding in synthesis.key_findings]),
#             "## Detailed Analysis\n" + synthesis.markdown_output,
#             "## Confidence Assessment\n"
#             + f"Overall confidence: {confidence_stats['overall']:.2f}",
#         ]

#         return "\n\n".join(markdown_sections)

#     async def process_document(self, document_text: Dict, query: str):
#         """Process document with streaming updates."""
#         self.reset_state()
#         self.current_query = query

#         # Initial query analysis
#         yield {
#             "type": "process_start",
#             "data": {"query": query, "timestamp": datetime.now().isoformat()},
#         }

#         # Process each chunk
#         for page_num, page in document_text.get("page", {}).items():
#             for para_num, paragraph in page.get("paragraph", {}).items():
#                 chunk_id = f"p{page_num}_para{para_num}"

#                 # Analyze chunk
#                 analysis = await self.analyze_chunk(paragraph, chunk_id, query)
#                 self.cognitive_state["chunk_analyses"].append(analysis)
#                 self.cognitive_state["context"] += f"\n{paragraph}"

#                 # Stream chunk analysis
#                 yield {
#                     "type": "chunk_analysis",
#                     "data": {
#                         "chunk_id": chunk_id,
#                         "steps": [
#                             {
#                                 "action": step.action.value,
#                                 "thought": step.thought,
#                                 "confidence": step.confidence,
#                                 "timestamp": step.timestamp.isoformat(),
#                             }
#                             for step in analysis.steps
#                         ],
#                         "relevance": analysis.relevance_score,
#                     },
#                 }

#         # Process cross-references
#         await self.process_cross_references()

#         # Generate final response
#         markdown_response = self.generate_markdown_response()

#         yield {
#             "type": "final_response",
#             "data": {
#                 "markdown": markdown_response,
#                 "metadata": {
#                     "chunks_processed": len(self.cognitive_state["chunk_analyses"]),
#                     "rag_queries": list(self.cognitive_state["rag_queries"]),
#                     "cross_references": self.cognitive_state["cross_references"],
#                 },
#             },
#         }
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Set
import dspy


class CognitiveAction(Enum):
    UNDERSTAND_PROBLEM = "understand_problem"
    IDENTIFY_GAPS = "identify_gaps"
    GATHER_INFORMATION = "gather_information"
    SYNTHESIZE_INFO = "synthesize_info"
    EVALUATE_ARGUMENTS = "evaluate_arguments"
    ITERATE_RESEARCH = "iterate_research"
    DRAW_CONCLUSIONS = "draw_conclusions"
    COMMUNICATE_FINDINGS = "communicate_findings"


@dataclass
class ResearchQuery:
    question: str
    context: str
    relevance_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    results: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class LegalReference:
    law_id: str
    article: str
    content: str
    relevance_score: float
    interpretation: str = ""


@dataclass
class Argument:
    claim: str
    evidence: List[str]
    strength: float
    counter_arguments: List[str] = field(default_factory=list)
    legal_basis: List[LegalReference] = field(default_factory=list)


@dataclass
class CognitiveAnalysis:
    document_id: str
    original_query: str
    understanding: Dict[str, str] = field(default_factory=dict)
    knowledge_gaps: List[str] = field(default_factory=list)
    research_queries: List[ResearchQuery] = field(default_factory=list)
    synthesized_findings: Dict[str, str] = field(default_factory=dict)
    evaluated_arguments: Dict[str, float] = field(default_factory=dict)
    legal_references: List[LegalReference] = field(default_factory=list)
    arguments: List[Argument] = field(default_factory=list)
    final_conclusions: str = ""
    confidence_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class UnderstandProblem(dspy.Signature):
    """Compreende profundamente o documento e o seu contexto legal."""

    content = dspy.InputField(desc="Conteúdo do documento")
    query = dspy.InputField(desc="Questão do utilizador")

    document_purpose = dspy.OutputField(desc="Objetivo principal do documento")
    main_claims = dspy.OutputField(desc="Principais argumentos apresentados")
    legal_framework = dspy.OutputField(desc="Enquadramento legal identificado")
    initial_analysis = dspy.OutputField(desc="Análise inicial do problema")


class IdentifyKnowledgeGaps(dspy.Signature):
    """Identifica lacunas de conhecimento que precisam ser investigadas."""

    initial_understanding = dspy.InputField()
    legal_context = dspy.InputField()

    knowledge_gaps: List[str] = dspy.OutputField(desc="Lista de lacunas identificadas")
    research_questions: List[str] = dspy.OutputField(
        desc="Perguntas específicas para pesquisa"
    )
    priority_areas: List[str] = dspy.OutputField(
        desc="Áreas prioritárias para investigação"
    )


class ResearchGatherer(dspy.Signature):
    """Pesquisa informações relevantes na base de dados."""

    research_questions = dspy.InputField()
    legal_context = dspy.InputField()

    relevant_laws = dspy.OutputField(desc="Leis e regulamentos relevantes")
    case_precedents = dspy.OutputField(desc="Precedentes legais")
    supporting_evidence = dspy.OutputField(desc="Evidências de suporte")


class SynthesisEngine(dspy.Signature):
    """Sintetiza as informações recolhidas em conclusões coerentes."""

    research_results = dspy.InputField()
    initial_understanding = dspy.InputField()

    synthesized_findings = dspy.OutputField(desc="Síntese das descobertas")
    key_insights = dspy.OutputField(desc="Insights principais")
    confidence_assessment = dspy.OutputField(desc="Avaliação de confiança")


class ArgumentEvaluator(dspy.Signature):
    """Avalia a força dos argumentos com base nas evidências."""

    arguments = dspy.InputField()
    legal_references = dspy.InputField()

    evaluated_arguments = dspy.OutputField(desc="Argumentos avaliados")
    strength_assessment = dspy.OutputField(desc="Avaliação da força dos argumentos")
    counter_arguments = dspy.OutputField(desc="Contra-argumentos identificados")


class ConclusionGenerator(dspy.Signature):
    """Gera conclusões finais e recomendações."""

    evaluated_arguments = dspy.InputField()
    synthesized_findings = dspy.InputField()
    legal_context = dspy.InputField()

    conclusions = dspy.OutputField(desc="Conclusões finais")
    recommendations = dspy.OutputField(desc="Recomendações")
    confidence_score: float = dspy.OutputField(desc="Pontuação de confiança")


class ReportFormatter(dspy.Signature):
    """Formata as conclusões em um relatório estruturado."""

    analysis = dspy.InputField()

    formatted_report = dspy.OutputField(desc="Relatório formatado")
    executive_summary = dspy.OutputField(desc="Resumo executivo")


class EnhancedCognitiveOCRAgent(dspy.Module):
    def __init__(self, retriever):
        super().__init__()
        self.retriever = retriever
        self.understanding = dspy.ChainOfThought(UnderstandProblem)
        self.gap_identifier = dspy.ChainOfThought(IdentifyKnowledgeGaps)
        self.researcher = dspy.ChainOfThought(ResearchGatherer)
        self.synthesizer = dspy.ChainOfThought(SynthesisEngine)
        self.evaluator = dspy.ChainOfThought(ArgumentEvaluator)
        self.conclusion_generator = dspy.ChainOfThought(ConclusionGenerator)
        self.report_formatter = dspy.ChainOfThought(ReportFormatter)
        self.current_analysis = None

    def process_document(self, document: str, query: str) -> dict:
        """Processa o documento completo e retorna a análise."""
        self.current_analysis = CognitiveAnalysis(
            document_id=str(hash(document)), original_query=query
        )

        understanding = self._understand_problem(document, query)

        gaps = self._identify_gaps(understanding)

        research_results = self._gather_research(gaps)

        synthesis = self._synthesize_information(research_results, understanding)
        print(synthesis)

        evaluated = self._evaluate_arguments(synthesis)

        conclusions = self._draw_conclusions(evaluated, synthesis)

        final_report = self._format_report()

        return final_report

    def _understand_problem(self, document: str, query: str) -> Dict[str, Any]:
        print("A analisar o documento")
        understanding = self.understanding(content=document, query=query)

        self.current_analysis.understanding = {
            "purpose": understanding.document_purpose,
            "claims": understanding.main_claims,
            "legal_framework": understanding.legal_framework,
            "initial_analysis": understanding.initial_analysis,
        }

        return understanding

    def _identify_gaps(self, understanding: Any) -> Dict[str, Any]:
        print("A identificar lacunas")
        gaps = self.gap_identifier(
            initial_understanding=understanding.initial_analysis,
            legal_context=understanding.legal_framework,
        )

        self.current_analysis.knowledge_gaps = gaps.knowledge_gaps
        return gaps

    def _gather_research(self, gaps: Any) -> List[Dict[str, Any]]:
        print("A pesquisar na base de dados legal")
        research_results = []

        for question in gaps.research_questions:
            query = ResearchQuery(
                question=question, context=str(gaps.priority_areas), relevance_score=0.0
            )
            # Use retriever to get information
            retrieved_info = self.retriever.query(query=question, topk=3, queue=None)
            parsed_docs = [doc.get("text", "") for doc in retrieved_info]
            query.results = parsed_docs
            # Calculate confidence based on retrieval results
            query.confidence = self._calculate_confidence(retrieved_info)

            self.current_analysis.research_queries.append(query)
            research_results.append(
                {
                    "question": question,
                    "results": parsed_docs,
                    "confidence": query.confidence,
                }
            )

        return research_results

    def _synthesize_information(
        self, research_results: List[Dict[str, Any]], understanding: Any
    ) -> Dict[str, Any]:
        print("A sintetizar informação")
        synthesis = self.synthesizer(
            research_results=research_results,
            initial_understanding=understanding.initial_analysis,
        )

        self.current_analysis.synthesized_findings = {
            "findings": synthesis.synthesized_findings,
            "insights": synthesis.key_insights,
            "confidence": synthesis.confidence_assessment,
        }

        return synthesis

    def _evaluate_arguments(self, synthesis: Any) -> Dict[str, Any]:
        print("A avaliar argumentos")
        evaluation = self.evaluator(
            arguments=self.current_analysis.understanding["claims"],
            legal_references=self.current_analysis.legal_references,
        )

        self.current_analysis.evaluated_arguments = {
            arg: score
            for arg, score in zip(
                evaluation.evaluated_arguments, evaluation.strength_assessment
            )
        }

        return evaluation

    def _draw_conclusions(self, evaluated: Any, synthesis: Any) -> Dict[str, Any]:
        print(f"A tirar conclusões")
        conclusions = self.conclusion_generator(
            evaluated_arguments=evaluated.evaluated_arguments,
            synthesized_findings=synthesis.synthesized_findings,
            legal_context=self.current_analysis.understanding["legal_framework"],
        )

        self.current_analysis.final_conclusions = conclusions.conclusions
        self.current_analysis.recommendations = conclusions.recommendations
        self.current_analysis.confidence_score = float(conclusions.confidence_score)

        return conclusions

    def _format_report(self):
        print("A finalizar a formatação")
        print(self.current_analysis)
        report = self.report_formatter(analysis=self.current_analysis)
        print(report)
        return {
            "report": report.formatted_report,
            "summary": report.executive_summary,
            "confidence": self.current_analysis.confidence_score,
            "recommendations": self.current_analysis.recommendations,
        }

    def _calculate_confidence(self, results: List[str]) -> float:
        print("A calcular a confiança nos documentos extraido")
        if not results:
            return 0.0

        # Implement your confidence calculation logic here
        # This is a simple example
        relevance_scores = [result.get("score", 0) / 100 for result in results]
        return min(sum(relevance_scores) / len(relevance_scores), 1.0)


def setup_cognitive_system(api_key: str, retriever) -> EnhancedCognitiveOCRAgent:
    """Configura e retorna uma instância do sistema cognitivo."""
    config = CognitiveOCRConfig(api_key=api_key)
    agent = EnhancedCognitiveOCRAgent(retriever=retriever)
    return agent


class CognitiveOCRConfig:
    def __init__(self, api_key: str):
        self.llm = dspy.LM(
            "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", api_key=api_key
        )
        dspy.configure(lm=self.llm)
        self.reset_state()

    def get_lm(self):
        return self.llm

    def reset_state(self):
        self.cognitive_state = {
            "context": "",
            "chunk_analyses": [],
            "cross_references": [],
            "rag_queries": set(),
            "confidence_history": [],
        }


# Example usage
def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("TOGETHER_API_KEY")

    # Initialize your retriever here
    retriever = Retriever()  # Replace with your actual retriever

    mock_document = {
        "page": {
            0: {
                "paragraph": {
                    1: "COMUNICADO A IMPRENSA",
                    2: 'ASSUNTO: PETEÇAO PUBLECA PEDE A EXTINÇAO DA "ASSOCIACAO DAS TESTEMUNHAS DE JEOVA" E o CANCELAMENTO po SEU - DE RELIGIAO RECONHECIOA PELO ESTADO',
                    3: "PORTUGUÈS. usboà, 9 de Fevereiro de 2018",
                    4: ") dia 9 de Março de 2018 marca a passegem do 400 aniversério da publicaçso, emn Dlàrlo da Repiblica, L Série A, no 57/78, da Declaraçao Universal dos Direltos do Homemn; o dla 9 de Novembro de 2018 marca da passagem do 400 aniversario da entrada emn vigor na ordemn I portuguesa da Convençào Européla dos Direitos do Homem. Nestas convençbes estao consagrados vàrlos direltos fundamentals do ser humano, nos quais % incluern 0 direlto à liberdade de pensamento, de opiniko e de expressso, a tiberdade de ter uma religiko ou mudar de religiho ou de crenças @ de nao ser Inquietado, discriminedo ou prejudicado por isso. Em sintonla com estas convençbes 4 Constituiçho da Republica Portuguess consagra diversos direltos, laberdades e garantias pessoals, entre os quals se contam o dinelto à lberdade de conscièncla, de religiao e de culto, bem como o direito à liberdade de expressào, de assoctaçao, o direlto à integridade moral e fisica, o direito a nido sea tratado con crueldade ou desumanidade, o direito & bom nome 4 a no ser tratado com discriminaçào, entre outros. Acontece por vezes que o direlto à lberdade religlosa collde com outros direlkos fundamentals dos Individuos. Quais sao os limites da laberdade religlosa? Serà que a Nberdade de praticar uma rellglao permite atropelar outros direitos humanos fundementals? Pode-se permitir tudo a uma organizaçao religlosa E nome da liberdade religlosa consagrada na constituiçao? Eske à um Em causa està o tratamento dispensado pelas Testemunhas de 1 àquetes Individuos, adultos e menores, que por algum motivo deixaram de estar afiliados corn esta organtzaçao I As Testemunhas de Jeova êm uama pratica de excomunhso que Implica a completa ostracizaçao social dos ex-membros e 0 odlo &os dissidentes de 1 essa prética ensinada e - de forma Instiucional separa familas e amigos, causs danos psicotogicos profundos que podem, no limite, terminar 3o suicidio, coage oS Indlviduos, limita a auto-detemminacao da pessoa, destrol a sua auto-estime e agride a dignidade humana. Deve uma Igreja que advoga praticas cruéis, desumanas e que violarn a lel, a Constituiçao e os direltos humanos continuar à receber reconhecimente oficlal do Estado7 Pode e deve  Estado Fol colocada online uma petiçao so porlomento, -o sentido de pedir a extinçao de entidode colectiva religiosa que I as Testemunhas de Jeovà em Portugal e cancelar o su registo como I coletiva rellglosa, retirando-lhe assim 0 estatuto de rellglao I oficialmente pelo I Portuguès. até que esta prética de ostracizaçao I seja concelado definitivamente pelo grupo religioso e as suas vitimas allviadas do sofconfigrimento que por causa proscriçio ou 0 banimento desta religiso, nem de impedir 9 individuos que professam esta fé :a reunirem liveemente ou divuigarem n :uns crenças; entendemos que asses :so diraitos I que nao colidem com outros direitos individumis Esta petiçao visa apenas o estatuto da entidade religlosa colectiva que as representa, e, caso a violaçao dos direitos humanos e constituclonais cesse de forma satisfatéria e I entendemos que",
                    5: "debate que a nossa I precisa fazer.",
                    6: "intervir no sentido de regular este confito e proteger os cidadhos?",
                    7: "dela passam. € muito importente destacar",
                    8: "seguinte: Nso : trata de pedir",
                    9: "as Testemunhas de Jeové I voltar a gozar de reconhecimento oficiab.",
                    10: "A petiçao pode ser encontrada no seguinte endereço:",
                    11: "http://peticaopublica.com/oview.aspx7pl-ExtRegistoAT)",
                    12: "Agradecemos a atençao e divulgaçao da Iniciativa e a promoçao do debate deste kemo no sociedade. Para mais esclarecimentos podera obter 0s contactos de quern propde esta Iniciotiva",
                    13: "enviando mensagem pare o correio electronico sdenone.Ziegmall.cem",
                }
            }
        }
    }

    document = "".join(mock_document["page"][0]["paragraph"].values())

    query = "Os jeovas declaram impostos?"

    # Setup the cognitive system
    agent = setup_cognitive_system(api_key=api_key, retriever=retriever)

    # Example document and query
    # document = """
    # [Your document content here]
    # """
    # query = "What are the legal implications of this document?"

    # Process the document
    result = agent.process_document(document=document, query=query)

    # Print results
    print("\n=== Analysis Results ===")
    print("\nExecutive Summary:")
    print(result["summary"])
    print("\nConfidence Score:", result["confidence"])
    print("\nRecommendations:")
    for rec in result["recommendations"]:
        print(f"- {rec}")


if __name__ == "__main__":
    main()

# async def process_rag_queries(self, queries: List[str]) -> Dict[str, str]:
#     """Process RAG queries and return results."""
#     # Implement your RAG logic here
#     results = {}
#     for query in queries:
#         # Placeholder for RAG implementation
#         results[query] = f"RAG response for: {query}"
#     return results


# import asyncio
# import os
# from dotenv import load_dotenv


# def main():
#     load_dotenv()
#     api_key = os.getenv("TOGETHER_API_KEY")

#     config = CognitiveOCRConfig(api_key=api_key)
#     lm = config.get_lm()
#     agent = CognitiveOCRAgent()
#     # Mock document with multiple pages and paragraphs
#     mock_document = {
#         "page": {
#             0: {
#                 "paragraph": {
#                     1: "COMUNICADO A IMPRENSA",
#                     2: 'ASSUNTO: PETEÇAO PUBLECA PEDE A EXTINÇAO DA "ASSOCIACAO DAS TESTEMUNHAS DE JEOVA" E o CANCELAMENTO po SEU - DE RELIGIAO RECONHECIOA PELO ESTADO',
#                     3: "PORTUGUÈS. usboà, 9 de Fevereiro de 2018",
#                     4: ") dia 9 de Março de 2018 marca a passegem do 400 aniversério da publicaçso, emn Dlàrlo da Repiblica, L Série A, no 57/78, da Declaraçao Universal dos Direltos do Homemn; o dla 9 de Novembro de 2018 marca da passagem do 400 aniversario da entrada emn vigor na ordemn I portuguesa da Convençào Européla dos Direitos do Homem. Nestas convençbes estao consagrados vàrlos direltos fundamentals do ser humano, nos quais % incluern 0 direlto à liberdade de pensamento, de opiniko e de expressso, a tiberdade de ter uma religiko ou mudar de religiho ou de crenças @ de nao ser Inquietado, discriminedo ou prejudicado por isso. Em sintonla com estas convençbes 4 Constituiçho da Republica Portuguess consagra diversos direltos, laberdades e garantias pessoals, entre os quals se contam o dinelto à lberdade de conscièncla, de religiao e de culto, bem como o direito à liberdade de expressào, de assoctaçao, o direlto à integridade moral e fisica, o direito a nido sea tratado con crueldade ou desumanidade, o direito & bom nome 4 a no ser tratado com discriminaçào, entre outros. Acontece por vezes que o direlto à lberdade religlosa collde com outros direlkos fundamentals dos Individuos. Quais sao os limites da laberdade religlosa? Serà que a Nberdade de praticar uma rellglao permite atropelar outros direitos humanos fundementals? Pode-se permitir tudo a uma organizaçao religlosa E nome da liberdade religlosa consagrada na constituiçao? Eske à um Em causa està o tratamento dispensado pelas Testemunhas de 1 àquetes Individuos, adultos e menores, que por algum motivo deixaram de estar afiliados corn esta organtzaçao I As Testemunhas de Jeova êm uama pratica de excomunhso que Implica a completa ostracizaçao social dos ex-membros e 0 odlo &os dissidentes de 1 essa prética ensinada e - de forma Instiucional separa familas e amigos, causs danos psicotogicos profundos que podem, no limite, terminar 3o suicidio, coage oS Indlviduos, limita a auto-detemminacao da pessoa, destrol a sua auto-estime e agride a dignidade humana. Deve uma Igreja que advoga praticas cruéis, desumanas e que violarn a lel, a Constituiçao e os direltos humanos continuar à receber reconhecimente oficlal do Estado7 Pode e deve  Estado Fol colocada online uma petiçao so porlomento, -o sentido de pedir a extinçao de entidode colectiva religiosa que I as Testemunhas de Jeovà em Portugal e cancelar o su registo como I coletiva rellglosa, retirando-lhe assim 0 estatuto de rellglao I oficialmente pelo I Portuguès. até que esta prética de ostracizaçao I seja concelado definitivamente pelo grupo religioso e as suas vitimas allviadas do sofconfigrimento que por causa proscriçio ou 0 banimento desta religiso, nem de impedir 9 individuos que professam esta fé :a reunirem liveemente ou divuigarem n :uns crenças; entendemos que asses :so diraitos I que nao colidem com outros direitos individumis Esta petiçao visa apenas o estatuto da entidade religlosa colectiva que as representa, e, caso a violaçao dos direitos humanos e constituclonais cesse de forma satisfatéria e I entendemos que",
#                     5: "debate que a nossa I precisa fazer.",
#                     6: "intervir no sentido de regular este confito e proteger os cidadhos?",
#                     7: "dela passam. € muito importente destacar",
#                     8: "seguinte: Nso : trata de pedir",
#                     9: "as Testemunhas de Jeové I voltar a gozar de reconhecimento oficiab.",
#                     10: "A petiçao pode ser encontrada no seguinte endereço:",
#                     11: "http://peticaopublica.com/oview.aspx7pl-ExtRegistoAT)",
#                     12: "Agradecemos a atençao e divulgaçao da Iniciativa e a promoçao do debate deste kemo no sociedade. Para mais esclarecimentos podera obter 0s contactos de quern propde esta Iniciotiva",
#                     13: "enviando mensagem pare o correio electronico sdenone.Ziegmall.cem",
#                 }
#             }
#         }
#     }

#     mock_query = "Os jeovas declaram impostos?"

#     print("\n=== Starting Document Analysis ===\n")
#     print(f"Query: {mock_query}\n")

#     res = agent(document=mock_document, query=mock_query)

#     print(f"Answer: {res}\n")

#     print("-------------------")
#     # print(f"llm: {lm.inspect_history(n=1)}")
#     return res
#     # async for update in agent.process_document(mock_document, mock_query):
#     #     try:
#     #         if update["type"] == "process_start":
#     #             print("🔍 Beginning Analysis...")
#     #             print("-" * 50)

#     #         elif update["type"] == "chunk_analysis":
#     #             print(f"\n📝 Processing Chunk {update['data']['chunk_id']}...")
#     #             print("\nReasoning Steps:")
#     #             for step in update["data"]["steps"]:
#     #                 print(f"\n🤔 {step['action']}:")
#     #                 print(f"   Thought: {step['thought']}")
#     #                 print(f"   Confidence: {step['confidence']:.2f}")
#     #             print(f"\nRelevance Score: {update['data']['relevance']:.2f}")
#     #             print("-" * 50)

#     #         elif update["type"] == "final_response":
#     #             print("\n✨ Final Analysis:")
#     #             print("\n" + update["data"]["markdown"])
#     #             print("\n📊 Metadata:")
#     #             print(
#     #                 f"- Chunks Processed: {update['data']['metadata']['chunks_processed']}"
#     #             )
#     #             print(
#     #                 f"- RAG Queries Generated: {len(update['data']['metadata']['rag_queries'])}"
#     #             )
#     #             print(
#     #                 f"- Cross References Found: {len(update['data']['metadata']['cross_references'])}"
#     #             )

#     #         else:
#     #             print(f"\n⚠️ Unknown update type: {update['type']}")

#     #     except KeyError as e:
#     #         print(f"\n❌ Error processing update: {e}")
#     #         print("Update structure:", update)

#     #     except Exception as e:
#     #         print(f"\n❌ Unexpected error: {e}")


# if __name__ == "__main__":
#     main()