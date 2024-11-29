# import asyncio
# import os
import re
from collections import deque
from dataclasses import dataclass
from enum import Enum
from queue import Queue
from threading import Thread
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

import dspy
import numpy as np
from ocr.ExtractFromImage.main import ImageProcessor
from ocr.ExtractFromPDF.main import PDFProcessor
from rag.retriever.database.bin.utils import DenseEmbeddingModel
from rag.retriever.database.bin.utils import SparseEmbeddingModel
from rag.retriever.main import Retriever


class CognitiveAction(Enum):
    IDENTIFY_GAPS = "identify_gaps"
    GATHER_INFORMATION = "gather_information"
    SKIP_CHUNK = "skip_chunk"
    SYNTHESIZE_INFO = "synthesize_info"
    EVALUATE_ARGUMENTS = "evaluate_arguments"
    DRAW_CONCLUSIONS = "draw_conclusions"
    COMMUNICATE_FINDINGS = "communicate_findings"


@dataclass
class LegalMetadata:
    """Metadata specific to legal documents and analysis."""

    legislation_refs: List[str] = None
    precedent_refs: List[str] = None
    legal_principles: List[str] = None
    jurisdiction: Optional[str] = None

    def __post_init__(self):
        self.legislation_refs = self.legislation_refs or []
        self.precedent_refs = self.precedent_refs or []
        self.legal_principles = self.legal_principles or []


@dataclass
class Context:
    text: str
    confidence: float
    source: str
    relevance_score: float = 0.0
    emotional_valence: float = 0.0
    legal_metadata: Optional[LegalMetadata] = None


@dataclass
class KnowledgeBase:
    step_number: int
    contexts: List[Context]
    conclusion: Optional[str] = None
    confidence_score: float = 0.0
    patterns: List[str] = None
    legal_framework: Dict[str, List[str]] = None

    def __post_init__(self):
        self.patterns = self.patterns or []
        self.legal_framework = self.legal_framework or {}

    def reset(self) -> None:
        self.knowledge_bases = []
        self.current_step = 0
        self.final_conclusion = None
        self.attention_history = []
        self.pattern_memory = {}
        self.cognitive_state = CognitiveState()


@dataclass
class MemoryTrace:
    """Represents a single memory item with activation and associations."""

    content: str
    activation: float = 1.0
    associations: Dict[str, float] = None
    timestamp: float = 0.0
    source: str = ""
    relevance: float = 0.0
    legal_metadata: Optional[LegalMetadata] = None

    def __post_init__(self):
        self.associations = self.associations or {}
        self.legal_metadata = self.legal_metadata or LegalMetadata()


@dataclass
class AttentionFocus:
    """Tracks current focus of attention and relevance scores."""

    current_focus: str
    relevance_scores: Dict[str, float]
    attention_threshold: float = 0.5
    inhibited_items: List[str] = None
    legal_focus_points: List[str] = None

    def __post_init__(self):
        self.inhibited_items = self.inhibited_items or []
        self.legal_focus_points = self.legal_focus_points or []


class CognitiveState:
    """Manages the current cognitive state including working and long-term memory."""

    def __init__(self, working_memory_size: int = 5):
        self.working_memory = deque(maxlen=working_memory_size)
        self.long_term_memory: List[MemoryTrace] = []
        self.attention = AttentionFocus("", {})
        self.confidence_history: List[float] = []
        self.strategy_stack: List[str] = []
        self.emotional_state: Dict[str, float] = {"valence": 0.0, "arousal": 0.0}
        self.metacognitive_log: List[Dict] = []
        self.legal_context: Dict[str, Any] = {}

    def update_activation(self, decay_rate: float = 0.1):
        """Simulate memory decay over time."""
        for trace in self.long_term_memory:
            trace.activation *= 1 - decay_rate

    def update_emotion(self, valence: float, arousal: float):
        """Update emotional state with new values."""
        self.emotional_state["valence"] = valence
        self.emotional_state["arousal"] = arousal


class UnderstandProblem(dspy.Signature):
    """Compreende profundamente o documento e o seu contexto legal."""

    content = dspy.InputField(desc="Conteúdo do documento")
    query = dspy.InputField(desc="Questão do utilizador")

    document_purpose: str = dspy.OutputField(desc="Objetivo principal do documento")
    main_claims: List[str] = dspy.OutputField(desc="Principais argumentos apresentados")
    initial_analysis: str = dspy.OutputField(desc="Análise inicial do problema")
    emotional_assessment: Dict[str, float] = dspy.OutputField(
        desc="Avaliação emocional inicial"
    )
    legal_framework: Dict[str, List[str]] = dspy.OutputField(
        desc="Enquadramento legal identificado"
    )


class IdentifyKnowledgeGaps(dspy.Signature):
    """
    Identifica lacunas no conhecimento legal necessário para responder à questão.
    Gera no máximo duas questões para cada categoria de lacuna.
    """

    query = dspy.InputField(desc="Questão do utilizador")
    chunk = dspy.InputField(desc="Excerto do documento")
    contexts = dspy.InputField(desc="Contexto até à data")
    emotional_state = dspy.InputField(desc="Estado emocional atual")

    legal_queries: List[str] = dspy.OutputField(desc="Questões legais gerais")
    legislative_queries: List[str] = dspy.OutputField(desc="Queries sobre legislação")
    jurisprudence_queries: List[str] = dspy.OutputField(
        desc="Queries sobre jurisprudência"
    )
    confidence: float = dspy.OutputField(desc="Confiança na identificação")


class PatternRecognition(dspy.Signature):
    """Identifica padrões e analogias legais no conteúdo."""

    current_content = dspy.InputField(desc="Current content being analyzed")
    memory_traces = dspy.InputField(desc="Previous memory traces")
    emotional_context = dspy.InputField(desc="Current emotional context")

    legal_patterns: List[str] = dspy.OutputField(desc="Identified legal patterns")
    legal_principles: List[str] = dspy.OutputField(desc="Identified legal principles")
    precedents: List[str] = dspy.OutputField(desc="Relevant legal precedents")
    similarity_scores: Dict[str, float] = dspy.OutputField(
        desc="Pattern similarity scores"
    )


class ReasoningStep(dspy.Signature):
    """Determina o próximo passo cognitivo baseado no contexto legal atual."""

    query = dspy.InputField(desc="Questão do utilizador")
    context = dspy.InputField(desc="Contexto do problema até à data")
    chunk = dspy.InputField(desc="Excerto do documento")
    initial_analysis = dspy.InputField(desc="Análise inicial")
    previous_choice: CognitiveAction = dspy.InputField(desc="Passo anterior")
    emotional_state = dspy.InputField(desc="Estado emocional atual")

    action: CognitiveAction = dspy.OutputField(desc="Ação a tomar")
    confidence: float = dspy.OutputField(desc="Confiança na decisão")


class MetaCognition(dspy.Signature):
    """Minitoriza e controla os processos cognitivos com foco legal."""

    current_state = dspy.InputField(desc="Current cognitive state")
    confidence = dspy.InputField(desc="Current confidence level")
    strategy = dspy.InputField(desc="Current strategy")
    emotional_state = dspy.InputField(desc="Current emotional state")

    should_adjust: bool = dspy.OutputField(desc="Whether to adjust strategy")
    new_strategy: Optional[str] = dspy.OutputField(desc="Proposed new strategy")
    metacognitive_notes: str = dspy.OutputField(desc="Reasoning about the process")


class SynthesizeInformation(dspy.Signature):
    """Sumariza a informação legal relevante e identifica padrões."""

    contexts = dspy.InputField(desc="List of relevant contexts")
    query = dspy.InputField(desc="Original query")
    emotional_state = dspy.InputField(desc="Current emotional state")
    patterns = dspy.InputField(desc="Identified patterns")
    legal_framework = dspy.InputField(desc="Current legal framework")

    synthesis: str = dspy.OutputField(desc="Synthesized information")
    confidence: float = dspy.OutputField(desc="Confidence in synthesis")
    emotional_valence: float = dspy.OutputField(desc="Emotional valence of synthesis")
    legal_implications: List[str] = dspy.OutputField(
        desc="Legal implications identified"
    )


class EvaluateArguments(dspy.Signature):
    """Avalia os argumentos legais com base na evidência recolhida."""

    synthesis = dspy.InputField(desc="Synthesized information")
    query = dspy.InputField(desc="Original query")
    evidence = dspy.InputField(desc="Gathered evidence")
    emotional_context = dspy.InputField(desc="Emotional context")
    legal_framework = dspy.InputField(desc="Legal framework")

    evaluation: str = dspy.OutputField(desc="Evaluation of arguments")
    recommendations: List[str] = dspy.OutputField(desc="Legal recommendations")
    confidence: float = dspy.OutputField(desc="Confidence in evaluation")
    cited_legislation: List[str] = dspy.OutputField(
        desc="Cited legislation and precedents"
    )


class ChunkRelevance(dspy.Signature):
    """Avalia a relevância de um excerto do documento para a questão do utilizador."""

    query = dspy.InputField(desc="Questão do utilizador")
    chunk = dspy.InputField(desc="Excerto do documento")

    is_relevant: bool = dspy.OutputField(desc="Se o excerto é relevante")
    relevance_score: float = dspy.OutputField(desc="Pontuação de relevância (0-1)")
    reasoning: str = dspy.OutputField(desc="Razão para a relevância atribuída")


class AnswerSectionType(Enum):
    INTRODUCTION = "Introducao"
    DEVELOPMENT = "Desenvolvimento"
    CONCLUSION = "Conclusao"


class AnswerStructure:
    section: AnswerSectionType
    content: str


class DrawConclusions(dspy.Signature):
    """Sendo tu um especialista da legislação portuguesa, responde à questão baseado EXCLUSIVAMENTE no contexto fornecido. Por isso, é essencial que sigas estas instruções:
    1. Baseia a tua resposta unica e excluisivamente na informação fornecida no contexto. Não incluas interpretações pessoais, assumções ou informação que não esteja presente no contexto.
    2. Se o contexto nã contiver informação suficiente para responder à questão, deves responder com "Não é possível responder à questão com a informação fornecida". Evita fornecer informações especulativas ou respostas genéricas.
    3. A tua resposta deve estar no formato abaixo:
    - Introdução
        Dá um breve resumo da questão e do que vais abordar na resposta.
    - Desenvolvimento
        Responde à questão de forma detalhada e abrangente, utilizando vocabulário simples e claro.
        Caso a resposta seja complexa ou não objetiva, deves utilizar listas para enumerar os diversos pontos.
    - Conclusão
        Faz um resumo da resposta e conclui a questão.
    """

    evaluation = dspy.InputField(desc="Evaluation of arguments")
    contexts = dspy.InputField(desc="All relevant contexts")
    query = dspy.InputField(desc="Original query")
    emotional_state = dspy.InputField(desc="Final emotional state")
    patterns = dspy.InputField(desc="Identified patterns")
    legal_framework = dspy.InputField(desc="Complete legal framework")

    answer: List[AnswerStructure] = dspy.OutputField(desc="Final conclusion")
    confidence: float = dspy.OutputField(desc="Confidence in conclusion")
    emotional_impact: Dict[str, float] = dspy.OutputField(
        desc="Emotional impact of conclusion"
    )
    legal_opinion: str = dspy.OutputField(desc="Formal legal opinion")


class EnhancedCognitiveOCRAgent(dspy.Module):
    def __init__(self, retriever, working_memory_size: int = 5):
        super().__init__()
        self.retriever = retriever
        self.cognitive_state = CognitiveState(working_memory_size)
        self.query_relevance = QueryRelevanceCalculator()

        # Core cognitive components
        self.understanding = dspy.Predict(UnderstandProblem)
        self.gap_identifier = dspy.Predict(IdentifyKnowledgeGaps)
        self.reasoning = dspy.Predict(ReasoningStep)
        self.synthesizer = dspy.Predict(SynthesizeInformation)
        self.evaluator = dspy.Predict(EvaluateArguments)
        self.concluder = dspy.Predict(DrawConclusions)
        self.chunk_relevance = dspy.Predict(ChunkRelevance)

        # Enhanced cognitive components
        self.metacognition = dspy.Predict(MetaCognition)
        self.pattern_recognition = dspy.Predict(PatternRecognition)

        # State tracking
        self.knowledge_bases = []
        self.current_step = 0
        self.final_conclusion = None
        self.attention_history = []
        self.pattern_memory = {}
        self.legal_context_history = []

    def _get_current_context(self) -> str:
        active_contexts = []
        activation_threshold = 0.3

        for memory_trace in self.cognitive_state.working_memory:
            active_contexts.append(memory_trace.content)

        for kb in self.knowledge_bases:
            for context in kb.contexts:
                if isinstance(context, MemoryTrace):
                    if context.activation > activation_threshold:
                        active_contexts.append(context.text)
                else:
                    if context.relevance_score > activation_threshold:
                        active_contexts.append(context.text)

        seen = set()
        unique_contexts = [x for x in active_contexts if not (x in seen or seen.add(x))]

        return " ".join(unique_contexts)

    def _extract_legal_metadata(self, text: str) -> LegalMetadata:
        metadata = LegalMetadata()

        metadata.legislation_refs = self._extract_legislation_references(text)

        metadata.precedent_refs = self._extract_precedent_references(text)

        metadata.legal_principles = self._extract_legal_principles(text)

        metadata.jurisdiction = None

        return metadata

    def _extract_legislation_references(self, text: str) -> List[str]:
        """Extract references to legislation from text."""
        legislation_refs = []

        patterns = [
            r"Lei n[.º°]\s*\d+[/-]\d+",
            r"Decreto-Lei n[.º°]\s*\d+[/-]\d+",
            r"artigo \d+[.º°]",
            r"art\.\s*\d+[.º°]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            legislation_refs.extend(matches)

        return list(set(legislation_refs))

    def _extract_precedent_references(self, text: str) -> List[str]:
        """Extract references to legal precedents from text."""
        precedent_refs = []

        # Common precedent patterns
        patterns = [
            r"Acórdão\s+\d+[/-]\d+",  # Acórdão 123/2023
            r"Processo\s+\d+[/-]\d+",  # Processo 123/2023
            r"STJ\s+\d+[/-]\d+",  # STJ 123/2023
            r"TC\s+\d+[/-]\d+",  # TC 123/2023
        ]

        # Add found references
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            precedent_refs.extend(matches)

        return list(set(precedent_refs))

    def _extract_legal_principles(self, text: str) -> List[str]:
        """Extract references to legal principles from text."""
        principles = []

        # Common principle patterns
        patterns = [
            r"princípio d[aoe]\s+\w+",  # princípio da legalidade
            r"princípio\s+\w+",  # princípio constitucional
        ]

        # Add found principles
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            principles.extend(matches)

        return list(set(principles))

    def process_document(self, document: dict, query: str) -> dict:
        merged_document = self._merge_document(document)

        initial_understanding = self._initial_processing(merged_document, query)

        self._initialize_knowledge_base(initial_understanding)

        self._process_document_chunks(document, query)

        return self._generate_final_response()

    def _merge_document(self, document: dict) -> str:
        return "".join(document["page"][0]["paragraph"].values())

    def _initial_processing(self, document: str, query: str) -> Any:
        initial_understanding = self.understanding(content=document, query=query)

        patterns = self.pattern_recognition(
            current_content=initial_understanding.initial_analysis,
            memory_traces=[],
            emotional_context=self.cognitive_state.emotional_state,
        )

        self.pattern_memory["initial"] = patterns.legal_patterns
        self.legal_context_history.append(
            {
                "step": 0,
                "legal_principles": patterns.legal_principles,
                "precedents": patterns.precedents,
            }
        )

        return initial_understanding

    def _initialize_knowledge_base(self, initial_understanding: Any) -> None:
        legal_metadata = self._extract_legal_metadata(
            initial_understanding.initial_analysis
        )

        initial_kb = KnowledgeBase(
            step_number=0,
            contexts=[
                Context(
                    text=initial_understanding.initial_analysis,
                    confidence=1.0,
                    source="initial_analysis",
                    emotional_valence=0.0,
                    legal_metadata=legal_metadata,
                )
            ],
            patterns=self.pattern_memory.get("initial", []),
            legal_framework=initial_understanding.legal_framework,
        )
        self.knowledge_bases.append(initial_kb)

    async def _identify_gaps(
        self, query: str, chunk: str, kb: KnowledgeBase
    ) -> List[str]:
        """Identify knowledge gaps with stricter relevance filtering."""
        # First check if chunk is relevant enough to warrant queries
        relevance_check = self.chunk_relevance(query=query, chunk=chunk)

        print(f"Chunk relevance analysis: {relevance_check.reasoning}")

        # If not relevant enough, skip query generation
        if not relevance_check.is_relevant or relevance_check.relevance_score < 0.7:
            print(
                f"Skipping chunk - relevance score: {relevance_check.relevance_score}"
            )
            return []

        current_contexts = [c.text for c in kb.contexts]
        gaps = self.gap_identifier(
            query=query,
            chunk=chunk,
            contexts=current_contexts,
            emotional_state=self.cognitive_state.emotional_state,
        )

        # Combine and filter queries
        all_queries = []
        if gaps.legal_queries:
            # Take only top 2 most relevant legal queries
            filtered_legal = await self._filter_top_queries(
                gaps.legal_queries, query, 2
            )
            all_queries.extend(filtered_legal)

        # Prioritize and further filter queries
        prioritized_queries = self._prioritize_legal_queries(all_queries, query)

        # Take only top N most relevant queries overall
        return prioritized_queries[:3]  # Stricter limit

    async def _filter_top_queries(
        self, queries: List[str], original_query: str, top_n: int
    ) -> List[str]:
        """Filter queries to keep only the most relevant ones."""
        scored_queries = []
        for query in queries:
            relevance_score = await self.query_relevance.calculate_query_relevance(
                query, original_query
            )
            specificity_score = self._calculate_specificity(query)
            legal_score = self._calculate_legal_relevance(query)

            total_score = (
                relevance_score * 0.4 + specificity_score * 0.3 + legal_score * 0.3
            )

            scored_queries.append((total_score, query))

        return [q[1] for q in sorted(scored_queries, reverse=True)[:top_n]]

    def _generate_final_response(self) -> dict:
        all_contexts = self._get_current_context()

        all_legal_metadata = self._aggregate_legal_metadata()

        conclusion = self.concluder(
            evaluation=self.knowledge_bases[-1].contexts[-1].text
            if self.knowledge_bases[-1].contexts
            else "",
            contexts=all_contexts,
            query=self.knowledge_bases[0].contexts[0].text,
            emotional_state=self.cognitive_state.emotional_state,
            patterns=list(set([p for kb in self.knowledge_bases for p in kb.patterns])),
            legal_framework=all_legal_metadata,
        )

        return {
            "conclusion": conclusion.conclusion,
            "legal_opinion": conclusion.legal_opinion,
            "confidence": conclusion.confidence,
            "supporting_context": all_contexts,
            "emotional_impact": conclusion.emotional_impact,
            "cognitive_state": {
                "attention_history": self.attention_history,
                "metacognitive_log": self.cognitive_state.metacognitive_log,
                "identified_patterns": self.pattern_memory,
                "emotional_state": self.cognitive_state.emotional_state,
                "legal_context": self.legal_context_history,
            },
            "legal_metadata": {
                "legislation_refs": all_legal_metadata.get("legislation_refs", []),
                "precedent_refs": all_legal_metadata.get("precedent_refs", []),
                "legal_principles": all_legal_metadata.get("legal_principles", []),
                "jurisdiction": all_legal_metadata.get("jurisdiction"),
            },
        }

    def _aggregate_legal_metadata(self) -> Dict[str, Any]:
        aggregated = {
            "legislation_refs": set(),
            "precedent_refs": set(),
            "legal_principles": set(),
            "jurisdictions": set(),
        }

        for kb in self.knowledge_bases:
            for context in kb.contexts:
                if context.legal_metadata:
                    aggregated["legislation_refs"].update(
                        context.legal_metadata.legislation_refs
                    )
                    aggregated["precedent_refs"].update(
                        context.legal_metadata.precedent_refs
                    )
                    aggregated["legal_principles"].update(
                        context.legal_metadata.legal_principles
                    )
                    if context.legal_metadata.jurisdiction:
                        aggregated["jurisdictions"].add(
                            context.legal_metadata.jurisdiction
                        )

        return {
            "legislation_refs": sorted(aggregated["legislation_refs"]),
            "precedent_refs": sorted(aggregated["precedent_refs"]),
            "legal_principles": sorted(aggregated["legal_principles"]),
            "jurisdictions": sorted(aggregated["jurisdictions"]),
            "summary": {
                "total_legislation": len(aggregated["legislation_refs"]),
                "total_precedents": len(aggregated["precedent_refs"]),
                "total_principles": len(aggregated["legal_principles"]),
                "jurisdictions_count": len(aggregated["jurisdictions"]),
            },
        }

    def _recognize_patterns(self, content: str) -> Any:
        memory_traces = [
            trace.content for trace in self.cognitive_state.long_term_memory
        ]

        recognized_patterns = self.pattern_recognition(
            current_content=content,
            memory_traces=memory_traces,
            emotional_context=self.cognitive_state.emotional_state,
        )

        self.cognitive_state.metacognitive_log.append(
            {
                "action": "pattern_recognition",
                "identified_patterns": recognized_patterns.legal_patterns,
                "identified_principles": recognized_patterns.legal_principles,
                "identified_precedents": recognized_patterns.precedents,
                "similarity_scores": recognized_patterns.similarity_scores,
            }
        )

        return recognized_patterns

    def _process_chunk(self, chunk: str, query: str) -> None:
        """Process chunk with enhanced progression tracking."""
        self.current_step += 1
        current_kb = KnowledgeBase(
            step_number=self.current_step, contexts=[], patterns=[], legal_framework={}
        )

        # Initial legal analysis
        patterns = self._recognize_patterns(chunk)
        current_kb.patterns.extend(patterns.legal_patterns)
        legal_metadata = self._extract_legal_metadata(chunk)

        # Track processing state
        processing_state = {
            "identified_gaps": False,
            "performed_synthesis": False,
            "evaluated_arguments": False,
            "draw_conclusions": False,
        }

        depth_limit = 0
        previous_choice = None

        while depth_limit < 5:
            action = self._determine_next_action(chunk, query, previous_choice)
            print(f"Chosen action: {action} for step {self.current_step}")

            # Update processing state
            if action == CognitiveAction.IDENTIFY_GAPS:
                if processing_state["identified_gaps"]:
                    # Skip redundant gap identification
                    action = CognitiveAction.SYNTHESIZE_INFO
                processing_state["identified_gaps"] = True
            elif action == CognitiveAction.SYNTHESIZE_INFO:
                processing_state["performed_synthesis"] = True
            elif action == CognitiveAction.EVALUATE_ARGUMENTS:
                processing_state["evaluated_arguments"] = True
            elif action == CognitiveAction.DRAW_CONCLUSIONS:
                processing_state["draw_conclusions"] = True
                break

            success_metrics = self._execute_cognitive_action(
                action, chunk, query, current_kb, legal_metadata
            )

            self._update_metacognitive_state(action, success_metrics)
            self._update_attention_focus(chunk, success_metrics, legal_metadata)

            # Force progression if stuck
            if depth_limit >= 3 and not processing_state["performed_synthesis"]:
                action = CognitiveAction.SYNTHESIZE_INFO

            previous_choice = action
            depth_limit += 1

        self.knowledge_bases.append(current_kb)

    def _gather_information(self, queries: List[str]) -> List[Context]:
        contexts = []
        queue = Queue()
        thread_pool = []

        def query_worker(query):
            try:
                if self.retriever:
                    results = self.retriever.query(query, 3)
                    queue.put((query, results))
            except Exception as e:
                print(f"Error querying for {query}: {e}")

        queries = list(set(queries))

        for query in queries:
            print(f"Querying for: {query}")
            t = Thread(target=query_worker, args=(query,))
            thread_pool.append(t)
            t.start()

        for thread in thread_pool:
            thread.join()

        while not queue.empty():
            query, results = queue.get()
            for result in results:
                legal_metadata = self._extract_legal_metadata(result["text"])
                context = Context(
                    text=result["text"],
                    confidence=result["score"],
                    source=f"retrieval_{query}",
                    relevance_score=result["score"],
                    legal_metadata=legal_metadata,
                )
                contexts.append(context)

                self.cognitive_state.metacognitive_log.append(
                    {
                        "action": "information_retrieval",
                        "query": query,
                        "relevance_score": result["score"],
                        "legal_metadata_found": bool(legal_metadata),
                    }
                )

        return contexts

    def _update_metacognitive_state(
        self, action: CognitiveAction, success_metrics: Dict[str, float]
    ) -> None:
        metacognitive_assessment = self.metacognition(
            current_state=self._get_current_context(),
            confidence=success_metrics.get("confidence", 0.0),
            strategy=str(action),
            emotional_state=self.cognitive_state.emotional_state,
        )

        if metacognitive_assessment.should_adjust:
            self.cognitive_state.strategy_stack.append(
                metacognitive_assessment.new_strategy
            )

        self.cognitive_state.confidence_history.append(
            success_metrics.get("confidence", 0.0)
        )

        self.cognitive_state.metacognitive_log.append(
            {
                "action": action,
                "confidence": success_metrics.get("confidence", 0.0),
                "relevance": success_metrics.get("relevance", 0.0),
                "should_adjust_strategy": metacognitive_assessment.should_adjust,
                "new_strategy": metacognitive_assessment.new_strategy,
                "metacognitive_notes": metacognitive_assessment.metacognitive_notes,
                "step_number": self.current_step,
            }
        )

    def _determine_next_action(
        self, chunk: str, query: str, previous_step: Optional[CognitiveAction]
    ) -> CognitiveAction:
        """Determine next cognitive action with enhanced progression logic."""
        current_context = self._get_current_context()
        initial_analysis = (
            self.knowledge_bases[0].contexts[0].text
            if self.knowledge_bases and self.knowledge_bases[0].contexts
            else ""
        )

        consecutive_gaps = sum(
            1
            for log in self.cognitive_state.metacognitive_log[-3:]
            if log.get("action") == CognitiveAction.IDENTIFY_GAPS
        )

        if consecutive_gaps >= 2:
            if any(
                ctx.source == "retrieval"
                for kb in self.knowledge_bases
                for ctx in kb.contexts
            ):
                return CognitiveAction.SYNTHESIZE_INFO
            else:
                return CognitiveAction.SKIP_CHUNK

        decision = self.reasoning(
            query=query,
            chunk=chunk,
            context=current_context,
            initial_analysis=initial_analysis,
            previous_choice=previous_step,
            emotional_state=self.cognitive_state.emotional_state,
        )

        if previous_step == CognitiveAction.SYNTHESIZE_INFO:
            return CognitiveAction.EVALUATE_ARGUMENTS
        elif previous_step == CognitiveAction.EVALUATE_ARGUMENTS:
            if self._should_draw_conclusions():
                return CognitiveAction.DRAW_CONCLUSIONS

        return decision.action

    def _should_draw_conclusions(self) -> bool:
        """Determine if enough analysis has been done to draw conclusions."""
        if not self.knowledge_bases:
            return False

        # Check for sufficient context gathering
        has_synthesis = any(
            ctx.source == "synthesis"
            for kb in self.knowledge_bases
            for ctx in kb.contexts
        )
        has_evaluation = any(
            ctx.source == "evaluation"
            for kb in self.knowledge_bases
            for ctx in kb.contexts
        )

        # Check confidence levels
        recent_confidence = [
            log.get("confidence", 0.0)
            for log in self.cognitive_state.metacognitive_log[-3:]
        ]
        high_confidence = sum(conf > 0.7 for conf in recent_confidence) >= 2

        return has_synthesis and has_evaluation and high_confidence

    def _process_document_chunks(self, document: dict, query: str) -> None:
        for page_num, page in document.get("page", {}).items():
            print(f"Processing page {page_num}")

            sorted_paragraphs = sorted(
                page["paragraph"].items(), key=lambda x: int(x[0])
            )

            for para_num, chunk in sorted_paragraphs:
                print(f"Processing paragraph {para_num}")

                if not chunk.strip():
                    continue

                self._process_chunk(chunk, query)

        self.cognitive_state.update_activation()

        self.cognitive_state.metacognitive_log.append(
            {
                "action": "document_processing_complete",
                "total_chunks_processed": sum(
                    len(page["paragraph"]) for page in document.get("page", {}).values()
                ),
                "knowledge_bases_created": len(self.knowledge_bases),
                "final_memory_trace_count": len(self.cognitive_state.long_term_memory),
            }
        )

    def _execute_cognitive_action(
        self,
        action: CognitiveAction,
        chunk: str,
        query: str,
        kb: KnowledgeBase,
        legal_metadata: LegalMetadata,
    ) -> Dict[str, float]:
        success_metrics = {"confidence": 0.0, "relevance": 0.0}

        if action == CognitiveAction.IDENTIFY_GAPS:
            success_metrics = self._handle_gap_identification(
                chunk, query, kb, legal_metadata
            )
        elif action == CognitiveAction.SYNTHESIZE_INFO:
            success_metrics = self._handle_synthesis(kb, query, legal_metadata)
        elif action == CognitiveAction.EVALUATE_ARGUMENTS:
            success_metrics = self._handle_evaluation(kb, query, legal_metadata)

        return success_metrics

    def _synthesize_information(self, kb: KnowledgeBase, query: str) -> Any:
        # Get all relevant contexts
        contexts = [c.text for c in kb.contexts]

        # Only proceed with synthesis if we have contexts
        if not contexts:
            return None

        # Perform synthesis with legal context
        synthesis = self.synthesizer(
            contexts=contexts,
            query=query,
            emotional_state=self.cognitive_state.emotional_state,
            patterns=kb.patterns,
            legal_framework=kb.legal_framework,
        )

        # Log synthesis in metacognitive state
        self.cognitive_state.metacognitive_log.append(
            {
                "action": "synthesis",
                "patterns_used": kb.patterns,
                "contexts_synthesized": len(contexts),
                "confidence": synthesis.confidence,
                "legal_implications_identified": synthesis.legal_implications,
            }
        )

        if synthesis.confidence > 0.7:
            self.cognitive_state.working_memory.append(
                MemoryTrace(
                    content=synthesis.synthesis,
                    activation=1.0,
                    source="synthesis",
                    relevance=synthesis.confidence,
                )
            )

        return synthesis

    def _handle_synthesis(
        self, kb: KnowledgeBase, query: str, legal_metadata: LegalMetadata
    ) -> Dict[str, float]:
        synthesis = self._synthesize_information(kb, query)

        kb.contexts.append(
            Context(
                text=synthesis.synthesis,
                confidence=synthesis.confidence,
                source="synthesis",
                emotional_valence=synthesis.emotional_valence,
                legal_metadata=legal_metadata,
            )
        )

        return {
            "confidence": synthesis.confidence,
            "relevance": 0.8,
            "emotional_valence": synthesis.emotional_valence,
        }

    def _handle_evaluation(
        self, kb: KnowledgeBase, query: str, legal_metadata: LegalMetadata
    ) -> Dict[str, float]:
        latest_synthesis = next(
            (c.text for c in reversed(kb.contexts) if c.source == "synthesis"), None
        )

        if not latest_synthesis:
            return {"confidence": 0.0, "relevance": 0.0}

        evaluation = self.evaluator(
            synthesis=latest_synthesis,
            query=query,
            evidence=[c.text for c in kb.contexts],
            emotional_context=self.cognitive_state.emotional_state,
            legal_framework=kb.legal_framework,
        )

        kb.contexts.append(
            Context(
                text=evaluation.evaluation,
                confidence=evaluation.confidence,
                source="evaluation",
                legal_metadata=legal_metadata,
            )
        )

        return {
            "confidence": evaluation.confidence,
            "relevance": 0.7,
            "recommendation_strength": len(evaluation.recommendations) / 5.0,
        }

    def _handle_gap_identification(
        self, chunk: str, query: str, kb: KnowledgeBase, legal_metadata: LegalMetadata
    ) -> Dict[str, float]:
        gaps = self._identify_gaps(query, chunk, kb)
        retrieved_info = self._gather_information(gaps)

        # Add legal metadata to retrieved information
        for info in retrieved_info:
            info.legal_metadata = self._extract_legal_metadata(info.text)

        kb.contexts.extend(retrieved_info)

        confidence = self._calculate_gap_resolution_confidence(gaps, retrieved_info)
        legal_relevance = self._calculate_legal_relevance_score(
            retrieved_info, legal_metadata
        )

        return {
            "confidence": confidence,
            "relevance": legal_relevance,
            "legal_coverage": self._calculate_legal_coverage(retrieved_info),
        }

    def _calculate_gap_resolution_confidence(
        self, gaps: List[str], retrieved_info: List[Context]
    ) -> float:
        if not gaps:
            return 1.0

        gap_resolution_scores = []

        for gap in gaps:
            gap_score = 0.0
            relevant_contexts = 0

            for info in retrieved_info:
                relevance = self._calculate_gap_context_relevance(gap, info)
                if relevance > 0:
                    gap_score += relevance
                    relevant_contexts += 1

            if relevant_contexts > 0:
                gap_resolution_scores.append(gap_score / relevant_contexts)
            else:
                gap_resolution_scores.append(0.0)

        if gap_resolution_scores:
            return sum(gap_resolution_scores) / len(gap_resolution_scores)
        return 0.0

    def _calculate_gap_context_relevance(self, gap: str, context: Context) -> float:
        relevance_score = 0.0

        relevance_score += context.relevance_score * 0.3

        if context.legal_metadata:
            if any(
                ref in gap.lower() for ref in context.legal_metadata.legislation_refs
            ):
                relevance_score += 0.3

            if any(
                principle in gap.lower()
                for principle in context.legal_metadata.legal_principles
            ):
                relevance_score += 0.2

            if any(
                precedent in gap.lower()
                for precedent in context.legal_metadata.precedent_refs
            ):
                relevance_score += 0.2

        return min(1.0, relevance_score)

    def _calculate_legal_coverage(self, contexts: List[Context]) -> float:
        coverage_metrics = {"legislation": 0.0, "precedents": 0.0, "principles": 0.0}

        for context in contexts:
            if context.legal_metadata:
                if context.legal_metadata.legislation_refs:
                    coverage_metrics["legislation"] += 0.3
                if context.legal_metadata.precedent_refs:
                    coverage_metrics["precedents"] += 0.3
                if context.legal_metadata.legal_principles:
                    coverage_metrics["principles"] += 0.4

        return min(1.0, sum(coverage_metrics.values()))

    def _calculate_legal_relevance_score(
        self, contexts: List[Context], legal_metadata: LegalMetadata
    ) -> float:
        relevance_score = 0.0

        for context in contexts:
            if context.legal_metadata:
                matching_legislation = len(
                    set(context.legal_metadata.legislation_refs).intersection(
                        legal_metadata.legislation_refs
                    )
                )
                relevance_score += matching_legislation * 0.2

                matching_precedents = len(
                    set(context.legal_metadata.precedent_refs).intersection(
                        legal_metadata.precedent_refs
                    )
                )
                relevance_score += matching_precedents * 0.2

                matching_principles = len(
                    set(context.legal_metadata.legal_principles).intersection(
                        legal_metadata.legal_principles
                    )
                )
                relevance_score += matching_principles * 0.2

                if (
                    context.legal_metadata.jurisdiction
                    and context.legal_metadata.jurisdiction
                    == legal_metadata.jurisdiction
                ):
                    relevance_score += 0.2

        return min(1.0, relevance_score)

    def _update_attention_focus(
        self, content: str, metrics: Dict[str, float], legal_metadata: LegalMetadata
    ) -> None:
        relevance_threshold = 0.5
        if metrics["relevance"] > relevance_threshold:
            self.cognitive_state.attention.current_focus = content
            self.cognitive_state.attention.relevance_scores[content] = metrics[
                "relevance"
            ]

            # Track legal focus points
            if legal_metadata:
                self.cognitive_state.attention.legal_focus_points.extend(
                    [
                        *legal_metadata.legislation_refs,
                        *legal_metadata.precedent_refs,
                        *legal_metadata.legal_principles,
                    ]
                )

        self.attention_history.append(
            {
                "focus": self.cognitive_state.attention.current_focus,
                "relevance": metrics["relevance"],
                "legal_focus_points": self.cognitive_state.attention.legal_focus_points,
                "timestamp": self.current_step,
            }
        )

    def reset(self) -> None:
        self.knowledge_bases = []
        self.current_step = 0
        self.final_conclusion = None
        self.attention_history = []
        self.pattern_memory = {}
        self.cognitive_state = CognitiveState()
        self.legal_context_history = []


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
    llm = dspy.LM(
        "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", api_key=api_key
    )
    dspy.configure(lm=llm)

    retriever = Retriever()

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

    query = "O seguinte documento é válido de forma a extinguir a associação das testemunhas de jeová?"

    agent = EnhancedCognitiveOCRAgent(retriever=retriever)

    result = agent.process_document(document=mock_document, query=query)
    print(result)
    print(result.get("conclusion"))
    print(result.get("confidence"))
    print(result.get("legal_opinion"))

    # return {
    #         "conclusion": conclusion.conclusion,
    #         "legal_opinion": conclusion.legal_opinion,
    #         "confidence": conclusion.confidence,
    #         "supporting_context": all_contexts,
    #         "emotional_impact": conclusion.emotional_impact,
    #         "cognitive_state": {
    #             "attention_history": self.attention_history,
    #             "metacognitive_log": self.cognitive_state.metacognitive_log,
    #             "identified_patterns": self.pattern_memory,
    #             "emotional_state": self.cognitive_state.emotional_state,
    #             "legal_context": self.legal_context_history
    #         },
    #         "legal_metadata": {
    #             "legislation_refs": all_legal_metadata.get("legislation_refs", []),
    #             "precedent_refs": all_legal_metadata.get("precedent_refs", []),
    #             "legal_principles": all_legal_metadata.get("legal_principles", []),
    #             "jurisdiction": all_legal_metadata.get("jurisdiction")
    #         }
    #     }


import torch
from torch.nn.functional import cosine_similarity


class QueryRelevanceCalculator:
    def __init__(self, cache_dir: str = ".cache"):
        # Initialize embedding models
        self.dense_model = DenseEmbeddingModel(cache_dir=cache_dir)
        self.sparse_model = SparseEmbeddingModel(cache_dir=cache_dir)

    async def calculate_dense_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity using dense embeddings."""
        # Get embeddings for both queries
        emb1 = await self.dense_model.aembed_query(query1)
        emb2 = await self.dense_model.aembed_query(query2)

        # Convert to tensors
        emb1_tensor = torch.tensor(emb1)
        emb2_tensor = torch.tensor(emb2)

        # Calculate cosine similarity
        similarity = cosine_similarity(
            emb1_tensor.unsqueeze(0), emb2_tensor.unsqueeze(0)
        ).item()
        return float(similarity)

    async def calculate_sparse_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity using sparse embeddings."""
        # Get sparse embeddings
        sparse_vec1 = await self.sparse_model.aembed_query(query1)
        sparse_vec2 = await self.sparse_model.aembed_query(query2)

        # Convert sparse dictionaries to sets for overlap calculation
        keys1 = set(sparse_vec1.keys())
        keys2 = set(sparse_vec2.keys())

        # Calculate Jaccard similarity for token overlap
        intersection = len(keys1.intersection(keys2))
        union = len(keys1.union(keys2))

        if union == 0:
            return 0.0

        # Calculate weighted similarity considering token frequencies
        weighted_similarity = 0.0
        for key in keys1.intersection(keys2):
            weighted_similarity += min(sparse_vec1[key], sparse_vec2[key])

        total_weights = sum(sparse_vec1.values()) + sum(sparse_vec2.values())
        if total_weights > 0:
            weighted_similarity = 2 * weighted_similarity / total_weights

        # Combine Jaccard and weighted similarities
        similarity = 0.5 * (intersection / union) + 0.5 * weighted_similarity
        return float(similarity)

    async def calculate_query_relevance(self, query: str, original_query: str) -> float:
        """Calculate hybrid similarity score combining dense and sparse embeddings."""
        # Get both similarity scores
        dense_score = await self.calculate_dense_similarity(query, original_query)
        sparse_score = await self.calculate_sparse_similarity(query, original_query)

        # Combine scores with weights
        # Give more weight to dense embeddings for semantic understanding
        # but maintain significant weight for sparse to catch specific terms
        final_score = (dense_score * 0.7) + (sparse_score * 0.3)

        return final_score

    async def get_most_relevant_queries(
        self,
        candidate_queries: List[str],
        original_query: str,
        top_k: int = 3,
        threshold: float = 0.5,
    ) -> List[Tuple[str, float]]:
        """Get the most relevant queries from a list of candidates."""
        scores = []
        for query in candidate_queries:
            score = await self.calculate_query_relevance(query, original_query)
            if score >= threshold:
                scores.append((query, score))

        # Sort by score and return top k
        return sorted(scores, key=lambda x: x[1], reverse=True)[:top_k]


if __name__ == "__main__":
    main()
