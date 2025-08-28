"""
Question Storage Service for QuizGenius MVP
Handles persistent storage of questions and tests in DynamoDB
Implements Step 3.2.3: Question Data Storage (US-4.4.2 - 5 points)
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from services.question_generation_service import GeneratedQuestion
from services.question_processor import ProcessedQuestion
from utils.dynamodb_utils import get_current_timestamp, generate_id
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionStorageError(Exception):
    """Custom exception for question storage errors"""
    pass

class QuestionStorageService:
    """
    Service for storing and managing questions in DynamoDB
    """
    
    def __init__(self):
        """Initialize the question storage service"""
        try:
            self.config = Config()
            
            # Initialize DynamoDB client
            self.dynamodb = boto3.resource('dynamodb', region_name=self.config.AWS_REGION)
            
            # Table references
            self.questions_table = self.dynamodb.Table('QuizGenius_Questions')
            self.documents_table = self.dynamodb.Table('QuizGenius_Documents')
            self.tests_table = self.dynamodb.Table('QuizGenius_Tests')
            
            # Verify table access
            self._verify_table_access()
            
            logger.info("QuestionStorageService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize QuestionStorageService: {str(e)}")
            raise QuestionStorageError(f"Storage service initialization failed: {str(e)}")
    
    def store_question(self, question: GeneratedQuestion, document_id: str, 
                      instructor_id: str, processed_question: Optional[ProcessedQuestion] = None) -> Dict[str, Any]:
        """
        Store a generated question in DynamoDB
        
        Args:
            question: Generated question to store
            document_id: ID of source document
            instructor_id: ID of instructor who generated the question
            processed_question: Optional processed version of the question
            
        Returns:
            Dict with storage result and metadata
        """
        try:
            logger.info(f"Storing question: {question.question_id}")
            
            # Prepare question item
            question_item = {
                'question_id': question.question_id,
                'document_id': document_id,
                'created_by': instructor_id,
                'question_type': question.question_type,
                'question_text': question.question_text,
                'correct_answer': question.correct_answer,
                'options': question.options,
                'difficulty_level': question.difficulty_level,
                'topic': question.topic,
                'source_content': question.source_content,
                'confidence_score': question.confidence_score,
                'created_date': get_current_timestamp(),
                'updated_date': get_current_timestamp(),
                'status': 'active',
                'metadata': question.metadata
            }
            
            # Add processed question data if available
            if processed_question:
                question_item.update({
                    'processed_text': processed_question.processed_text,
                    'processed_options': processed_question.processed_options,
                    'quality_score': processed_question.quality_score,
                    'validation_result': asdict(processed_question.validation_result),
                    'processing_timestamp': processed_question.processing_timestamp,
                    'processing_metadata': processed_question.metadata
                })
            
            # Store in DynamoDB
            response = self.questions_table.put_item(Item=question_item)
            
            # Update question count in document
            self._update_document_question_count(document_id, 1)
            
            logger.info(f"Question stored successfully: {question.question_id}")
            
            return {
                'success': True,
                'question_id': question.question_id,
                'storage_timestamp': question_item['created_date'],
                'response_metadata': response.get('ResponseMetadata', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to store question: {str(e)}")
            raise QuestionStorageError(f"Question storage failed: {str(e)}")
    
    def store_questions_batch(self, questions: List[GeneratedQuestion], document_id: str, 
                            instructor_id: str, processed_questions: Optional[List[ProcessedQuestion]] = None) -> Dict[str, Any]:
        """
        Store multiple questions in a batch operation
        
        Args:
            questions: List of generated questions to store
            document_id: ID of source document
            instructor_id: ID of instructor who generated the questions
            processed_questions: Optional list of processed questions
            
        Returns:
            Dict with batch storage results
        """
        try:
            logger.info(f"Storing {len(questions)} questions in batch")
            
            # Prepare batch items
            batch_items = []
            processed_map = {}
            
            if processed_questions:
                processed_map = {pq.question_id: pq for pq in processed_questions}
            
            for question in questions:
                processed_question = processed_map.get(question.question_id)
                
                question_item = {
                    'question_id': question.question_id,
                    'document_id': document_id,
                    'created_by': instructor_id,
                    'question_type': question.question_type,
                    'question_text': question.question_text,
                    'correct_answer': question.correct_answer,
                    'options': question.options,
                    'difficulty_level': question.difficulty_level,
                    'topic': question.topic,
                    'source_content': question.source_content,
                    'confidence_score': Decimal(str(question.confidence_score)),
                    'created_date': get_current_timestamp(),
                    'updated_date': get_current_timestamp(),
                    'status': 'active',
                    'metadata': question.metadata
                }
                
                # Add processed data if available
                if processed_question:
                    question_item.update({
                        'ProcessedText': processed_question.processed_text,
                        'ProcessedOptions': processed_question.processed_options,
                        'QualityScore': processed_question.quality_score,
                        'ValidationResult': asdict(processed_question.validation_result),
                        'ProcessingTimestamp': processed_question.processing_timestamp,
                        'ProcessingMetadata': processed_question.metadata
                    })
                
                batch_items.append(question_item)
            
            # Execute batch write
            success_count = 0
            failed_items = []
            
            # DynamoDB batch_writer handles batching automatically
            with self.questions_table.batch_writer() as batch:
                for item in batch_items:
                    try:
                        batch.put_item(Item=item)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to store question {item['QuestionID']}: {str(e)}")
                        failed_items.append({
                            'question_id': item['QuestionID'],
                            'error': str(e)
                        })
            
            # Update document question count
            if success_count > 0:
                self._update_document_question_count(document_id, success_count)
            
            logger.info(f"Batch storage completed: {success_count} successful, {len(failed_items)} failed")
            
            return {
                'success': success_count > 0,
                'total_questions': len(questions),
                'stored_successfully': success_count,
                'failed_count': len(failed_items),
                'failed_items': failed_items,
                'storage_timestamp': get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Batch question storage failed: {str(e)}")
            raise QuestionStorageError(f"Batch storage failed: {str(e)}")
    
    def get_question(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a question by ID
        
        Args:
            question_id: ID of question to retrieve
            
        Returns:
            Question data or None if not found
        """
        try:
            response = self.questions_table.get_item(
                Key={'QuestionID': question_id}
            )
            
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Failed to retrieve question {question_id}: {str(e)}")
            raise QuestionStorageError(f"Question retrieval failed: {str(e)}")
    
    def get_questions_by_document(self, document_id: str, instructor_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all questions for a document
        
        Args:
            document_id: ID of source document
            instructor_id: ID of instructor (for security)
            
        Returns:
            List of question data
        """
        try:
            # Query using QuestionsByDocument-Index
            response = self.questions_table.query(
                IndexName='QuestionsByDocument-Index',
                KeyConditionExpression='document_id = :document_id',
                FilterExpression='created_by = :instructor_id AND #status = :status',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':instructor_id': instructor_id,
                    ':document_id': document_id,
                    ':status': 'active'
                }
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to retrieve questions for document {document_id}: {str(e)}")
            raise QuestionStorageError(f"Document questions retrieval failed: {str(e)}")
    
    def get_questions_by_instructor(self, instructor_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve questions created by an instructor
        
        Args:
            instructor_id: ID of instructor
            limit: Maximum number of questions to return
            
        Returns:
            List of question data
        """
        try:
            response = self.questions_table.query(
                IndexName='QuestionsByCreator-Index',
                KeyConditionExpression='created_by = :instructor_id',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':instructor_id': instructor_id,
                    ':status': 'active'
                },
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to retrieve questions for instructor {instructor_id}: {str(e)}")
            raise QuestionStorageError(f"Instructor questions retrieval failed: {str(e)}")
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single question by ID
        
        Args:
            question_id: Question ID
            
        Returns:
            Question data or None if not found
        """
        try:
            response = self.questions_table.get_item(
                Key={'question_id': question_id}
            )
            
            return response.get('Item')
            
        except Exception as e:
            logger.error(f"Failed to retrieve question {question_id}: {str(e)}")
            return None
    
    def update_question(self, question_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a question
        
        Args:
            question_id: ID of question to update
            updates: Dictionary of fields to update
            
        Returns:
            Update result
        """
        try:
            # Prepare update expression
            update_expression = "SET UpdatedAt = :updated_at"
            expression_values = {':updated_at': get_current_timestamp()}
            
            for key, value in updates.items():
                if key not in ['QuestionID', 'CreatedAt']:  # Don't allow updating these
                    update_expression += f", {key} = :{key.lower()}"
                    expression_values[f":{key.lower()}"] = value
            
            response = self.questions_table.update_item(
                Key={'QuestionID': question_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            logger.info(f"Question updated successfully: {question_id}")
            return {
                'success': True,
                'updated_item': response.get('Attributes'),
                'update_timestamp': expression_values[':updated_at']
            }
            
        except Exception as e:
            logger.error(f"Failed to update question {question_id}: {str(e)}")
            raise QuestionStorageError(f"Question update failed: {str(e)}")
    
    def delete_question(self, question_id: str, instructor_id: str) -> Dict[str, Any]:
        """
        Delete a question (soft delete by setting status to 'deleted')
        
        Args:
            question_id: ID of question to delete
            instructor_id: ID of instructor (for security)
            
        Returns:
            Deletion result
        """
        try:
            # Soft delete by updating status
            response = self.questions_table.update_item(
                Key={'question_id': question_id},
                UpdateExpression='SET #status = :status, updated_at = :updated_at',
                ConditionExpression='created_by = :instructor_id',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'deleted',
                    ':updated_at': get_current_timestamp(),
                    ':instructor_id': instructor_id
                },
                ReturnValues='ALL_OLD'
            )
            
            # Update document question count
            old_item = response.get('Attributes', {})
            if old_item.get('DocumentID'):
                self._update_document_question_count(old_item['DocumentID'], -1)
            
            logger.info(f"Question deleted successfully: {question_id}")
            return {
                'success': True,
                'deleted_item': old_item,
                'deletion_timestamp': get_current_timestamp()
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                raise QuestionStorageError("Question not found or access denied")
            else:
                raise QuestionStorageError(f"Question deletion failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to delete question {question_id}: {str(e)}")
            raise QuestionStorageError(f"Question deletion failed: {str(e)}")
    
    def get_question_statistics(self, instructor_id: str) -> Dict[str, Any]:
        """
        Get statistics about questions for an instructor
        
        Args:
            instructor_id: ID of instructor
            
        Returns:
            Statistics dictionary
        """
        try:
            # Get all questions for instructor
            questions = self.get_questions_by_instructor(instructor_id, limit=1000)
            
            # Calculate statistics
            total_questions = len(questions)
            mc_questions = len([q for q in questions if q.get('QuestionType') == 'multiple_choice'])
            tf_questions = len([q for q in questions if q.get('QuestionType') == 'true_false'])
            
            # Quality statistics
            quality_scores = [q.get('QualityScore', 0) for q in questions if q.get('QualityScore')]
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
            
            # Confidence statistics
            confidence_scores = [q.get('ConfidenceScore', 0) for q in questions if q.get('ConfidenceScore')]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Topic distribution
            topics = {}
            for question in questions:
                topic = question.get('Topic', 'Unknown')
                topics[topic] = topics.get(topic, 0) + 1
            
            return {
                'total_questions': total_questions,
                'multiple_choice_questions': mc_questions,
                'true_false_questions': tf_questions,
                'average_quality_score': round(avg_quality, 2),
                'average_confidence_score': round(avg_confidence, 2),
                'topic_distribution': topics,
                'statistics_timestamp': get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Failed to get question statistics: {str(e)}")
            raise QuestionStorageError(f"Statistics retrieval failed: {str(e)}")
    
    def _verify_table_access(self):
        """Verify access to required DynamoDB tables"""
        try:
            # Test access to each table
            self.questions_table.load()
            self.documents_table.load()
            self.tests_table.load()
            
        except Exception as e:
            raise QuestionStorageError(f"Cannot access DynamoDB tables: {str(e)}")
    
    def _update_document_question_count(self, document_id: str, count_change: int):
        """Update the question count for a document"""
        try:
            self.documents_table.update_item(
                Key={'DocumentID': document_id},
                UpdateExpression='ADD QuestionCount :count_change SET UpdatedAt = :updated_at',
                ExpressionAttributeValues={
                    ':count_change': count_change,
                    ':updated_at': get_current_timestamp()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update document question count: {str(e)}")
            # Don't raise exception as this is not critical


def create_question_storage_service() -> QuestionStorageService:
    """Factory function to create a question storage service"""
    return QuestionStorageService()


if __name__ == "__main__":
    # Test the question storage service
    try:
        storage = create_question_storage_service()
        print("QuestionStorageService initialized successfully")
    except Exception as e:
        print(f"Failed to initialize QuestionStorageService: {e}")