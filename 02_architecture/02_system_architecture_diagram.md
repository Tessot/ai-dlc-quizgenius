# QuizGenius MVP - System Architecture Diagram

## Overview
This document provides the high-level system architecture for QuizGenius MVP, a Streamlit-based application that converts PDF lecture content into assessments with automatic grading.

---

## High-Level System Architecture (ASCII Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QuizGenius MVP - Streamlit Application                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   Login Page    │    │ Instructor Hub  │    │  Student Hub    │             │
│  │                 │    │                 │    │                 │             │
│  │ • User Auth     │◄──►│ • PDF Upload    │    │ • View Tests    │             │
│  │ • Role Select   │    │ • Question Gen  │    │ • Take Tests    │             │
│  │ • Session Mgmt  │    │ • Test Creation │    │ • View Results  │             │
│  └─────────────────┘    │ • View Results  │    └─────────────────┘             │
│                         └─────────────────┘                                    │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                        Session State Management                             │
│  │                                                                             │
│  │  • user_role (instructor/student)     • current_test_session               │
│  │  • user_id                           • question_responses                  │
│  │  • authentication_status             • navigation_state                   │
│  │  • uploaded_files                    • form_data                          │
│  └─────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┤
│  │                           Core Business Logic                               │
│  │                                                                             │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  │ PDF Processing  │  │ Question Mgmt   │  │ Test & Grading  │             │
│  │  │                 │  │                 │  │                 │             │
│  │  │ • Upload Handle │  │ • Review/Edit   │  │ • Test Creation │             │
│  │  │ • Validation    │  │ • Delete        │  │ • Test Taking   │             │
│  │  │ • Text Extract  │  │ • Storage       │  │ • Auto Grading  │             │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│  └─────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              External Integrations                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────┐    ┌─────────────────────────────────┐ │
│  │         AWS Bedrock                 │    │    Local Data Storage          │ │
│  │                                     │    │                                 │ │
│  │  ┌─────────────────────────────────┐│    │  ┌─────────────────────────────┐│ │
│  │  │    Question Generation          ││    │  │         JSON Files          ││ │
│  │  │                                 ││    │  │                             ││ │
│  │  │ • Multiple Choice Prompts       ││    │  │ • users.json                ││ │
│  │  │ • True/False Prompts            ││    │  │ • questions.json            ││ │
│  │  │ • Response Processing           ││    │  │ • tests.json                ││ │
│  │  │ • Error Handling                ││    │  │ • results.json              ││ │
│  │  └─────────────────────────────────┘│    │  └─────────────────────────────┘│ │
│  │                                     │    │                                 │ │
│  │  ┌─────────────────────────────────┐│    │  ┌─────────────────────────────┐│ │
│  │  │  Bedrock Data Automation        ││    │  │      File Storage           ││ │
│  │  │                                 ││    │  │                             ││ │
│  │  │ • PDF Text Extraction           ││    │  │ • uploaded_pdfs/            ││ │
│  │  │ • Document Analysis             ││    │  │ • temp_files/               ││ │
│  │  │ • Content Structure Recognition ││    │  │ • exports/                  ││ │
│  │  └─────────────────────────────────┘│    │  └─────────────────────────────┘│ │
│  └─────────────────────────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture (ASCII Diagram)

```
Instructor Workflow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Login     │───►│ Upload PDF  │───►│ Generate    │───►│ Review &    │
│             │    │             │    │ Questions   │    │ Edit        │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │Local Storage│    │AWS Bedrock  │    │Local Storage│
                   │(PDF Files)  │    │(AI Service)│    │(Questions)  │
                   └─────────────┘    └─────────────┘    └─────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Create Test │───►│ Publish     │───►│ View        │
│             │    │ Test        │    │ Results     │
└─────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Local Storage│    │Local Storage│    │Local Storage│
│(Tests)      │    │(Published)  │    │(Results)    │
└─────────────┘    └─────────────┘    └─────────────┘

Student Workflow:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Login     │───►│ Browse      │───►│ Take Test   │───►│ View        │
│             │    │ Tests       │    │             │    │ Results     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                   │                   │
                           ▼                   ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
                   │Local Storage│    │Session State│    │Local Storage│
                   │(Tests)      │    │(Responses)  │    │(Results)    │
                   └─────────────┘    └─────────────┘    └─────────────┘
```

---

## Streamlit Application Structure

```
QuizGenius/
│
├── app.py                          # Main Streamlit application entry point
│
├── pages/                          # Streamlit pages directory
│   ├── 01_instructor_login.py      # Instructor authentication
│   ├── 02_student_login.py         # Student authentication
│   ├── 03_instructor_dashboard.py  # Instructor main hub
│   ├── 04_student_dashboard.py     # Student main hub
│   ├── 05_pdf_upload.py           # PDF upload and processing
│   ├── 06_question_generation.py  # AI question generation
│   ├── 07_question_management.py  # Review/edit questions
│   ├── 08_test_creation.py        # Create and publish tests
│   ├── 09_test_taking.py          # Student test interface
│   ├── 10_results_viewing.py      # Results for both roles
│   └── 11_logout.py               # Logout functionality
│
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── auth.py                    # Authentication functions
│   ├── data_manager.py            # Local data operations
│   ├── bedrock_client.py          # AWS Bedrock integration
│   ├── pdf_processor.py           # PDF handling utilities
│   ├── question_generator.py      # Question generation logic
│   ├── test_manager.py            # Test creation/management
│   ├── grading_engine.py          # Auto-grading functionality
│   └── session_manager.py         # Session state management
│
├── data/                          # Local data storage
│   ├── users.json                 # User accounts
│   ├── questions.json             # Generated questions
│   ├── tests.json                 # Created tests
│   ├── results.json               # Test results
│   ├── uploaded_pdfs/             # PDF file storage
│   ├── temp_files/                # Temporary processing files
│   └── exports/                   # Export files
│
├── config/                        # Configuration files
│   ├── aws_config.py              # AWS credentials and settings
│   ├── app_config.py              # Application settings
│   └── prompts.py                 # AI prompts for question generation
│
├── requirements.txt               # Python dependencies
├── README.md                      # Setup and usage instructions
└── .env.example                   # Environment variables template
```

---

## Component Mapping to User Stories

### **Authentication Components (Stories 2.1.1, 2.1.2, 3.1.1, 3.1.2)**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Login Pages ──► Session State ──► Role-based Navigation       │
│       │               │                        │                │
│       ▼               ▼                        ▼                │
│  • User Input    • user_role           • Instructor Hub        │
│  • Validation    • user_id             • Student Hub           │
│  • Error Msgs    • auth_status         • Logout Option         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **PDF Processing Components (Stories 2.2.1, 2.2.2, 4.1.1, 4.1.2)**
```
┌─────────────────────────────────────────────────────────────────┐
│                    PDF Processing System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  File Upload ──► Validation ──► AWS Bedrock ──► Text Storage   │
│       │              │              │               │          │
│       ▼              ▼              ▼               ▼          │
│  • st.file_up   • Format Check  • Data Auto    • Local JSON   │
│  • Progress     • Size Limit    • Text Extract • File System  │
│  • Error Msgs   • Content Val   • Quality Check• Metadata     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Question Generation Components (Stories 2.3.1, 4.2.1, 4.2.2, 4.2.3)**
```
┌─────────────────────────────────────────────────────────────────┐
│                 Question Generation System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Text Input ──► AI Processing ──► Question Parse ──► Storage   │
│       │              │                  │               │      │
│       ▼              ▼                  ▼               ▼      │
│  • PDF Text     • Bedrock API      • MC Questions  • JSON DB  │
│  • User Params  • Prompt Eng       • T/F Questions • File Sys │
│  • Progress     • Error Handle     • Validation    • Metadata │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Test Management Components (Stories 2.4.1-2.5.2, 4.4.2)**
```
┌─────────────────────────────────────────────────────────────────┐
│                   Test Management System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Question Review ──► Test Creation ──► Publishing ──► Storage  │
│       │                   │                │             │     │
│       ▼                   ▼                ▼             ▼     │
│  • Display List      • Test Config    • Status Update • JSON  │
│  • Edit Interface    • Question Select• Availability  • Files │
│  • Delete Options    • Metadata       • Student Access• Meta  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Test Taking Components (Stories 3.2.1-3.3.5)**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Taking System                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Test Browse ──► Test Start ──► Question UI ──► Submission     │
│       │              │              │               │          │
│       ▼              ▼              ▼               ▼          │
│  • Available    • Session Init  • Answer Input  • Validation  │
│  • Filtering    • Progress Track• Navigation    • Confirmation │
│  • Selection    • State Mgmt    • State Save    • Processing  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Grading & Results Components (Stories 4.3.1-4.3.3, 3.4.1-3.4.2, 2.6.1-2.6.2)**
```
┌─────────────────────────────────────────────────────────────────┐
│                  Grading & Results System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Auto Grade ──► Score Calc ──► Results Display ──► Storage     │
│       │             │               │                  │       │
│       ▼             ▼               ▼                  ▼       │
│  • Answer Check • Percentage    • Student View     • JSON DB  │
│  • MC Grading   • Points Total  • Instructor View  • File Sys │
│  • T/F Grading  • Time Track    • Detailed Review  • Reports  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Local Deployment Architecture

```
Development Environment:
┌─────────────────────────────────────────────────────────────────┐
│                      Local Laptop                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │    Python       │    │   Streamlit     │                    │
│  │  Environment    │    │   Application   │                    │
│  │                 │    │                 │                    │
│  │ • Python 3.8+   │◄──►│ • streamlit run │                    │
│  │ • pip packages  │    │ • localhost:8501│                    │
│  │ • AWS SDK       │    │ • Auto-reload   │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  Local Storage  │    │  AWS Services   │                    │
│  │                 │    │                 │                    │
│  │ • JSON files    │    │ • Bedrock API   │◄─── Internet      │
│  │ • PDF uploads   │    │ • Data Auto     │                    │
│  │ • Temp files    │    │ • Credentials   │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Future AWS Migration Path:
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   ECS/Fargate   │    │   S3 Storage    │                    │
│  │                 │    │                 │                    │
│  │ • Streamlit App │◄──►│ • PDF Files     │                    │
│  │ • Auto Scaling  │    │ • JSON Data     │                    │
│  │ • Load Balancer │    │ • Static Assets │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   DynamoDB      │    │  Cognito Auth   │                    │
│  │                 │    │                 │                    │
│  │ • User Data     │    │ • User Pools    │                    │
│  │ • Questions     │    │ • Authentication│                    │
│  │ • Results       │    │ • Authorization │                    │
│  └─────────────────┘    └─────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Session State Management Strategy

```
Streamlit Session State Structure:
┌─────────────────────────────────────────────────────────────────┐
│                      st.session_state                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Authentication State:                                          │
│  ├── authenticated: bool                                        │
│  ├── user_role: str ("instructor" | "student")                 │
│  ├── user_id: str                                              │
│  └── login_time: datetime                                      │
│                                                                 │
│  Navigation State:                                              │
│  ├── current_page: str                                         │
│  ├── previous_page: str                                        │
│  └── navigation_history: list                                  │
│                                                                 │
│  Instructor State:                                              │
│  ├── uploaded_pdf: UploadedFile                                │
│  ├── extracted_text: str                                       │
│  ├── generated_questions: list                                 │
│  ├── current_test: dict                                        │
│  └── editing_question_id: str                                  │
│                                                                 │
│  Student State:                                                 │
│  ├── current_test_session: dict                                │
│  ├── question_responses: dict                                  │
│  ├── test_start_time: datetime                                 │
│  ├── current_question_index: int                               │
│  └── test_completed: bool                                      │
│                                                                 │
│  Temporary Data:                                                │
│  ├── form_data: dict                                           │
│  ├── error_messages: list                                      │
│  ├── success_messages: list                                    │
│  └── processing_status: dict                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## AWS Bedrock Services Integration

**Confirmed: This architecture uses AWS Bedrock Data Automation for PDF processing as requested.**

### **Bedrock Data Automation Integration:**
- **PDF Text Extraction**: Uses Bedrock Data Automation APIs to extract text from uploaded PDFs
- **Document Analysis**: Leverages Bedrock's document understanding capabilities
- **Content Structure Recognition**: Identifies educational content structure for better question generation
- **Integration Method**: Direct API calls from Streamlit application using AWS SDK

### **Bedrock Foundation Models Integration:**
- **Question Generation**: Uses Bedrock foundation models (e.g., Claude, Titan) for generating questions
- **Prompt Engineering**: Custom prompts for multiple choice and true/false question generation
- **Response Processing**: Structured parsing of AI-generated questions
- **Integration Method**: Direct API calls using Bedrock Runtime API

### **Implementation Notes:**
- **AWS Credentials**: Configured locally via AWS CLI or environment variables
- **API Calls**: Synchronous calls with proper error handling and retries
- **Cost Management**: Efficient prompt design to minimize token usage
- **Regional Deployment**: Uses appropriate AWS region for Bedrock services

---

## Summary

This architecture provides:

1. **Simple Streamlit-based design** for rapid MVP development
2. **Local execution** with minimal external dependencies
3. **Clear separation of concerns** with modular utility functions
4. **AWS Bedrock integration** for AI-powered features (Data Automation + Foundation Models)
5. **Local data storage** using JSON files for simplicity
6. **Session state management** for user experience continuity
7. **Future migration path** to full AWS deployment
8. **Component mapping** to all 33 user stories

The architecture supports all MVP requirements while maintaining simplicity for local development and testing.