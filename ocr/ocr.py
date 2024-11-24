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


class DecisionType(Enum):
    KEEP_CONTEXT = "keep_context"
    GENERATE_QUERY = "generate_query"
    SKIP_CHUNK = "skip_chunk"
    ELABORATE_RATIONALE = "elaborate_rationale"
    EXTRACT_INFORMATION = "extract_information"
    CROSS_REFERENCE = "cross_reference"


@dataclass
class DocumentReference:
    page: int
    paragraph: int
    content: str
    extracted_info: Dict[str, Any]
    context: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert the DocumentReference to a dictionary."""
        return {
            "page": self.page,
            "paragraph": self.paragraph,
            "content": self.content,
            "extracted_info": self.extracted_info,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class KnowledgeItem:
    content: str
    source_references: List[DocumentReference]
    confidence: float
    last_updated: datetime = field(default_factory=datetime.now)
    related_items: List[str] = field(default_factory=list)


@dataclass
class ProcessingStep:
    step_num: int
    chunk: str
    current_context: str
    decision: DecisionType
    rationale: str
    knowledge_updates: List[Dict[str, Any]]
    cross_references: List[DocumentReference] = field(default_factory=list)
    generated_query: Optional[str] = None
    rag_response: Optional[str] = None
    extracted_info: Optional[Dict[str, Any]] = None
    relevance_score: float = 0.0


class QueryAnalyzer(dspy.Signature):
    """Analyzes the user query to determine information extraction strategy."""

    query = dspy.InputField(desc="User's query about the document")

    query_type = dspy.OutputField(
        desc="Type of query (general_analysis, specific_info, etc.)"
    )
    extraction_strategy = dspy.OutputField(
        desc="Strategy for extracting relevant information"
    )
    required_fields = dspy.OutputField(desc="List of specific fields to extract")


class ChunkAnalyzer(dspy.Signature):
    """Analyzes text chunks in context of the query."""

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
    """Generates intermediate thoughts and reasoning."""

    context = dspy.InputField(desc="Current context")
    query = dspy.InputField(desc="Original user query")
    recent_decision = dspy.InputField(desc="Last processing step details")
    extraction_strategy = dspy.InputField(desc="Current extraction strategy")

    thought = dspy.OutputField(desc="Generated thought or analysis")
    updated_context = dspy.OutputField(desc="New context incorporating the thought")
    query_progress = dspy.OutputField(desc="Progress towards answering the query")


class CrossReferenceAnalyzer(dspy.Signature):
    """Analyzes potential connections with previous document sections."""

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
        """Analyze the user's query to determine processing strategy."""
        # Remove await - DSPy Predict is synchronous
        analysis = self.query_analyzer(query=query)
        return {
            "query_type": analysis.query_type,
            "extraction_strategy": analysis.extraction_strategy,
            "required_fields": analysis.required_fields,
        }

    def analyze_cross_references(self, chunk: str, query: str) -> Dict[str, Any]:
        """Analyze connections with previous knowledge."""
        # Remove await - DSPy Predict is synchronous
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
        # TODO: Handle exception properly
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

        cross_ref_analysis = self.analyze_cross_references(chunk, query)
        # Chunk analysis - now synchronous
        analysis = self.chunk_analyzer(
            context=self.current_context,
            chunk=chunk,
            query=query,
            query_strategy=query_strategy["extraction_strategy"],
            required_fields=query_strategy["required_fields"],
        )

        # Process reference
        ref_id = self.knowledge_base.add_reference(
            page=page,
            paragraph=paragraph,
            content=chunk,
            extracted_info=analysis.extracted_info or {},
            context=self.current_context,
        )
        knowledge_updates = []
        cross_references = []
        if cross_ref_analysis["confidence"] > 0.7:
            related_refs = self.knowledge_base.find_related_references(chunk)
            cross_references.extend(related_refs)
            if related_refs:
                # Now synchronous
                new_knowledge = self.thought_generator(
                    context=self.current_context,
                    query=query,
                    recent_decision={
                        "chunk": chunk,
                        "related_refs": [ref.to_dict() for ref in related_refs],
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

                knowledge_updates.append(
                    {
                        "key": knowledge_key,
                        "content": new_knowledge.thought,
                        "confidence": cross_ref_analysis["confidence"],
                    }
                )

        step = ProcessingStep(
            step_num=len(self.processing_steps) + 1,
            chunk=chunk,
            current_context=self.current_context,
            decision=DecisionType(analysis.decision),
            rationale=analysis.rationale,
            knowledge_updates=knowledge_updates,
            cross_references=cross_references,
            extracted_info=analysis.extracted_info,
            relevance_score=float(analysis.relevance_score),
        )

        if step.decision in [DecisionType.KEEP_CONTEXT, DecisionType.CROSS_REFERENCE]:
            self.current_context += f"\n{chunk}"

        self.processing_steps.append(step)
        return step

    async def analyse_document(self, document_text: Dict, query: str):
        """Process document with knowledge building and cross-referencing."""
        # Now synchronous
        query_strategy = self.analyze_query(query)

        yield {"type": "query_analysis", "data": query_strategy}

        for page_num, page in document_text.get("page", {}).items():
            for para_num, paragraph in page.get("paragraph", {}).items():
                step = await self.process_chunk(
                    chunk=paragraph,
                    query=query,
                    page=int(page_num),
                    paragraph=int(para_num),
                    query_strategy=query_strategy,
                )

                print(step)

                yield {
                    "type": "step_update",
                    "data": {
                        "step_num": step.step_num,
                        "chunk": step.chunk,
                        "decision": step.decision.value,
                        "rationale": step.rationale,
                        "knowledge_updates": step.knowledge_updates,
                        "cross_references": [
                            {
                                "page": ref.page,
                                "paragraph": ref.paragraph,
                                "content": ref.content,
                            }
                            for ref in step.cross_references
                        ],
                        "extracted_info": step.extracted_info,
                        "relevance_score": step.relevance_score,
                        "current_context": self.current_context,
                    },
                }

        # Now synchronous
        final_thought = self.thought_generator(
            context=self.current_context,
            query=query,
            recent_decision=self.processing_steps[-1],
            extraction_strategy=query_strategy["extraction_strategy"],
        )

        yield {
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
                        "decision": step.decision.value,
                        "rationale": step.rationale,
                        "knowledge_updates": step.knowledge_updates,
                        "relevance_score": step.relevance_score,
                    }
                    for step in self.processing_steps
                ],
            },
        }


async def main():
    load_dotenv()
    api_key = os.getenv("TOGETHER_API_KEY")

    agent = OCRagent(api_key=api_key)

    mock_document = {
        "page": {
            0: {
                "paragraph": {
                    1: "- I DO PORTO SANTO",
                    2: "AVISO (M/F)",
                    3: "CONTRATOS DE I EM FUNÇOES PUBLICAS POR TEMPO I",
                    4: "Para os efeitos - do n. 2 do artigo 33.9 da Lei Geral do Trabalho em Funcbes Poblicas (LGTFP). aprovada em anexo à Lei n. 35/2014, de zo de junho, com a alines a) do n. 1 do artigo 19,9 da Portaria n. 83-A/2009, de 22 de janeiro, alterada e republicada pela Portaria n. 145-A/2011, de 6 de abril, torna-se publico que se encontram abertos procedimentos concursais comuns para ocupaçso de 3 (três) postos de trabalho, previstos e nao ocupados no Mapa de Pessoal deste Municipio, 2 modalidade de I de trabalho em funcbes publicas por tempo indeterminado, em virias Sireas de trabalho, de acordo com as referências abaixo indicadas, pelo prazo de dez (10) dias dteis, conforme avise n. 14454/2018, publicado no Diario da Republica, 2. série, n. 195, de 10 de I de 2018, a na bolsa de emprego Ref.. A: 1 Posto de trabalho de Técnico Superior Veterinaric Municipal, para o Gabinete Municipal de Veterinària; Ref. B: 1 Posto de trabalha de Assistente I àrea de Cantoneiro, para a Divisso de obras. Ambiente e Ref. C 1 Posto de trabalho de Assistente Operacional - àrea de Coveiro. para a Divisao de Obras, Ambiente e Serviços A apresentaçao das candidatura: deve ser efetvada em suporte de papel, atraves do preenchimente de formulario tipo, de utilizaçao obrigatoria, podendo ser obtido na pagina eletronica deste Municipio em hielm:perenansente.e/issures humanosi a entregar pessoalmente ou a remeter por correio registado, com aviso de receçao, dirigido ao Presidente da Camara Municipal do Porto Santo, Rua Or. Nuno Silvestre Teixeira (Edificio de Serviços Poblicos). 9400-000 Porto Santo,",
                    5: "publico (wwww.DepgOV.po, Serviços urbanos: e, Urbanos.",
                    6: "até ao termo do prazo de candidatura (24/10/2018). Municipio do Porto Santo, 10 de outubro de 2018",
                    7: "oVice-Presidente da CSmars Municipal Padie Jascm eelo - (Pedro de Vasconcelos Freitas)",
                }
            }
        }
    }
    mock_query = "Explica o seguinte documento"

    async for update in agent.analyse_document(mock_document, mock_query):
        try:
            print(update)
            if update["type"] == "step_update":
                print(f"Processing step {update['data']['step_num']}...")
                print(f"Decision: {update['data']['decision']}")
                print(f"Rationale: {update['data']['rationale']}\n")
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
