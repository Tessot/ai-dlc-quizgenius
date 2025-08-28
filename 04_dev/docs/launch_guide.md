# 🚀 QuizGenius MVP - Launch Guide

Welcome to QuizGenius MVP! This guide will help you launch and run the application on your computer.

## 📋 Prerequisites

### 1. Python Environment
Make sure you have Python 3.8+ installed on your system:

```bash
# Check your Python version
python --version
# or
python3 --version
```

### 2. AWS Account
You'll need an AWS account with appropriate permissions for:
- DynamoDB (for data storage)
- Cognito (for user authentication)
- Bedrock (for AI question generation)

## 🔧 Installation & Setup

### Step 1: Navigate to Application Directory
```bash
cd 04_dev
```

### Step 2: Install Dependencies

**Option A: Direct Installation**
```bash
pip install -r requirements.txt
```

**Option B: Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure AWS Credentials

Choose one of the following methods:

**Method A: AWS CLI (Recommended)**
```bash
# Install AWS CLI if not already installed
pip install awscli

# Configure AWS credentials
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (`json`)

**Method B: Environment Variables**
Create a `.env` file in the `04_dev` directory:

```bash
# Create .env file
touch .env
```

Add your AWS credentials to the `.env` file:
```env
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Optional: Set debug mode
DEBUG=true
```

## 🏗️ Setup AWS Resources

### Step 1: Create DynamoDB Tables
```bash
python scripts/create_dynamodb_tables.py
```

This creates the following tables:
- `QuizGenius-Users` - User accounts and profiles
- `QuizGenius-Documents` - Uploaded PDF documents
- `QuizGenius-Questions` - Generated questions
- `QuizGenius-Tests` - Created tests
- `QuizGenius-TestAttempts` - Student test attempts
- `QuizGenius-Results` - Test results and analytics

### Step 2: Create Cognito User Pool
```bash
python scripts/create_cognito_user_pool.py
```

This sets up AWS Cognito for user authentication and registration.

### Step 3: Verify Setup
Run these test scripts to ensure everything is configured correctly:

```bash
# Test AWS credentials
python scripts/test_aws_credentials.py

# Test DynamoDB setup
python scripts/test_dynamodb_setup.py

# Test authentication service
python scripts/test_auth_service.py
```

## 🚀 Launch the Application

### Start the Streamlit Application
```bash
streamlit run app.py
```

**Alternative command:**
```bash
python -m streamlit run app.py
```

### Access the Application
The application will automatically open in your browser at:
**http://localhost:8501**

If it doesn't open automatically, navigate to the URL manually.

### Custom Port (if needed)
If port 8501 is already in use:
```bash
streamlit run app.py --server.port 8502
```

## 👥 First Time Setup

### 1. Register User Accounts

**Create an Instructor Account:**
1. Click "Register as Instructor"
2. Fill in your details:
   - First Name, Last Name
   - Email address
   - Password
   - Institution (optional)
3. Click "Register"

**Create a Student Account:**
1. Click "Register as Student"
2. Fill in your details:
   - First Name, Last Name
   - Email address
   - Password
   - School/Institution (optional)
   - Subject interests (optional)
3. Click "Register"

### 2. Test the Complete Workflow

**As an Instructor:**
1. **Upload PDF**: Go to "PDF Upload" and upload a document
2. **Generate Questions**: Use AI to generate questions from the PDF
3. **Review Questions**: Edit and refine the generated questions
4. **Create Test**: Combine questions into a test
5. **Publish Test**: Make the test available to students
6. **View Analytics**: Monitor student performance

**As a Student:**
1. **Browse Tests**: View available tests
2. **Take Test**: Complete a test with the built-in timer
3. **View Results**: See detailed results and feedback
4. **Track Progress**: Monitor your performance over time

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. AWS Credentials Error
**Error:** `AWS credentials validation failed`

**Solution:**
```bash
# Test your AWS setup
python scripts/test_aws_credentials.py

# Reconfigure AWS CLI
aws configure

# Or check your .env file for correct credentials
```

#### 2. DynamoDB Tables Not Found
**Error:** `Table 'QuizGenius-Users' doesn't exist`

**Solution:**
```bash
# Recreate DynamoDB tables
python scripts/create_dynamodb_tables.py

# Verify tables were created
python scripts/test_dynamodb_setup.py
```

#### 3. Cognito User Pool Issues
**Error:** `User pool not found`

**Solution:**
```bash
# Recreate Cognito user pool
python scripts/create_cognito_user_pool.py
```

#### 4. Port Already in Use
**Error:** `Port 8501 is already in use`

**Solution:**
```bash
# Use a different port
streamlit run app.py --server.port 8502

# Or find and stop the process using port 8501
lsof -ti:8501 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8501   # Windows
```

#### 5. Module Import Errors
**Error:** `ModuleNotFoundError`

**Solution:**
```bash
# Ensure you're in the correct directory
cd 04_dev

# Reinstall dependencies
pip install -r requirements.txt

# If using virtual environment, make sure it's activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### 6. Permission Errors
**Error:** `Access denied` or `Permission denied`

**Solution:**
- Ensure your AWS user has the necessary permissions
- Check that your AWS credentials are correct
- Verify your AWS region is supported

### System Status Check
Once the application is running:
1. Navigate to "System Status" in the sidebar
2. Verify all services show as "Connected"
3. Check for any error messages

## 📊 Available Features

### 🎓 Instructor Features
- ✅ **PDF Upload & Processing** - Upload and extract text from PDF documents
- ✅ **AI Question Generation** - Generate multiple choice and true/false questions
- ✅ **Question Management** - Review, edit, and delete questions
- ✅ **Test Creation** - Create tests from question pools
- ✅ **Test Publishing** - Publish tests with access codes
- ✅ **Results & Analytics** - Comprehensive analytics dashboard
- ✅ **Student Performance Tracking** - Individual and class performance metrics

### 👨‍🎓 Student Features
- ✅ **Browse Available Tests** - View and filter available tests
- ✅ **Test Taking Interface** - Take tests with built-in timer
- ✅ **Immediate Results** - Get instant feedback after submission
- ✅ **Detailed Review** - Review answers with explanations
- ✅ **Performance Tracking** - Track progress over time
- ✅ **Test History** - View all completed tests

## 🎯 Quick Start Commands

For a complete setup from scratch:

```bash
# 1. Navigate to application directory
cd 04_dev

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure AWS (choose one method)
aws configure
# OR create .env file with credentials

# 4. Setup AWS resources
python scripts/create_dynamodb_tables.py
python scripts/create_cognito_user_pool.py

# 5. Verify setup
python scripts/test_aws_credentials.py
python scripts/test_dynamodb_setup.py

# 6. Launch application
streamlit run app.py
```

## 📝 Important Notes

### Security
- Never commit AWS credentials to version control
- Use environment variables or AWS CLI for credentials
- The application includes built-in security measures

### Performance
- The application is optimized for development use
- For production deployment, additional configuration is needed
- Database queries are optimized with proper indexing

### Data Storage
- All data is stored in AWS DynamoDB
- User authentication is handled by AWS Cognito
- PDF content is processed in memory (not stored permanently)

### AI Features
- Question generation uses AWS Bedrock
- Requires appropriate Bedrock model access
- AI-generated questions should be reviewed before use

## 🆘 Getting Help

### Application Issues
1. Check the "System Status" page in the application
2. Review the console output for error messages
3. Run the test scripts to identify specific issues

### AWS Issues
1. Verify your AWS credentials and permissions
2. Check the AWS Console for service status
3. Ensure your region supports all required services

### Development Issues
1. Check that all dependencies are installed
2. Verify you're using Python 3.8+
3. Ensure you're in the correct directory (`04_dev`)

## 🎉 Success!

If everything is set up correctly, you should see:
- ✅ Application running at http://localhost:8501
- ✅ Login/registration pages working
- ✅ All system status checks passing
- ✅ Ability to create instructor and student accounts

**Welcome to QuizGenius MVP! You're ready to start generating AI-powered quizzes from PDF documents.**

---

*For technical support or questions about the application, refer to the development documentation or contact the development team.*