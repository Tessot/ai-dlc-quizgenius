# Instructor User Stories - QuizGenius MVP (High Priority Only)

## Overview
This document contains the high priority user stories for instructor functionality in the QuizGenius MVP. These stories focus on the essential workflow: account management, PDF upload, question generation, test creation, and results viewing.

---

## 2.1 Account Registration and Authentication Stories

### Story 2.1.1: Instructor Account Registration
**As an** instructor  
**I want to** register for a QuizGenius account  
**So that** I can access the platform to create tests from my lecture materials

**Acceptance Criteria:**
- Given I am a new instructor
- When I visit the registration page
- Then I can create an account using email and password
- And my account is created through AWS Cognito
- And I receive a confirmation email to verify my account
- And I can log in after email verification

### Story 2.1.2: Instructor Login
**As a** registered instructor  
**I want to** log into my QuizGenius account  
**So that** I can access my dashboard and manage my tests

**Acceptance Criteria:**
- Given I have a verified instructor account
- When I enter my correct email and password
- Then I am authenticated through AWS Cognito
- And I am redirected to my instructor dashboard
- And my session is maintained securely

---

## 2.2 PDF Upload and Processing Stories

### Story 2.2.1: PDF Upload
**As an** instructor  
**I want to** upload a PDF of my lecture content  
**So that** the system can generate quiz questions from the material

**Acceptance Criteria:**
- Given I am logged into my instructor dashboard
- When I click "Upload PDF" and select a text-based PDF file
- Then the file is uploaded to the system
- And I see a confirmation that the upload was successful
- And the PDF is stored securely for processing
- And I receive an error message if the file is not a valid PDF

### Story 2.2.2: PDF Content Validation
**As an** instructor  
**I want to** know if my PDF contains extractable text  
**So that** I understand whether questions can be generated from it

**Acceptance Criteria:**
- Given I have uploaded a PDF file
- When the system processes the PDF
- Then it extracts and validates the text content
- And I see a preview of the extracted text
- And I receive a warning if no text can be extracted
- And I can proceed to question generation if text is successfully extracted

---

## 2.3 AI Question Generation Stories

### Story 2.3.1: Generate Questions from PDF
**As an** instructor  
**I want to** generate quiz questions automatically from my uploaded PDF  
**So that** I can save time creating assessments

**Acceptance Criteria:**
- Given I have successfully uploaded a PDF with extractable text
- When I click "Generate Questions"
- Then the system uses Amazon Bedrock to analyze the content
- And it generates multiple choice and true/false questions
- And I see a list of generated questions with their answers
- And each question includes the correct answer and distractors (for multiple choice)

---

## 2.4 Question Review and Editing Stories

### Story 2.4.1: Review Generated Questions
**As an** instructor  
**I want to** review all generated questions before creating a test  
**So that** I can ensure they are accurate and appropriate

**Acceptance Criteria:**
- Given questions have been generated from my PDF
- When I view the questions list
- Then I can see each question with its type (multiple choice or true/false)
- And I can see the correct answer for each question
- And I can see all answer options for multiple choice questions
- And questions are clearly formatted and readable

### Story 2.4.2: Edit Question Content
**As an** instructor  
**I want to** edit the generated questions  
**So that** I can improve their clarity and accuracy

**Acceptance Criteria:**
- Given I am reviewing generated questions
- When I click "Edit" on a question
- Then I can modify the question text
- And I can edit answer options for multiple choice questions
- And I can change the correct answer
- And I can save my changes
- And the updated question is reflected in the questions list

### Story 2.4.3: Delete Unwanted Questions
**As an** instructor  
**I want to** delete questions that are not suitable  
**So that** my test only includes high-quality questions

**Acceptance Criteria:**
- Given I am reviewing generated questions
- When I select questions I want to remove
- Then I can delete individual questions
- And I can delete multiple questions at once
- And deleted questions are permanently removed from the question pool
- And I receive confirmation before deletion

---

## 2.5 Test Creation and Publishing Stories

### Story 2.5.1: Create Test from Questions
**As an** instructor  
**I want to** create a test using my reviewed questions  
**So that** students can take the assessment

**Acceptance Criteria:**
- Given I have a set of reviewed and edited questions
- When I click "Create Test"
- Then I can give the test a title and description
- And I can select which questions to include in the test
- And I can set the test duration (time limit)
- And I can preview how the test will appear to students

### Story 2.5.2: Publish Test for Students
**As an** instructor  
**I want to** publish my test so students can access it  
**So that** they can take the assessment

**Acceptance Criteria:**
- Given I have created a test with selected questions
- When I click "Publish Test"
- Then the test becomes available to all students on the platform
- And students can see the test in their available tests list
- And I receive confirmation that the test is published
- And I can unpublish the test if needed

---

## 2.6 Student Results Viewing Stories

### Story 2.6.1: View Test Results Summary
**As an** instructor  
**I want to** see how students performed on my tests  
**So that** I can assess their understanding of the material

**Acceptance Criteria:**
- Given students have taken my published test
- When I access the test results section
- Then I can see a summary of all student attempts
- And I can see the average score for the test
- And I can see how many students have taken the test
- And I can see the completion rate

### Story 2.6.2: View Individual Student Results
**As an** instructor  
**I want to** see detailed results for individual students  
**So that** I can provide targeted feedback

**Acceptance Criteria:**
- Given students have completed my test
- When I click on a specific student's result
- Then I can see their individual score and answers
- And I can see which questions they got correct/incorrect
- And I can see the time they took to complete the test
- And I can see when they took the test

