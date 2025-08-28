# Student User Stories - QuizGenius MVP (High Priority Only)

## Overview
This document contains the high priority user stories for student functionality in the QuizGenius MVP. These stories focus on essential functionality: account management, test discovery, test taking, and results viewing.

---

## 3.1 Account Registration and Authentication Stories

### Story 3.1.1: Student Account Registration
**As a** student  
**I want to** register for a QuizGenius account  
**So that** I can access and take tests created by my instructors

**Acceptance Criteria:**
- Given I am a new student
- When I visit the registration page
- Then I can create an account using email and password
- And my account is created through AWS Cognito
- And I receive a confirmation email to verify my account
- And I can log in after email verification

### Story 3.1.2: Student Login
**As a** registered student  
**I want to** log into my QuizGenius account  
**So that** I can access available tests and view my results

**Acceptance Criteria:**
- Given I have a verified student account
- When I enter my correct email and password
- Then I am authenticated through AWS Cognito
- And I am redirected to my student dashboard
- And my session is maintained securely

---

## 3.2 Available Tests Browsing Stories

### Story 3.2.1: View Available Tests
**As a** student  
**I want to** see all available tests on the platform  
**So that** I can choose which tests to take

**Acceptance Criteria:**
- Given I am logged into my student dashboard
- When I access the "Available Tests" section
- Then I can see a list of all published tests
- And I can see the test title and description for each test
- And I can see which tests I have already taken
- And I can see which tests I haven't taken yet



---

## 3.3 Test Taking Experience Stories

### Story 3.3.1: Start a Test
**As a** student  
**I want to** start taking a test  
**So that** I can demonstrate my knowledge of the subject

**Acceptance Criteria:**
- Given I have selected a test to take
- When I click "Start Test"
- Then I see the first question of the test
- And I can see the total number of questions
- And I can see a timer if the test has a time limit
- And I can see my progress through the test

### Story 3.3.2: Answer Multiple Choice Questions
**As a** student  
**I want to** answer multiple choice questions  
**So that** I can complete the test

**Acceptance Criteria:**
- Given I am taking a test with multiple choice questions
- When I view a multiple choice question
- Then I can see the question text clearly
- And I can see all available answer options
- And I can select one answer option
- And I can change my selection before moving to the next question
- And my selected answer is visually highlighted

### Story 3.3.3: Answer True/False Questions
**As a** student  
**I want to** answer true/false questions  
**So that** I can complete the test

**Acceptance Criteria:**
- Given I am taking a test with true/false questions
- When I view a true/false question
- Then I can see the question statement clearly
- And I can select either "True" or "False"
- And I can change my selection before moving to the next question
- And my selected answer is visually highlighted

### Story 3.3.4: Navigate Through Test Questions
**As a** student  
**I want to** navigate between questions during the test  
**So that** I can review and change my answers

**Acceptance Criteria:**
- Given I am taking a test
- When I am on any question
- Then I can click "Next" to go to the next question
- And I can click "Previous" to go back to previous questions
- And I can see which questions I have answered
- And I can see which questions are still unanswered
- And I can jump to any question using a question navigator

### Story 3.3.5: Submit Test
**As a** student  
**I want to** submit my completed test  
**So that** I can receive my results

**Acceptance Criteria:**
- Given I have answered all questions in a test
- When I click "Submit Test"
- Then I see a confirmation dialog asking if I'm sure
- And I can review unanswered questions before submitting
- And after confirming, my test is submitted for grading
- And I cannot modify my answers after submission
- And I am redirected to see my results

---

## 3.4 Results and Feedback Viewing Stories

### Story 3.4.1: View Test Results Immediately
**As a** student  
**I want to** see my test results immediately after submission  
**So that** I can know how I performed

**Acceptance Criteria:**
- Given I have just submitted a test
- When the test is auto-graded
- Then I can see my overall score (percentage and points)
- And I can see how many questions I got correct/incorrect
- And I can see the time I took to complete the test
- And I can see my results are saved to my account

### Story 3.4.2: Review Correct and Incorrect Answers
**As a** student  
**I want to** see which questions I got right and wrong  
**So that** I can learn from my mistakes

**Acceptance Criteria:**
- Given I have completed a test and received results
- When I view my detailed results
- Then I can see each question with my answer
- And I can see the correct answer for each question
- And questions are marked as correct (green) or incorrect (red)
- And I can see explanations or feedback if provided

