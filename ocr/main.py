# from dataclasses import dataclass, field
# from enum import Enum
# from typing import List, Dict, Optional, Set, Tuple, Any
# import dspy
# from concurrent.futures import ThreadPoolExecutor
# from collections import defaultdict
# import re
# import torch
# from torch.nn.functional import cosine_similarity
# import asyncio
# from rag.retriever.database.bin.utils import DenseEmbeddingModel, SparseEmbeddingModel
# from rag.retriever.main import Retriever
# from ocr.ExtractFromImage.main import ImageProcessor
# from ocr.ExtractFromPDF.main import PDFProcessor

# class CognitiveAction(Enum):
#     ANALYZE = "analyze"
#     SYNTHESIZE = "synthesize"
#     EVALUATE = "evaluate"
#     CONCLUDE = "conclude"

# @dataclass
# class LegalContext:
#     references: List[str] = field(default_factory=list)
#     precedents: List[str] = field(default_factory=list)
#     principles: List[str] = field(default_factory=list)
#     jurisdiction: Optional[str] = None
#     confidence: float = 0.0

#     def merge(self, other: 'LegalContext') -> 'LegalContext':
#         return LegalContext(
#             references=list(set(self.references + other.references)),
#             precedents=list(set(self.precedents + other.precedents)),
#             principles=list(set(self.principles + other.principles)),
#             jurisdiction=self.jurisdiction or other.jurisdiction,
#             confidence=max(self.confidence, other.confidence)
#         )

#     def __iter__(self):
#         return iter([
#             ('references', self.references),
#             ('precedents', self.precedents),
#             ('principles', self.principles),
#             ('jurisdiction', self.jurisdiction),
#             ('confidence', self.confidence)
#         ])
# @dataclass
# class AnalysisResult:
#     content: str
#     legal_context: LegalContext
#     confidence: float
#     source: str
#     relevance: float = 0.0
#     patterns: List[str] = field(default_factory=list)
#     metadata: Dict[str, Any] = field(default_factory=dict)

#     def validate(self) -> bool:
#         return bool(self.content and self.legal_context and 0 <= self.confidence <= 1)

# class CognitiveState:
#     def __init__(self):
#         self.contexts: List[AnalysisResult] = []
#         self.current_action: CognitiveAction = CognitiveAction.ANALYZE
#         self.confidence_history: List[float] = []
#         self.legal_patterns: Dict[str, float] = {}
#         self.processing_errors: List[str] = []

#     def add_context(self, result: AnalysisResult):
#         if result.validate():
#             self.contexts.append(result)
#             self.confidence_history.append(result.confidence)

#     def get_average_confidence(self) -> float:
#         return sum(self.confidence_history) / len(self.confidence_history) if self.confidence_history else 0.0

# class RelevanceCalculator:
#     def __init__(self, dense_model: DenseEmbeddingModel, sparse_model: SparseEmbeddingModel):
#         self.dense_model = dense_model
#         self.sparse_model = sparse_model
#         self._cache: Dict[str, torch.Tensor] = {}
#         self.chunk_size = 512

#     def chunk_text(self, text: str) -> List[str]:
#         return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

#     async def calculate_relevance(self, text1: str, text2: str) -> float:
#         try:
#             dense_score = await self.calculate_dense_similarity(text1, text2)
#             sparse_score = await self.calculate_sparse_similarity(text1, text2)
#             return 0.7 * dense_score + 0.3 * sparse_score
#         except Exception as e:
#             print(f"Error calculating relevance: {e}")
#             return 0.0

#     async def calculate_dense_similarity(self, text1: str, text2: str) -> float:
#         try:
#             # Chunk texts and get embeddings for each chunk
#             chunks1 = self.chunk_text(text1)
#             chunks2 = self.chunk_text(text2)

#             emb1 = await self._get_chunked_embedding(chunks1, 'dense')
#             emb2 = await self._get_chunked_embedding(chunks2, 'dense')

#             similarity = cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0))
#             return float(similarity)
#         except Exception as e:
#             print(f"Dense similarity error: {e}")
#             return 0.0

#     async def calculate_sparse_similarity(self, text1: str, text2: str) -> float:
#         try:
#             chunks1 = self.chunk_text(text1)
#             chunks2 = self.chunk_text(text2)

#             vec1 = await self._get_chunked_sparse_embedding(chunks1)
#             vec2 = await self._get_chunked_sparse_embedding(chunks2)
#             return self._calculate_weighted_similarity(vec1, vec2)
#         except Exception as e:
#             print(f"Sparse similarity error: {e}")
#             return 0.0

#     async def _get_chunked_embedding(self, chunks: List[str], embed_type: str) -> torch.Tensor:
#         embeddings = []
#         for chunk in chunks:
#             cache_key = f"{embed_type}_{hash(chunk)}"
#             if cache_key not in self._cache:
#                 embedding = await self.dense_model.aembed_query(chunk)
#                 self._cache[cache_key] = torch.tensor(embedding)
#             embeddings.append(self._cache[cache_key])

#         # Average embeddings if multiple chunks
#         if embeddings:
#             return torch.mean(torch.stack(embeddings), dim=0)
#         return torch.zeros(self.dense_model.embedding_dim)

#     async def _get_chunked_sparse_embedding(self, chunks: List[str]) -> Dict[str, float]:
#         combined_vec = defaultdict(float)
#         for chunk in chunks:
#             vec = await self.sparse_model.aembed_query(chunk)
#             for key, value in vec.items():
#                 combined_vec[key] += value

#         # Normalize values
#         if combined_vec:
#             total = sum(combined_vec.values())
#             if total > 0:
#                 combined_vec = {k: v/total for k, v in combined_vec.items()}

#         return dict(combined_vec)

#     def _calculate_weighted_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
#         keys1, keys2 = set(vec1.keys()), set(vec2.keys())
#         intersection = keys1.intersection(keys2)
#         union = keys1.union(keys2)

#         if not union:
#             return 0.0

#         weighted_sim = sum(min(vec1.get(k, 0), vec2.get(k, 0)) for k in intersection)
#         total_weights = sum(vec1.values()) + sum(vec2.values())

#         if total_weights == 0:
#             return 0.0

#         weighted_sim = 2 * weighted_sim / total_weights
#         jaccard_sim = len(intersection) / len(union)
#         return 0.5 * (jaccard_sim + weighted_sim)

#     def clear_cache(self):
#         self._cache.clear()

# # Enhanced prediction signatures with comprehensive fields
# class DocumentAnalyzer(dspy.Signature):
#     """Analyzes document content in relation to query."""
#     content = dspy.InputField(desc="Document content to analyze")
#     query = dspy.InputField(desc="Query to analyze against")

#     analysis: str = dspy.OutputField(desc="Detailed analysis of content")
#     confidence: float = dspy.OutputField(desc="Confidence in analysis")
#     relevance: float = dspy.OutputField(desc="Relevance to query")
#     legal_implications: List[str] = dspy.OutputField(desc="Identified legal implications")
#     metadata: Dict[str, Any] = dspy.OutputField(desc="Additional analysis metadata")

# class InformationSynthesizer(dspy.Signature):
#     """Synthesizes multiple analysis results."""
#     contexts = dspy.InputField(desc="List of analysis contexts")
#     query = dspy.InputField(desc="Original query")
#     legal_contexts = dspy.InputField(desc="Legal contexts from analysis")

#     content: str = dspy.OutputField(desc="Synthesized content")
#     confidence: float = dspy.OutputField(desc="Synthesis confidence")
#     patterns: List[str] = dspy.OutputField(desc="Identified patterns")
#     unified_context: Dict[str, Any] = dspy.OutputField(desc="Unified legal context")

# class ArgumentEvaluator(dspy.Signature):
#     """Evaluates synthesized arguments."""
#     synthesis = dspy.InputField(desc="Synthesized content")
#     query = dspy.InputField(desc="Original query")
#     legal_context = dspy.InputField(desc="Legal context")
#     patterns = dspy.InputField(desc="Identified patterns")

#     evaluation: str = dspy.OutputField(desc="Evaluation results")
#     confidence: float = dspy.OutputField(desc="Evaluation confidence")
#     recommendations: List[str] = dspy.OutputField(desc="Legal recommendations")
#     critical_points: List[str] = dspy.OutputField(desc="Critical evaluation points")

# class ConclusionGenerator(dspy.Signature):
#     """Generates final conclusions."""
#     evaluation = dspy.InputField(desc="Evaluation results")
#     query = dspy.InputField(desc="Original query")
#     legal_context = dspy.InputField(desc="Legal context")
#     recommendations = dspy.InputField(desc="Legal recommendations")

#     conclusion: str = dspy.OutputField(desc="Final conclusion")
#     confidence: float = dspy.OutputField(desc="Conclusion confidence")
#     action_items: List[str] = dspy.OutputField(desc="Recommended actions")
#     summary: Dict[str, Any] = dspy.OutputField(desc="Conclusion summary")

# class LegalContextExtractor:
#     """Extracts legal context from text using pattern matching."""

#     def __init__(self):
#         self.patterns = {
#             'references': [
#                 r'Lei n[.º°]\s*\d+[/-]\d+',
#                 r'Decreto-Lei n[.º°]\s*\d+[/-]\d+',
#                 r'artigo \d+[.º°]',
#                 r'art\.\s*\d+[.º°]',
#             ],
#             'precedents': [
#                 r'Acórdão\s+\d+[/-]\d+',
#                 r'Processo\s+\d+[/-]\d+',
#                 r'STJ\s+\d+[/-]\d+',
#                 r'TC\s+\d+[/-]\d+',
#             ],
#             'principles': [
#                 r'princípio d[aoe]\s+\w+',
#                 r'princípio\s+\w+',
#             ]
#         }

#     def extract_context(self, text: str) -> LegalContext:
#         try:
#             refs = self._extract_patterns(text, self.patterns['references'])
#             precs = self._extract_patterns(text, self.patterns['precedents'])
#             prins = self._extract_patterns(text, self.patterns['principles'])

#             return LegalContext(
#                 references=refs,
#                 precedents=precs,
#                 principles=prins,
#                 confidence=self._calculate_confidence(refs, precs, prins)
#             )
#         except Exception as e:
#             print(f"Error extracting legal context: {e}")
#             return LegalContext()

#     def _extract_patterns(self, text: str, patterns: List[str]) -> List[str]:
#         results = set()
#         for pattern in patterns:
#             matches = re.findall(pattern, text, re.IGNORECASE)
#             results.update(matches)
#         return list(results)

#     def _calculate_confidence(self, refs: List[str], precs: List[str], prins: List[str]) -> float:
#         total_items = len(refs) + len(precs) + len(prins)
#         if total_items == 0:
#             return 0.0
#         weights = {
#             'references': 0.4,
#             'precedents': 0.3,
#             'principles': 0.3
#         }
#         score = (
#             (1 if refs else 0) * weights['references'] +
#             (1 if precs else 0) * weights['precedents'] +
#             (1 if prins else 0) * weights['principles']
#         )
#         return score

# class CognitiveOCR(dspy.Module):
#     def __init__(self, retriever, dense_model=None, sparse_model=None):
#         super().__init__()
#         self.retriever = retriever
#         self.state = CognitiveState()
#         self.relevance_calculator = RelevanceCalculator(dense_model, sparse_model)
#         self.legal_extractor = LegalContextExtractor()

#         self.analyzer = dspy.Predict(DocumentAnalyzer)
#         self.synthesizer = dspy.Predict(InformationSynthesizer)
#         self.evaluator = dspy.Predict(ArgumentEvaluator)
#         self.concluder = dspy.Predict(ConclusionGenerator)

#         self.metrics = defaultdict(int)

#     async def process_document(self, document: dict, query: str) -> dict:
#         try:
#             merged_content = self._merge_document(document)
#             initial_analysis = await self._analyze_document(merged_content, query)
#             self.state.add_context(initial_analysis)

#             chunks = self._get_document_chunks(document)
#             chunk_results = await self._process_chunks(chunks, query)

#             synthesis = await self._synthesize_results(chunk_results, query)
#             evaluation = await self._evaluate_analysis(synthesis, query)
#             conclusion = await self._generate_conclusion(evaluation, query)

#             return await self._prepare_response(conclusion)

#         except Exception as e:
#             self.state.processing_errors.append(str(e))
#             return self._create_error_response(str(e))

#     def _merge_document(self, document: dict) -> str:
#         pages = document.get("page", {}).values()
#         paragraphs = [
#             para.strip()
#             for page in pages
#             for para in page.get("paragraph", {}).values()
#             if para.strip()
#         ]
#         return " ".join(paragraphs)

#     def _get_document_chunks(self, document: dict) -> List[str]:
#         chunks = []
#         for page in document.get("page", {}).values():
#             paragraphs = sorted(
#                 page.get("paragraph", {}).items(),
#                 key=lambda x: int(x[0])
#             )
#             chunks.extend(para for _, para in paragraphs if para.strip())
#         return chunks

#     async def _analyze_document(self, content: str, query: str) -> AnalysisResult:
#         self.metrics['analyses'] += 1
#         analysis = self.analyzer(content=content, query=query)
#         legal_context = self.legal_extractor.extract_context(content)

#         return AnalysisResult(
#             content=analysis.analysis,
#             legal_context=legal_context,
#             confidence=analysis.confidence,
#             source="initial_analysis",
#             relevance=analysis.relevance,
#             patterns=[],
#             metadata=analysis.metadata
#         )

#     async def _process_chunks(self, chunks: List[str], query: str) -> List[AnalysisResult]:
#         async def process_chunk(chunk: str) -> Optional[AnalysisResult]:
#             relevance = await self.relevance_calculator.calculate_relevance(chunk, query)
#             if relevance < 0.3:
#                 return None

#             analysis = await self._analyze_document(chunk, query)
#             return analysis if analysis.confidence > 0.5 else None

#         results = []
#         async with asyncio.TaskGroup() as group:
#             tasks = [group.create_task(process_chunk(chunk)) for chunk in chunks]

#         for task in tasks:
#             if result := task.result():
#                 results.append(result)

#         return results

#     async def _synthesize_results(self, results: List[AnalysisResult], query: str) -> Optional[AnalysisResult]:
#         if not results:
#             return None

#         self.metrics['syntheses'] += 1
#         synthesis = self.synthesizer(
#             contexts=[r.content for r in results],
#             query=query,
#             legal_contexts=[r.legal_context for r in results]
#         )

#         combined_context = self._merge_legal_contexts(
#             [r.legal_context for r in results]
#         )

#         return AnalysisResult(
#             content=synthesis.content,
#             legal_context=combined_context,
#             confidence=synthesis.confidence,
#             source="synthesis",
#             relevance=max(r.relevance for r in results),
#             patterns=synthesis.patterns
#         )

#     def _merge_legal_contexts(self, contexts: List[LegalContext]) -> LegalContext:
#         if not contexts:
#             return LegalContext()

#         result = contexts[0]
#         for context in contexts[1:]:
#             result = result.merge(context)
#         return result

#     async def _evaluate_analysis(self, synthesis: AnalysisResult, query: str) -> Optional[AnalysisResult]:
#         if not synthesis:
#             return None

#         self.metrics['evaluations'] += 1
#         evaluation = self.evaluator(
#             synthesis=synthesis.content,
#             query=query,
#             legal_context=synthesis.legal_context,
#             patterns=synthesis.patterns
#         )

#         return AnalysisResult(
#             content=evaluation.evaluation,
#             legal_context=synthesis.legal_context,
#             confidence=evaluation.confidence,
#             source="evaluation",
#             patterns=synthesis.patterns,
#             metadata={'recommendations': evaluation.recommendations}
#         )

#     async def _generate_conclusion(self, evaluation: AnalysisResult, query: str) -> Optional[AnalysisResult]:
#         if not evaluation:
#             return None

#         self.metrics['conclusions'] += 1
#         conclusion = self.concluder(
#             evaluation=evaluation.content,
#             query=query,
#             legal_context=evaluation.legal_context,
#             recommendations=evaluation.metadata.get('recommendations', [])
#         )

#         return AnalysisResult(
#             content=conclusion.conclusion,
#             legal_context=evaluation.legal_context,
#             confidence=conclusion.confidence,
#             source="conclusion",
#             patterns=evaluation.patterns,
#             metadata={
#                 'action_items': conclusion.action_items,
#                 'summary': conclusion.summary
#             }
#         )

#     async def _prepare_response(self, conclusion: AnalysisResult) -> dict:
#         if not conclusion:
#             return self._create_error_response("Failed to generate conclusion")

#         return {
#             "status": "success",
#             "conclusion": conclusion.content,
#             "confidence": conclusion.confidence,
#             "legal_context": {
#                 "references": conclusion.legal_context.references,
#                 "precedents": conclusion.legal_context.precedents,
#                 "principles": conclusion.legal_context.principles,
#                 "jurisdiction": conclusion.legal_context.jurisdiction
#             },
#             "recommendations": conclusion.metadata.get('action_items', []),
#             "metrics": dict(self.metrics),
#             "errors": self.state.processing_errors
#         }

#     def _create_error_response(self, error_message: str) -> dict:
#         return {
#             "status": "error",
#             "error": error_message,
#             "partial_results": [
#                 {
#                     "content": ctx.content,
#                     "confidence": ctx.confidence,
#                     "source": ctx.source
#                 }
#                 for ctx in self.state.contexts
#             ],
#             "metrics": dict(self.metrics)
#         }

#     def reset(self):
#         self.state = CognitiveState()
#         self.metrics.clear()
#         self.relevance_calculator.clear_cache()

# # Utils for processing different document types
# class DocumentProcessor:
#     def __init__(self):
#         self.image_processor = ImageProcessor()
#         self.pdf_processor = PDFProcessor()

#     async def process(self, file_path: str) -> dict:
#         if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
#             return await self.image_processor.process(file_path)
#         elif file_path.lower().endswith('.pdf'):
#             return await self.pdf_processor.process(file_path)
#         else:
#             raise ValueError(f"Unsupported file type: {file_path}")


# # Example usage
# async def main():
#     import os
#     from dotenv import load_dotenv

#     load_dotenv()
#     api_key = os.getenv("TOGETHER_API_KEY")
#     llm = dspy.LM(
#         "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", api_key=api_key
#     )
#     dspy.configure(lm=llm)

#     dense_model = DenseEmbeddingModel(cache_dir=".cache")
#     sparse_model = SparseEmbeddingModel(cache_dir=".cache")
#     retriever = Retriever()
#     doc_processor = DocumentProcessor()

#     retriever = Retriever()

#     ocr = CognitiveOCR(
#         retriever=retriever,
#         dense_model=dense_model,
#         sparse_model=sparse_model
#     )

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

#     query = "O seguinte documento é válido de forma a extinguir a associação das testemunhas de jeová?"

#     result = await ocr.process_document(mock_document, query)


#     if result["status"] == "success":
#         print(f"Conclusion: {result['conclusion']}")
#         print(f"Confidence: {result['confidence']}")
#         print("Legal Context:", result["legal_context"])
#         if result["recommendations"]:
#             print("Recommendations:", result["recommendations"])
#     else:
#         print(f"Error: {result['error']}")
#         if result["partial_results"]:
#             print("Partial results available:", len(result["partial_results"]))

# if __name__ == "__main__":
#     asyncio.run(main())
#     # return {
#     #         "conclusion": conclusion.conclusion,
#     #         "legal_opinion": conclusion.legal_opinion,
#     #         "confidence": conclusion.confidence,
#     #         "supporting_context": all_contexts,
#     #         "emotional_impact": conclusion.emotional_impact,
#     #         "cognitive_state": {
#     #             "attention_history": self.attention_history,
#     #             "metacognitive_log": self.cognitive_state.metacognitive_log,
#     #             "identified_patterns": self.pattern_memory,
#     #             "emotional_state": self.cognitive_state.emotional_state,
#     #             "legal_context": self.legal_context_history
#     #         },
#     #         "legal_metadata": {
#     #             "legislation_refs": all_legal_metadata.get("legislation_refs", []),
#     #             "precedent_refs": all_legal_metadata.get("precedent_refs", []),
#     #             "legal_principles": all_legal_metadata.get("legal_principles", []),
#     #             "jurisdiction": all_legal_metadata.get("jurisdiction")
#     #         }
#     #     }

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set, Tuple, Any
import dspy
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import re
import torch
from torch.nn.functional import cosine_similarity
import asyncio
from rag.retriever.database.bin.utils import DenseEmbeddingModel, SparseEmbeddingModel
from rag.retriever.main import Retriever
from ocr.ExtractFromImage.main import ImageProcessor
from ocr.ExtractFromPDF.main import PDFProcessor


class CognitiveAction(Enum):
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    EVALUATE = "evaluate"
    CONCLUDE = "conclude"


@dataclass
class KnowledgeGap:
    question: str
    context: str
    confidence: float = 0.0
    is_addressed: bool = False
    retrieved_context: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class LegalContext:
    references: List[str] = field(default_factory=list)
    precedents: List[str] = field(default_factory=list)
    principles: List[str] = field(default_factory=list)
    jurisdiction: Optional[str] = None
    confidence: float = 0.0
    knowledge_gaps: List[KnowledgeGap] = field(default_factory=list)

    def merge(self, other: "LegalContext") -> "LegalContext":
        merged = LegalContext(
            references=list(set(self.references + other.references)),
            precedents=list(set(self.precedents + other.precedents)),
            principles=list(set(self.principles + other.principles)),
            jurisdiction=self.jurisdiction or other.jurisdiction,
            confidence=max(self.confidence, other.confidence),
            knowledge_gaps=self.knowledge_gaps + other.knowledge_gaps,
        )
        return merged

    def __iter__(self):
        return iter(
            [
                ("references", self.references),
                ("precedents", self.precedents),
                ("principles", self.principles),
                ("jurisdiction", self.jurisdiction),
                ("confidence", self.confidence),
                ("knowledge_gaps", self.knowledge_gaps),
            ]
        )


@dataclass
class AnalysisResult:
    content: str
    legal_context: LegalContext
    confidence: float
    source: str
    relevance: float = 0.0
    patterns: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    knowledge_gaps: List[KnowledgeGap] = field(default_factory=list)

    def validate(self) -> bool:
        return bool(
            self.content
            and self.legal_context
            and 0 <= self.confidence <= 1
            and 0 <= self.relevance <= 1
        )


class CognitiveState:
    def __init__(self):
        self.contexts: List[AnalysisResult] = []
        self.current_action: CognitiveAction = CognitiveAction.ANALYZE
        self.confidence_history: List[float] = []
        self.legal_patterns: Dict[str, float] = {}
        self.processing_errors: List[str] = []
        self.knowledge_gaps: List[KnowledgeGap] = []

    def add_context(self, result: AnalysisResult):
        if result.validate():
            self.contexts.append(result)
            self.confidence_history.append(result.confidence)
            self.knowledge_gaps.extend(result.knowledge_gaps)

    def get_average_confidence(self) -> float:
        return (
            sum(self.confidence_history) / len(self.confidence_history)
            if self.confidence_history
            else 0.0
        )

    def get_unaddressed_gaps(self) -> List[KnowledgeGap]:
        return [gap for gap in self.knowledge_gaps if not gap.is_addressed]


class RelevanceCalculator:
    def __init__(
        self, dense_model: DenseEmbeddingModel, sparse_model: SparseEmbeddingModel
    ):
        self.dense_model = dense_model
        self.sparse_model = sparse_model
        self._cache: Dict[str, torch.Tensor] = {}
        self.chunk_size = 512

    def chunk_text(self, text: str) -> List[str]:
        return [
            text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)
        ]

    async def calculate_relevance(self, text1: str, text2: str) -> float:
        try:
            dense_score = await self.calculate_dense_similarity(text1, text2)
            sparse_score = await self.calculate_sparse_similarity(text1, text2)
            return 0.7 * dense_score + 0.3 * sparse_score
        except Exception as e:
            print(f"Error calculating relevance: {e}")
            return 0.0

    async def calculate_dense_similarity(self, text1: str, text2: str) -> float:
        try:
            # Chunk texts and get embeddings for each chunk
            chunks1 = self.chunk_text(text1)
            chunks2 = self.chunk_text(text2)

            emb1 = await self._get_chunked_embedding(chunks1, "dense")
            emb2 = await self._get_chunked_embedding(chunks2, "dense")

            similarity = cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0))
            return float(similarity)
        except Exception as e:
            print(f"Dense similarity error: {e}")
            return 0.0

    async def calculate_sparse_similarity(self, text1: str, text2: str) -> float:
        try:
            chunks1 = self.chunk_text(text1)
            chunks2 = self.chunk_text(text2)

            vec1 = await self._get_chunked_sparse_embedding(chunks1)
            vec2 = await self._get_chunked_sparse_embedding(chunks2)
            return self._calculate_weighted_similarity(vec1, vec2)
        except Exception as e:
            print(f"Sparse similarity error: {e}")
            return 0.0

    async def _get_chunked_embedding(
        self, chunks: List[str], embed_type: str
    ) -> torch.Tensor:
        embeddings = []
        for chunk in chunks:
            cache_key = f"{embed_type}_{hash(chunk)}"
            if cache_key not in self._cache:
                embedding = await self.dense_model.aembed_query(chunk)
                self._cache[cache_key] = torch.tensor(embedding)
            embeddings.append(self._cache[cache_key])

        # Average embeddings if multiple chunks
        if embeddings:
            return torch.mean(torch.stack(embeddings), dim=0)
        return torch.zeros(self.dense_model.embedding_dim)

    async def _get_chunked_sparse_embedding(
        self, chunks: List[str]
    ) -> Dict[str, float]:
        combined_vec = defaultdict(float)
        for chunk in chunks:
            vec = await self.sparse_model.aembed_query(chunk)
            for key, value in vec.items():
                combined_vec[key] += value

        # Normalize values
        if combined_vec:
            total = sum(combined_vec.values())
            if total > 0:
                combined_vec = {k: v / total for k, v in combined_vec.items()}

        return dict(combined_vec)

    def _calculate_weighted_similarity(
        self, vec1: Dict[str, float], vec2: Dict[str, float]
    ) -> float:
        keys1, keys2 = set(vec1.keys()), set(vec2.keys())
        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)

        if not union:
            return 0.0

        weighted_sim = sum(min(vec1.get(k, 0), vec2.get(k, 0)) for k in intersection)
        total_weights = sum(vec1.values()) + sum(vec2.values())

        if total_weights == 0:
            return 0.0

        weighted_sim = 2 * weighted_sim / total_weights
        jaccard_sim = len(intersection) / len(union)
        return 0.5 * (jaccard_sim + weighted_sim)

    def clear_cache(self):
        self._cache.clear()


class LegalContextExtractor:
    """Extracts legal context from text using pattern matching."""

    def __init__(self):
        self.patterns = {
            "references": [
                r"Lei n[.º°]\s*\d+[/-]\d+",
                r"Decreto-Lei n[.º°]\s*\d+[/-]\d+",
                r"artigo \d+[.º°]",
                r"art\.\s*\d+[.º°]",
            ],
            "precedents": [
                r"Acórdão\s+\d+[/-]\d+",
                r"Processo\s+\d+[/-]\d+",
                r"STJ\s+\d+[/-]\d+",
                r"TC\s+\d+[/-]\d+",
            ],
            "principles": [
                r"princípio d[aoe]\s+\w+",
                r"princípio\s+\w+",
            ],
        }

    def extract_context(self, text: str) -> LegalContext:
        try:
            refs = self._extract_patterns(text, self.patterns["references"])
            precs = self._extract_patterns(text, self.patterns["precedents"])
            prins = self._extract_patterns(text, self.patterns["principles"])

            return LegalContext(
                references=refs,
                precedents=precs,
                principles=prins,
                confidence=self._calculate_confidence(refs, precs, prins),
            )
        except Exception as e:
            print(f"Error extracting legal context: {e}")
            return LegalContext()

    def _extract_patterns(self, text: str, patterns: List[str]) -> List[str]:
        results = set()
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            results.update(matches)
        return list(results)

    def _calculate_confidence(
        self, refs: List[str], precs: List[str], prins: List[str]
    ) -> float:
        total_items = len(refs) + len(precs) + len(prins)
        if total_items == 0:
            return 0.0
        weights = {"references": 0.4, "precedents": 0.3, "principles": 0.3}
        score = (
            (1 if refs else 0) * weights["references"]
            + (1 if precs else 0) * weights["precedents"]
            + (1 if prins else 0) * weights["principles"]
        )
        return score


class GapIdentifier(dspy.Signature):
    """Identifies knowledge gaps in a legal context."""

    context = dspy.InputField(desc="Current legal context")
    query = dspy.InputField(desc="Original query")
    legal_references = dspy.InputField(desc="Known legal references")
    legal_precedents = dspy.InputField(desc="Known legal precedents")
    legal_principles = dspy.InputField(desc="Known legal principles")

    gaps: List[str] = dspy.OutputField(desc="List of identified knowledge gaps")
    confidence: float = dspy.OutputField(desc="Confidence in identified gaps")


class QueryRefiner(dspy.Signature):
    """Refines a knowledge gap into a focused search query."""

    question = dspy.InputField(desc="Knowledge gap question")
    legal_context = dspy.InputField(desc="Legal context")

    refined_query: str = dspy.OutputField(desc="Refined search query")
    search_priority: float = dspy.OutputField(desc="Priority score for this query")


class QueryGenerator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.gap_identifier = dspy.Predict(GapIdentifier)
        self.query_refiner = dspy.Predict(QueryRefiner)

    async def generate_queries(
        self, context: str, query: str, legal_context: LegalContext
    ) -> List[KnowledgeGap]:
        gaps = self.gap_identifier(
            context=context,
            query=query,
            legal_references=legal_context.references,
            legal_precedents=legal_context.precedents,
            legal_principles=legal_context.principles,
        )

        knowledge_gaps = []
        for gap in gaps.gaps:
            refined = self.query_refiner(question=gap, legal_context=str(legal_context))

            knowledge_gaps.append(
                KnowledgeGap(
                    question=refined.refined_query,
                    context=context,
                    confidence=gaps.confidence,
                    retrieved_context=[],
                )
            )

        return knowledge_gaps[:3]


class RelevanceSignature(dspy.Signature):
    """Evaluates text relevance for legal queries."""

    chunk = dspy.InputField(desc="Text chunk to evaluate")
    query = dspy.InputField(desc="Original query")
    legal_context = dspy.InputField(desc="Legal context")

    score: float = dspy.OutputField(desc="Relevance score (0-1)")
    reasoning: str = dspy.OutputField(desc="Detailed reasoning")
    key_points: List[str] = dspy.OutputField(desc="Key legal points identified")


class RelevanceEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.evaluator = dspy.Predict(RelevanceSignature)

    def evaluate(
        self, chunk: str, query: str, legal_context: Optional[LegalContext] = None
    ) -> Tuple[float, str, List[str]]:
        evaluation = self.evaluator(
            chunk=chunk,
            query=query,
            legal_context=str(legal_context) if legal_context else "None",
        )

        return (float(evaluation.score), evaluation.reasoning, evaluation.key_points)

    def evaluate_retrieved_context(
        self, retrieved_context: List[Dict[str, Any]], original_gap: KnowledgeGap
    ) -> float:
        total_score = 0.0
        for ctx in retrieved_context:
            relevance = self.evaluator(
                chunk=ctx["text"], query=original_gap.question, legal_context="None"
            )
            total_score += float(relevance.score)

        return (
            min(1.0, total_score / len(retrieved_context)) if retrieved_context else 0.0
        )


class KnowledgeEnhancer:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever
        self.relevance_evaluator = RelevanceEvaluator()

    async def enhance_knowledge(
        self, gap: KnowledgeGap, top_k: int = 2
    ) -> KnowledgeGap:
        print("Retrieving additional information...")
        try:
            results = await self.retriever.query(gap.question, top_k)
            gap.retrieved_context = results

            # Evaluate how well the retrieved information addresses the gap
            gap.confidence = self.relevance_evaluator.evaluate_retrieved_context(
                results, gap
            )
            gap.is_addressed = gap.confidence > 0.7

            return gap
        except Exception as e:
            print(f"Error enhancing knowledge: {e}")
            return gap

    async def process_gaps(
        self, gaps: List[KnowledgeGap], max_parallel: int = 3
    ) -> List[KnowledgeGap]:
        """Process multiple knowledge gaps in parallel."""
        enhanced_gaps = []
        async with asyncio.TaskGroup() as group:
            tasks = [
                group.create_task(self.enhance_knowledge(gap))
                for gap in gaps[:max_parallel]
            ]

        for task in tasks:
            if result := task.result():
                enhanced_gaps.append(result)

        return enhanced_gaps


class CognitiveOCR(dspy.Module):
    def __init__(self, retriever, dense_model=None, sparse_model=None):
        super().__init__()
        self.retriever = retriever
        self.state = CognitiveState()
        self.relevance_calculator = RelevanceCalculator(dense_model, sparse_model)
        self.legal_extractor = LegalContextExtractor()
        self.query_generator = QueryGenerator()
        self.knowledge_enhancer = KnowledgeEnhancer(retriever)

        self.analyzer = dspy.Predict(DocumentAnalyzer)
        self.synthesizer = dspy.Predict(InformationSynthesizer)
        self.evaluator = dspy.Predict(ArgumentEvaluator)
        self.concluder = dspy.Predict(ConclusionGenerator)

        self.metrics = defaultdict(int)

    async def process_document(self, document: dict, query: str) -> dict:
        try:
            # Initial analysis
            merged_content = self._merge_document(document)
            initial_analysis = await self._analyze_document(merged_content, query)
            self.state.add_context(initial_analysis)

            # Process chunks and identify knowledge gaps
            chunks = self._get_document_chunks(document)
            chunk_results = await self._process_chunks(chunks, query)

            # Process identified knowledge gaps
            await self._process_knowledge_gaps()

            # Generate final analysis
            synthesis = await self._synthesize_results(chunk_results, query)
            evaluation = await self._evaluate_analysis(synthesis, query)
            conclusion = await self._generate_conclusion(evaluation, query)
            print(synthesis)
            print(evaluation)
            print(conclusion)
            return await self._prepare_response(conclusion)

        except Exception as e:
            self.state.processing_errors.append(str(e))
            return self._create_error_response(str(e))

    async def _process_chunks(
        self, chunks: List[str], query: str
    ) -> List[AnalysisResult]:
        async def process_chunk(chunk: str) -> Optional[AnalysisResult]:
            relevance, reasoning, key_points = self.relevance_evaluator.evaluate(
                chunk, query, None
            )

            if relevance < 0.3:
                return None

            # Generate queries for knowledge gaps
            legal_context = self.legal_extractor.extract_context(chunk)
            knowledge_gaps = await self.query_generator.generate_queries(
                chunk, query, legal_context
            )

            # Analyze with identified gaps
            analysis = await self._analyze_document(chunk, query)
            analysis.knowledge_gaps = knowledge_gaps

            return analysis if analysis.confidence > 0.5 else None

        results = []
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(process_chunk(chunk)) for chunk in chunks]

        for task in tasks:
            if result := task.result():
                results.append(result)
                self.state.knowledge_gaps.extend(result.knowledge_gaps)

        return results

    async def _process_knowledge_gaps(self):
        """Process and enhance knowledge for identified gaps."""
        unaddressed_gaps = self.state.get_unaddressed_gaps()
        if unaddressed_gaps:
            enhanced_gaps = await self.knowledge_enhancer.process_gaps(unaddressed_gaps)
            self.state.knowledge_gaps = enhanced_gaps

    async def _synthesize_results(
        self, results: List[AnalysisResult], query: str
    ) -> Optional[AnalysisResult]:
        if not results:
            return None

        # Combine all contexts including retrieved information
        combined_context = self._merge_contexts(results)
        enhanced_context = self._enhance_with_retrieved_info(combined_context)

        synthesis = self.synthesizer(
            contexts=[r.content for r in results],
            query=query,
            legal_contexts=[r.legal_context for r in results],
            enhanced_context=enhanced_context,
        )

        return AnalysisResult(
            content=synthesis.content,
            legal_context=self._merge_legal_contexts(
                [r.legal_context for r in results]
            ),
            confidence=synthesis.confidence,
            source="synthesis",
            relevance=max(r.relevance for r in results),
            patterns=synthesis.patterns,
            knowledge_gaps=self.state.knowledge_gaps,
        )

    def _merge_contexts(self, results: List[AnalysisResult]) -> str:
        return "\n\n".join(r.content for r in results)

    def _enhance_with_retrieved_info(self, context: str) -> str:
        retrieved_info = []
        for gap in self.state.knowledge_gaps:
            if gap.is_addressed and gap.retrieved_context:
                retrieved_info.extend(ctx["text"] for ctx in gap.retrieved_context)

        if retrieved_info:
            return f"{context}\n\nAdditional Research:\n" + "\n\n".join(retrieved_info)
        return context

    def _merge_document(self, document: dict) -> str:
        pages = document.get("page", {}).values()
        paragraphs = [
            para.strip()
            for page in pages
            for para in page.get("paragraph", {}).values()
            if para.strip()
        ]
        return " ".join(paragraphs)

    def _get_document_chunks(self, document: dict) -> List[str]:
        chunks = []
        for page in document.get("page", {}).values():
            paragraphs = sorted(
                page.get("paragraph", {}).items(), key=lambda x: int(x[0])
            )
            chunks.extend(para for _, para in paragraphs if para.strip())
        return chunks

    async def _prepare_response(self, conclusion: AnalysisResult) -> dict:
        if not conclusion:
            return self._create_error_response("Failed to generate conclusion")

        return {
            "status": "success",
            "conclusion": conclusion.content,
            "confidence": conclusion.confidence,
            "legal_context": {
                "references": conclusion.legal_context.references,
                "precedents": conclusion.legal_context.precedents,
                "principles": conclusion.legal_context.principles,
                "jurisdiction": conclusion.legal_context.jurisdiction,
            },
            "knowledge_gaps": [
                {
                    "question": gap.question,
                    "is_addressed": gap.is_addressed,
                    "confidence": gap.confidence,
                }
                for gap in self.state.knowledge_gaps
            ],
            "recommendations": conclusion.metadata.get("action_items", []),
            "metrics": dict(self.metrics),
            "errors": self.state.processing_errors,
        }

    def _create_error_response(self, error_message: str) -> dict:
        return {
            "status": "error",
            "error": error_message,
            "partial_results": [
                {
                    "content": ctx.content,
                    "confidence": ctx.confidence,
                    "source": ctx.source,
                }
                for ctx in self.state.contexts
            ],
            "metrics": dict(self.metrics),
        }

    async def _analyze_document(self, content: str, query: str) -> AnalysisResult:
        self.metrics["analyses"] += 1
        analysis = self.analyzer(content=content, query=query)
        legal_context = self.legal_extractor.extract_context(content)

        return AnalysisResult(
            content=analysis.analysis,
            legal_context=legal_context,
            confidence=analysis.confidence,
            source="initial_analysis",
            relevance=analysis.relevance,
            patterns=[],
            metadata=analysis.metadata,
        )

    async def _process_chunks(
        self, chunks: List[str], query: str
    ) -> List[AnalysisResult]:
        async def process_chunk(chunk: str) -> Optional[AnalysisResult]:
            relevance = await self.relevance_calculator.calculate_relevance(
                chunk, query
            )
            if relevance < 0.3:
                return None

            analysis = await self._analyze_document(chunk, query)
            return analysis if analysis.confidence > 0.5 else None

        results = []
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(process_chunk(chunk)) for chunk in chunks]

        for task in tasks:
            if result := task.result():
                results.append(result)

        return results

    async def _synthesize_results(
        self, results: List[AnalysisResult], query: str
    ) -> Optional[AnalysisResult]:
        if not results:
            return None

        self.metrics["syntheses"] += 1
        synthesis = self.synthesizer(
            contexts=[r.content for r in results],
            query=query,
            legal_contexts=[r.legal_context for r in results],
        )

        combined_context = self._merge_legal_contexts(
            [r.legal_context for r in results]
        )

        return AnalysisResult(
            content=synthesis.content,
            legal_context=combined_context,
            confidence=synthesis.confidence,
            source="synthesis",
            relevance=max(r.relevance for r in results),
            patterns=synthesis.patterns,
        )

    def _merge_legal_contexts(self, contexts: List[LegalContext]) -> LegalContext:
        if not contexts:
            return LegalContext()

        result = contexts[0]
        for context in contexts[1:]:
            result = result.merge(context)
        return result

    async def _evaluate_analysis(
        self, synthesis: AnalysisResult, query: str
    ) -> Optional[AnalysisResult]:
        if not synthesis:
            return None

        self.metrics["evaluations"] += 1
        evaluation = self.evaluator(
            synthesis=synthesis.content,
            query=query,
            legal_context=synthesis.legal_context,
            patterns=synthesis.patterns,
        )

        return AnalysisResult(
            content=evaluation.evaluation,
            legal_context=synthesis.legal_context,
            confidence=evaluation.confidence,
            source="evaluation",
            patterns=synthesis.patterns,
            metadata={"recommendations": evaluation.recommendations},
        )

    async def _generate_conclusion(
        self, evaluation: AnalysisResult, query: str
    ) -> Optional[AnalysisResult]:
        if not evaluation:
            return None

        self.metrics["conclusions"] += 1
        conclusion = self.concluder(
            evaluation=evaluation.content,
            query=query,
            legal_context=evaluation.legal_context,
            recommendations=evaluation.metadata.get("recommendations", []),
        )

        return AnalysisResult(
            content=conclusion.conclusion,
            legal_context=evaluation.legal_context,
            confidence=conclusion.confidence,
            source="conclusion",
            patterns=evaluation.patterns,
            metadata={
                "action_items": conclusion.action_items,
                "summary": conclusion.summary,
            },
        )

    async def _prepare_response(self, conclusion: AnalysisResult) -> dict:
        if not conclusion:
            return self._create_error_response("Failed to generate conclusion")

        return {
            "status": "success",
            "conclusion": conclusion.content,
            "confidence": conclusion.confidence,
            "legal_context": {
                "references": conclusion.legal_context.references,
                "precedents": conclusion.legal_context.precedents,
                "principles": conclusion.legal_context.principles,
                "jurisdiction": conclusion.legal_context.jurisdiction,
            },
            "recommendations": conclusion.metadata.get("action_items", []),
            "metrics": dict(self.metrics),
            "errors": self.state.processing_errors,
        }

    def _create_error_response(self, error_message: str) -> dict:
        return {
            "status": "error",
            "error": error_message,
            "partial_results": [
                {
                    "content": ctx.content,
                    "confidence": ctx.confidence,
                    "source": ctx.source,
                }
                for ctx in self.state.contexts
            ],
            "metrics": dict(self.metrics),
        }

    def reset(self):
        self.state = CognitiveState()
        self.metrics.clear()
        self.relevance_calculator.clear_cache()


class DocumentAnalyzer(dspy.Signature):
    content = dspy.InputField(desc="Document content to analyze")
    query = dspy.InputField(desc="Original query")

    analysis: str = dspy.OutputField(desc="Analysis result")
    confidence: float = dspy.OutputField(desc="Analysis confidence")
    relevance: float = dspy.OutputField(desc="Query relevance")
    metadata: Dict[str, Any] = dspy.OutputField(desc="Additional metadata")


class InformationSynthesizer(dspy.Signature):
    """Synthesizes multiple analysis results."""

    contexts = dspy.InputField(desc="List of contexts to synthesize")
    query = dspy.InputField(desc="Original query")
    legal_contexts = dspy.InputField(desc="Legal contexts")
    enhanced_context = dspy.InputField(
        desc="Enhanced context with retrieved information"
    )

    content: str = dspy.OutputField(desc="Synthesized content")
    confidence: float = dspy.OutputField(desc="Synthesis confidence")
    patterns: List[str] = dspy.OutputField(desc="Identified patterns")


class ArgumentEvaluator(dspy.Signature):
    """Evaluates the analysis results."""

    content = dspy.InputField(desc="Content to evaluate")
    query = dspy.InputField(desc="Original query")
    legal_context = dspy.InputField(desc="Legal context")
    patterns = dspy.InputField(desc="Identified patterns")
    additional_context = dspy.InputField(desc="Additional retrieved context")

    evaluation: str = dspy.OutputField(desc="Evaluation result")
    confidence: float = dspy.OutputField(desc="Evaluation confidence")
    recommendations: List[str] = dspy.OutputField(desc="Recommendations")


class ConclusionGenerator(dspy.Signature):
    evaluation = dspy.InputField(desc="Evaluation content")
    query = dspy.InputField(desc="Original query")
    legal_context = dspy.InputField(desc="Legal context")
    recommendations = dspy.InputField(desc="Recommendations")

    conclusion: str = dspy.OutputField(desc="Final conclusion")
    confidence: float = dspy.OutputField(desc="Conclusion confidence")
    action_items: List[str] = dspy.OutputField(desc="Action items")
    summary: Dict[str, Any] = dspy.OutputField(desc="Summary")


# Example usage
async def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("TOGETHER_API_KEY")

    # Initialize models
    llm = dspy.LM(
        "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", api_key=api_key
    )
    dspy.configure(lm=llm)

    dense_model = DenseEmbeddingModel(cache_dir=".cache")
    sparse_model = SparseEmbeddingModel(cache_dir=".cache")
    retriever = Retriever()

    # Initialize OCR with components
    ocr = CognitiveOCR(
        retriever=retriever, dense_model=dense_model, sparse_model=sparse_model
    )

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

    query = "Analisa legalmente o seguinte documento"

    result = await ocr.process_document(mock_document, query)
    print(result)
    # Print results
    if result["status"] == "success":
        print(f"Conclusion: {result['conclusion']}")
        print(f"Confidence: {result['confidence']}")
        print("\nLegal Context:", result["legal_context"])
        print("\nKnowledge Gaps Addressed:")
        for gap in result["knowledge_gaps"]:
            print(
                f"- {gap['question']} (Addressed: {gap['is_addressed']}, Confidence: {gap['confidence']})"
            )
        if result["recommendations"]:
            print("\nRecommendations:", result["recommendations"])
    else:
        print(f"Error: {result['error']}")
        if result["partial_results"]:
            print("Partial results available:", len(result["partial_results"]))


if __name__ == "__main__":
    asyncio.run(main())
