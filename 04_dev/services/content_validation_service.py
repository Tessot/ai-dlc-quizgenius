#!/usr/bin/env python3
"""
Content Quality Validation Service for QuizGenius MVP
This service validates PDF content quality for educational use and question generation.
Implements Step 2.2.2: Content Quality Validation (US-4.1.2 - 3 points)
Author: Expert Software Engineer
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from services.bedrock_service import BedrockService, BedrockServiceError
from utils.dynamodb_utils import get_current_timestamp, generate_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentValidationResult:
    """Result of content validation process"""
    validation_id: str
    is_suitable: bool
    quality_score: float  # 0.0 to 10.0
    content_length: int
    word_count: int
    readability_score: float
    educational_indicators: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    validation_timestamp: datetime

@dataclass
class ContentAnalysis:
    """Detailed analysis of content characteristics"""
    structure_score: float
    vocabulary_complexity: float
    educational_keywords_count: int
    sentence_complexity: float
    paragraph_structure: Dict[str, Any]
    topic_indicators: List[str]
    content_type: str  # 'textbook', 'lecture_notes', 'article', 'other'

class ContentValidationError(Exception):
    """Custom exception for content validation errors"""
    pass

class ContentValidationService:
    """
    Service for validating PDF content quality for educational use
    """
    
    def __init__(self):
        """Initialize the content validation service"""
        try:
            self.bedrock_service = BedrockService()
            
            # Validation thresholds
            self.min_word_count = 50
            self.min_quality_score = 3.0
            self.min_educational_keywords = 2
            
            # Educational keyword categories
            self.educational_keywords = {
                'academic': [
                    'definition', 'concept', 'theory', 'principle', 'method', 'analysis',
                    'research', 'study', 'experiment', 'hypothesis', 'conclusion', 'evidence',
                    'example', 'illustration', 'demonstrate', 'explain', 'describe', 'compare'
                ],
                'instructional': [
                    'chapter', 'section', 'lesson', 'unit', 'objective', 'learning',
                    'understand', 'knowledge', 'skill', 'practice', 'exercise', 'problem',
                    'solution', 'answer', 'question', 'review', 'summary', 'key points'
                ],
                'scientific': [
                    'observation', 'data', 'measurement', 'calculation', 'formula', 'equation',
                    'variable', 'constant', 'function', 'relationship', 'correlation', 'causation',
                    'model', 'simulation', 'prediction', 'validation', 'verification'
                ],
                'analytical': [
                    'evaluate', 'assess', 'critique', 'analyze', 'synthesize', 'interpret',
                    'infer', 'deduce', 'conclude', 'argue', 'justify', 'support', 'evidence'
                ]
            }
            
            logger.info("ContentValidationService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ContentValidationService: {str(e)}")
            raise ContentValidationError(f"Service initialization failed: {str(e)}")
    
    def validate_content(self, content: str, filename: str = None) -> ContentValidationResult:
        """
        Validate content quality for educational use
        
        Args:
            content: Text content to validate
            filename: Optional filename for context
            
        Returns:
            ContentValidationResult with validation details
        """
        validation_id = generate_id('validation')
        start_time = datetime.now()
        
        logger.info(f"Starting content validation {validation_id}")
        
        try:
            # Basic content analysis
            basic_analysis = self._analyze_basic_metrics(content)
            
            # Detailed content analysis
            detailed_analysis = self._analyze_content_structure(content)
            
            # Educational content detection
            educational_analysis = self._analyze_educational_content(content)
            
            # Quality scoring
            quality_score = self._calculate_quality_score(
                basic_analysis, detailed_analysis, educational_analysis
            )
            
            # Determine suitability
            is_suitable = self._determine_suitability(
                quality_score, basic_analysis, educational_analysis
            )
            
            # Generate issues and recommendations
            issues, recommendations = self._generate_feedback(
                basic_analysis, detailed_analysis, educational_analysis, quality_score
            )
            
            # Create result
            result = ContentValidationResult(
                validation_id=validation_id,
                is_suitable=is_suitable,
                quality_score=quality_score,
                content_length=basic_analysis['content_length'],
                word_count=basic_analysis['word_count'],
                readability_score=detailed_analysis.sentence_complexity,
                educational_indicators=educational_analysis,
                issues=issues,
                recommendations=recommendations,
                metadata={
                    'filename': filename,
                    'basic_analysis': basic_analysis,
                    'detailed_analysis': detailed_analysis.__dict__,
                    'processing_time_seconds': (datetime.now() - start_time).total_seconds()
                },
                validation_timestamp=start_time
            )
            
            logger.info(f"Content validation completed: score {quality_score:.1f}, suitable: {is_suitable}")
            return result
            
        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}")
            raise ContentValidationError(f"Validation failed: {str(e)}")
    
    def _analyze_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Analyze basic content metrics"""
        try:
            content_clean = content.strip()
            
            return {
                'content_length': len(content_clean),
                'word_count': len(content_clean.split()),
                'sentence_count': len(re.findall(r'[.!?]+', content_clean)),
                'paragraph_count': len([p for p in content_clean.split('\n\n') if p.strip()]),
                'line_count': len(content_clean.split('\n')),
                'average_word_length': sum(len(word) for word in content_clean.split()) / len(content_clean.split()) if content_clean.split() else 0
            }
            
        except Exception as e:
            logger.error(f"Basic metrics analysis failed: {str(e)}")
            return {
                'content_length': 0,
                'word_count': 0,
                'sentence_count': 0,
                'paragraph_count': 0,
                'line_count': 0,
                'average_word_length': 0
            }
    
    def _analyze_content_structure(self, content: str) -> ContentAnalysis:
        """Analyze content structure and complexity"""
        try:
            # Structure analysis
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            sentences = re.findall(r'[^.!?]*[.!?]', content)
            
            # Calculate structure score
            structure_score = self._calculate_structure_score(paragraphs, sentences)
            
            # Vocabulary complexity
            words = re.findall(r'\b\w+\b', content.lower())
            vocab_complexity = self._calculate_vocabulary_complexity(words)
            
            # Sentence complexity
            sentence_complexity = self._calculate_sentence_complexity(sentences)
            
            # Educational keywords
            educational_count = self._count_educational_keywords(content.lower())
            
            # Paragraph structure analysis
            paragraph_analysis = {
                'count': len(paragraphs),
                'average_length': sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
                'length_variance': self._calculate_paragraph_variance(paragraphs)
            }
            
            # Topic indicators
            topic_indicators = self._extract_topic_indicators(content)
            
            # Content type detection
            content_type = self._detect_content_type(content, educational_count)
            
            return ContentAnalysis(
                structure_score=structure_score,
                vocabulary_complexity=vocab_complexity,
                educational_keywords_count=educational_count,
                sentence_complexity=sentence_complexity,
                paragraph_structure=paragraph_analysis,
                topic_indicators=topic_indicators,
                content_type=content_type
            )
            
        except Exception as e:
            logger.error(f"Content structure analysis failed: {str(e)}")
            return ContentAnalysis(
                structure_score=0.0,
                vocabulary_complexity=0.0,
                educational_keywords_count=0,
                sentence_complexity=0.0,
                paragraph_structure={'count': 0, 'average_length': 0, 'length_variance': 0},
                topic_indicators=[],
                content_type='unknown'
            )
    
    def _analyze_educational_content(self, content: str) -> Dict[str, Any]:
        """Analyze educational content indicators"""
        try:
            content_lower = content.lower()
            
            # Count keywords by category
            keyword_counts = {}
            total_educational_keywords = 0
            
            for category, keywords in self.educational_keywords.items():
                count = sum(1 for keyword in keywords if keyword in content_lower)
                keyword_counts[category] = count
                total_educational_keywords += count
            
            # Detect educational patterns
            patterns = {
                'definitions': len(re.findall(r'\b(?:is defined as|definition|means that|refers to)\b', content_lower)),
                'examples': len(re.findall(r'\b(?:for example|such as|for instance|e\.g\.)\b', content_lower)),
                'lists': len(re.findall(r'^\s*[\d\w]\.\s', content, re.MULTILINE)),
                'questions': len(re.findall(r'\?', content)),
                'emphasis': len(re.findall(r'\b(?:important|key|crucial|essential|significant)\b', content_lower)),
                'transitions': len(re.findall(r'\b(?:however|therefore|furthermore|moreover|consequently)\b', content_lower))
            }
            
            # Calculate educational score
            educational_score = self._calculate_educational_score(keyword_counts, patterns)
            
            return {
                'keyword_counts': keyword_counts,
                'total_educational_keywords': total_educational_keywords,
                'educational_patterns': patterns,
                'educational_score': educational_score,
                'has_structure': patterns['lists'] > 0 or patterns['definitions'] > 0,
                'has_examples': patterns['examples'] > 0,
                'interactive_elements': patterns['questions']
            }
            
        except Exception as e:
            logger.error(f"Educational content analysis failed: {str(e)}")
            return {
                'keyword_counts': {},
                'total_educational_keywords': 0,
                'educational_patterns': {},
                'educational_score': 0.0,
                'has_structure': False,
                'has_examples': False,
                'interactive_elements': 0
            }
    
    def _calculate_structure_score(self, paragraphs: List[str], sentences: List[str]) -> float:
        """Calculate content structure score"""
        try:
            score = 0.0
            
            # Paragraph count (optimal: 3-10 paragraphs)
            para_count = len(paragraphs)
            if 3 <= para_count <= 10:
                score += 2.0
            elif 2 <= para_count <= 15:
                score += 1.0
            
            # Paragraph length consistency
            if paragraphs:
                lengths = [len(p.split()) for p in paragraphs]
                avg_length = sum(lengths) / len(lengths)
                if 30 <= avg_length <= 150:  # Good paragraph length
                    score += 1.5
                
                # Length variance (consistency)
                variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
                if variance < 1000:  # Consistent paragraph lengths
                    score += 1.0
            
            # Sentence structure
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
                if 10 <= avg_sentence_length <= 25:  # Good sentence length
                    score += 1.5
            
            return min(score, 6.0)  # Max score of 6.0
            
        except Exception as e:
            logger.error(f"Structure score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_vocabulary_complexity(self, words: List[str]) -> float:
        """Calculate vocabulary complexity score"""
        try:
            if not words:
                return 0.0
            
            # Unique word ratio
            unique_ratio = len(set(words)) / len(words)
            
            # Average word length
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # Complex word count (words > 6 characters)
            complex_words = [word for word in words if len(word) > 6]
            complex_ratio = len(complex_words) / len(words)
            
            # Calculate complexity score (0-4 scale)
            complexity = (unique_ratio * 1.5) + (avg_word_length / 10) + (complex_ratio * 2)
            
            return min(complexity, 4.0)
            
        except Exception as e:
            logger.error(f"Vocabulary complexity calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_sentence_complexity(self, sentences: List[str]) -> float:
        """Calculate sentence complexity score"""
        try:
            if not sentences:
                return 0.0
            
            # Average sentence length
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            
            # Sentence length variance
            lengths = [len(s.split()) for s in sentences]
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            
            # Complex sentence indicators
            complex_indicators = 0
            for sentence in sentences:
                # Count subordinate clauses, conjunctions, etc.
                if re.search(r'\b(?:because|although|however|therefore|while|whereas)\b', sentence.lower()):
                    complex_indicators += 1
                if sentence.count(',') > 2:
                    complex_indicators += 1
            
            complex_ratio = complex_indicators / len(sentences)
            
            # Calculate complexity (0-4 scale)
            complexity = (avg_length / 25) + (complex_ratio * 2) + (min(variance, 100) / 100)
            
            return min(complexity, 4.0)
            
        except Exception as e:
            logger.error(f"Sentence complexity calculation failed: {str(e)}")
            return 0.0
    
    def _count_educational_keywords(self, content_lower: str) -> int:
        """Count total educational keywords in content"""
        try:
            total_count = 0
            for category, keywords in self.educational_keywords.items():
                for keyword in keywords:
                    total_count += content_lower.count(keyword)
            return total_count
            
        except Exception as e:
            logger.error(f"Educational keyword counting failed: {str(e)}")
            return 0
    
    def _calculate_paragraph_variance(self, paragraphs: List[str]) -> float:
        """Calculate paragraph length variance"""
        try:
            if len(paragraphs) < 2:
                return 0.0
            
            lengths = [len(p.split()) for p in paragraphs]
            avg_length = sum(lengths) / len(lengths)
            variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            
            return variance
            
        except Exception as e:
            logger.error(f"Paragraph variance calculation failed: {str(e)}")
            return 0.0
    
    def _extract_topic_indicators(self, content: str) -> List[str]:
        """Extract topic indicators from content"""
        try:
            indicators = []
            
            # Look for capitalized terms (potential topics)
            capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            
            # Filter and deduplicate
            topic_candidates = []
            for term in capitalized_terms:
                if len(term) > 3 and term not in ['The', 'This', 'That', 'These', 'Those']:
                    topic_candidates.append(term)
            
            # Get most frequent topics
            from collections import Counter
            topic_counts = Counter(topic_candidates)
            indicators = [topic for topic, count in topic_counts.most_common(10) if count > 1]
            
            return indicators
            
        except Exception as e:
            logger.error(f"Topic indicator extraction failed: {str(e)}")
            return []
    
    def _detect_content_type(self, content: str, educational_keywords: int) -> str:
        """Detect the type of educational content"""
        try:
            content_lower = content.lower()
            
            # Textbook indicators (stronger indicators)
            textbook_indicators = ['chapter', 'section', 'exercise', 'problem', 'review', 'summary']
            textbook_score = sum(1 for indicator in textbook_indicators if indicator in content_lower)
            
            # Lecture notes indicators
            lecture_indicators = ['lecture', 'notes', 'today', 'class', 'discussion', 'slides']
            lecture_score = sum(1 for indicator in lecture_indicators if indicator in content_lower)
            
            # Research paper indicators (stronger indicators for research)
            research_indicators = ['methodology', 'results', 'hypothesis', 'experiment', 'data', 'abstract']
            research_score = sum(1 for indicator in research_indicators if indicator in content_lower)
            
            # Article indicators (weaker, more general)
            article_indicators = ['references', 'author', 'journal', 'published']
            article_score = sum(1 for indicator in article_indicators if indicator in content_lower)
            
            # Determine type based on highest score, but prioritize educational content
            scores = {
                'textbook': textbook_score,
                'lecture_notes': lecture_score,
                'research_paper': research_score,
                'article': article_score
            }
            
            # If we have strong educational indicators, prefer educational classification
            if educational_keywords > 5:
                # Check if it's clearly a textbook or research paper
                if textbook_score >= 2:
                    return 'textbook'
                elif research_score >= 2:
                    return 'research_paper'
                else:
                    return 'educational_material'
            elif max(scores.values()) > 0:
                return max(scores.keys(), key=lambda k: scores[k])
            else:
                return 'general_text'
                
        except Exception as e:
            logger.error(f"Content type detection failed: {str(e)}")
            return 'unknown'
    
    def _calculate_educational_score(self, keyword_counts: Dict[str, int], patterns: Dict[str, int]) -> float:
        """Calculate educational content score"""
        try:
            score = 0.0
            
            # Keyword category scores
            for category, count in keyword_counts.items():
                if count > 0:
                    score += min(count * 0.5, 2.0)  # Max 2 points per category
            
            # Pattern scores
            if patterns['definitions'] > 0:
                score += min(patterns['definitions'] * 0.5, 1.5)
            if patterns['examples'] > 0:
                score += min(patterns['examples'] * 0.3, 1.0)
            if patterns['lists'] > 0:
                score += min(patterns['lists'] * 0.2, 1.0)
            if patterns['emphasis'] > 0:
                score += min(patterns['emphasis'] * 0.1, 0.5)
            
            return min(score, 10.0)  # Max score of 10.0
            
        except Exception as e:
            logger.error(f"Educational score calculation failed: {str(e)}")
            return 0.0
    
    def _calculate_quality_score(
        self, 
        basic_analysis: Dict[str, Any], 
        detailed_analysis: ContentAnalysis, 
        educational_analysis: Dict[str, Any]
    ) -> float:
        """Calculate overall content quality score"""
        try:
            score = 0.0
            
            # Basic metrics (0-2 points)
            word_count = basic_analysis['word_count']
            if word_count >= 200:
                score += 2.0
            elif word_count >= 100:
                score += 1.5
            elif word_count >= 50:
                score += 1.0
            
            # Structure score (0-2 points)
            score += min(detailed_analysis.structure_score / 3, 2.0)
            
            # Educational content (0-3 points)
            score += min(educational_analysis['educational_score'] / 3.33, 3.0)
            
            # Vocabulary complexity (0-1.5 points)
            score += min(detailed_analysis.vocabulary_complexity / 2.67, 1.5)
            
            # Sentence complexity (0-1.5 points)
            score += min(detailed_analysis.sentence_complexity / 2.67, 1.5)
            
            return min(score, 10.0)
            
        except Exception as e:
            logger.error(f"Quality score calculation failed: {str(e)}")
            return 0.0
    
    def _determine_suitability(
        self, 
        quality_score: float, 
        basic_analysis: Dict[str, Any], 
        educational_analysis: Dict[str, Any]
    ) -> bool:
        """Determine if content is suitable for question generation"""
        try:
            # Minimum requirements
            if quality_score < self.min_quality_score:
                return False
            
            if basic_analysis['word_count'] < self.min_word_count:
                return False
            
            if educational_analysis['total_educational_keywords'] < self.min_educational_keywords:
                return False
            
            # Additional checks
            if basic_analysis['sentence_count'] < 3:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Suitability determination failed: {str(e)}")
            return False
    
    def _generate_feedback(
        self, 
        basic_analysis: Dict[str, Any], 
        detailed_analysis: ContentAnalysis, 
        educational_analysis: Dict[str, Any], 
        quality_score: float
    ) -> Tuple[List[str], List[str]]:
        """Generate issues and recommendations"""
        try:
            issues = []
            recommendations = []
            
            # Word count issues
            word_count = basic_analysis['word_count']
            if word_count < self.min_word_count:
                issues.append(f"Content too short ({word_count} words). Minimum {self.min_word_count} words required.")
                recommendations.append("Add more detailed explanations and examples to increase content length.")
            elif word_count < 100:
                recommendations.append("Consider adding more content for better question generation potential.")
            
            # Educational content issues
            edu_keywords = educational_analysis['total_educational_keywords']
            if edu_keywords < self.min_educational_keywords:
                issues.append(f"Insufficient educational content indicators ({edu_keywords} found).")
                recommendations.append("Include more educational terms like definitions, examples, and explanations.")
            
            # Structure issues
            if detailed_analysis.structure_score < 2.0:
                issues.append("Poor content structure detected.")
                recommendations.append("Organize content into clear paragraphs with logical flow.")
            
            if basic_analysis['paragraph_count'] < 2:
                recommendations.append("Break content into multiple paragraphs for better readability.")
            
            # Sentence complexity
            if detailed_analysis.sentence_complexity < 1.0:
                recommendations.append("Consider using more varied sentence structures.")
            elif detailed_analysis.sentence_complexity > 3.5:
                recommendations.append("Some sentences may be too complex. Consider simplifying for clarity.")
            
            # Educational patterns
            patterns = educational_analysis['educational_patterns']
            if patterns['definitions'] == 0:
                recommendations.append("Include clear definitions of key terms.")
            if patterns['examples'] == 0:
                recommendations.append("Add examples to illustrate concepts.")
            
            # Overall quality
            if quality_score < 5.0:
                issues.append(f"Overall content quality is low (score: {quality_score:.1f}/10).")
                recommendations.append("Focus on improving educational content structure and vocabulary.")
            elif quality_score < 7.0:
                recommendations.append("Content quality is moderate. Consider adding more educational elements.")
            
            return issues, recommendations
            
        except Exception as e:
            logger.error(f"Feedback generation failed: {str(e)}")
            return ["Error generating feedback"], ["Please review content manually"]
    
    def validate_for_question_generation(self, content: str, min_questions: int = 1) -> Dict[str, Any]:
        """
        Validate content specifically for question generation capability
        
        Args:
            content: Content to validate
            min_questions: Minimum number of questions expected
            
        Returns:
            Validation result with question generation assessment
        """
        try:
            # Run standard validation
            validation_result = self.validate_content(content)
            
            # Estimate question generation potential
            word_count = validation_result.word_count
            educational_score = validation_result.educational_indicators['educational_score']
            
            # More generous estimation: 1 question per 75-100 words, adjusted by educational score
            base_questions = max(1, word_count // 100)  # More generous base calculation
            education_multiplier = min(max(educational_score / 4.0, 1.0), 2.5)  # Min 1x, Max 2.5x multiplier
            estimated_questions = int(base_questions * education_multiplier)
            
            # Question generation suitability (more lenient for good educational content)
            suitable_for_generation = (
                validation_result.is_suitable and 
                estimated_questions >= min_questions and
                validation_result.quality_score >= 3.5  # Slightly lower threshold
            )
            
            return {
                'validation_result': validation_result,
                'suitable_for_generation': suitable_for_generation,
                'estimated_questions': estimated_questions,
                'min_questions_required': min_questions,
                'generation_confidence': min(validation_result.quality_score / 10.0, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Question generation validation failed: {str(e)}")
            raise ContentValidationError(f"Question generation validation failed: {str(e)}")

# Utility functions
def validate_content_quality(content: str, filename: str = None) -> ContentValidationResult:
    """
    Convenience function to validate content quality
    
    Args:
        content: Content to validate
        filename: Optional filename
        
    Returns:
        ContentValidationResult
    """
    service = ContentValidationService()
    return service.validate_content(content, filename)

def check_question_generation_suitability(content: str, min_questions: int = 1) -> Dict[str, Any]:
    """
    Convenience function to check question generation suitability
    
    Args:
        content: Content to check
        min_questions: Minimum questions required
        
    Returns:
        Suitability assessment
    """
    service = ContentValidationService()
    return service.validate_for_question_generation(content, min_questions)