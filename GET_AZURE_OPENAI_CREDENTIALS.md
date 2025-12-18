# 🚀 How to Get Azure OpenAI Credentials - Complete Guide

This guide will walk you through obtaining Azure OpenAI access and credentials for your Multi-Tenant NLP2SQL system.

## 📋 Prerequisites

- **Azure Account**: Active Azure subscription (free tier works)
- **Credit Card**: Required for Azure account (even for free services)
- **Business Justification**: Azure OpenAI requires approval with use case description

## 🎯 Step 1: Apply for Azure OpenAI Access

### Why You Need Approval
Azure OpenAI is a restricted service that requires approval due to:
- Content safety and responsible AI policies
- High demand and limited capacity
- Enterprise-focused offering

### Application Process

1. **Go to Azure OpenAI Application Form**
   - Visit: https://aka.ms/oai/access
   - Or search "Azure OpenAI access request" in Azure portal

2. **Fill Out Application Form**
   ```
   Company Information:
   - Company Name: [Your company name]
   - Industry: [Technology/Healthcare/Finance/etc.]
   - Company Size: [Number of employees]
   - Use Case: Multi-tenant database query system with NLP
   
   Technical Details:
   - Primary Use Case: "Natural language to SQL conversion for business intelligence"
   - Expected Usage: "Processing business queries for data analytics"
   - Safety Measures: "Input validation, content filtering, audit logging"
   ```

3. **Use Case Description Template**
   ```
   We are building a multi-tenant database query system that converts natural 
   language questions into SQL queries for business intelligence. The system 
   serves multiple organizations with complete data isolation and security.
   
   Example queries:
   - "Show me sales performance this quarter"
   - "Which products have the highest profit margins?"
   - "List customers who haven't purchased in 6 months"
   
   We need Azure OpenAI to improve natural language understanding and handle 
   complex business queries that require context awareness and industry-specific 
   terminology understanding.
   
   Security measures include:
   - Input validation and sanitization
   - Tenant isolation with org_id filtering
   - Audit logging of all queries
   - Role-based access control
   - SQL injection prevention
   ```

4. **Submit and Wait**
   - Approval typically takes 1-5 business days
   - You'll receive email notification when approved

## 🎯 Step 2: Create Azure OpenAI Resource (After Approval)

### 2.1 Access Azure Portal
1. Go to https://portal.azure.com
2. Sign in with your Azure account

### 2.2 Create Resource
1. Click **"Create a resource"**
2. Search for **"Azure OpenAI"**
3. Click **"Create"**

### 2.3 Configure Resource
```
Basic Settings:
- Subscription: [Your subscription]
- Resource Group: Create new "nlp2sql-rg"
- Region: East US (recommended for GPT-4 availability)
- Name: "nlp2sql-openai-[yourname]"
- Pricing Tier: Standard S0

Advanced Settings:
- Network: Public endpoint (for development)
- Identity: System assigned managed identity

Tags (Optional):
- Environment: Development
- Project: NLP2SQL
- Owner: [Your name]
```

4. Click **"Review + Create"**
5. Click **"Create"** and wait for deployment

## 🎯 Step 3: Deploy AI Models

### 3.1 Access Azure OpenAI Studio
1. Go to your Azure OpenAI resource
2. Click **"Go to Azure OpenAI Studio"**
3. Or visit: https://oai.azure.com

### 3.2 Create Model Deployment
1. Navigate to **"Deployments"** in the left menu
2. Click **"Create new deployment"**

### 3.3 Configure Deployment
```
Model Selection:
- Model: GPT-4 (recommended) or GPT-35-Turbo (cheaper)
- Model Version: Latest available (e.g., 0613)

Deployment Settings:
- Deployment Name: "nlp2sql-gpt4"
- Deployment Type: Standard
- Rate Limit (TPM): 10,000 (adjust based on needs)
- Content Filter: Default (recommended)
```

4. Click **"Create"** and wait for deployment

### 3.4 Alternative Models
If GPT-4 isn't available:
- **GPT-35-Turbo**: Good performance, lower cost
- **GPT-35-Turbo-16k**: Handles longer contexts
- Check model availability in your region

## 🎯 Step 4: Get Your Credentials

### 4.1 Get Endpoint and Keys
1. Go back to Azure Portal
2. Navigate to your Azure OpenAI resource
3. Click **"Keys and Endpoint"** in the left menu

### 4.2 Copy Required Information
```
Required Credentials:
✅ Endpoint: https://your-resource-name.openai.azure.com/
✅ Key 1 or Key 2: [32-character API key]
✅ Deployment Name: nlp2sql-gpt4 (from step 3)
✅ API Version: 2024-02-15-preview (latest)
```

## 🎯 Step 5: Configure Your System

### 5.1 Update Environment File
Edit your `.env` file:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://nlp2sql-openai-yourname.openai.azure.com/
AZURE_OPENAI_KEY=your-32-character-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=nlp2sql-gpt4
AZURE_OPENAI_MODEL=gpt-4
ENABLE_AZURE_OPENAI=true
```

### 5.2 Test Configuration
Run the test script:
```bash
cd "D:\Fundae\Multi Tenant NLP2SQL"
python test_azure_openai.py
```

Expected output:
```
Results: 3/3 tests passed
[SUCCESS] All tests passed! Azure OpenAI integration is ready.
```

### 5.3 Restart Your Application
```bash
# Restart backend (if running)
# Then restart frontend
python run_demo_now.py
```

## 🎯 Step 6: Test Enhanced Queries

Try these advanced queries in your application:

### Simple Queries
- "Show me all products"
- "How many customers do we have?"

### Complex Queries (Now Possible with GPT-4)
- "Show me the top 5 products by revenue this quarter"
- "Find customers who haven't made a purchase in the last 6 months"
- "What's the average order value for each product category?"
- "Compare this month's sales to last month by product category"

## 💰 Cost Information

### Pricing (as of 2024)
- **GPT-4**: ~$0.03/1K input tokens, ~$0.06/1K output tokens
- **GPT-35-Turbo**: ~$0.0015/1K input tokens, ~$0.002/1K output tokens

### Cost Examples
- **100 queries/day**: ~$15-30/month
- **500 queries/day**: ~$75-150/month
- **2000 queries/day**: ~$300-600/month

### Cost Optimization Tips
1. Start with GPT-3.5-Turbo for testing
2. Use GPT-4 only for complex queries
3. Set spending alerts in Azure
4. Monitor usage in Azure Portal

## 🚨 Troubleshooting Common Issues

### Application Rejected
- **Reason**: Insufficient business justification
- **Solution**: Reapply with more detailed use case
- **Tip**: Emphasize business intelligence and data analytics benefits

### No GPT-4 Available
- **Reason**: Regional availability varies
- **Solution**: Try different Azure regions (East US, West Europe)
- **Alternative**: Use GPT-3.5-Turbo initially

### Quota Exceeded
- **Reason**: Too many requests
- **Solution**: Increase TPM limit in deployment settings
- **Alternative**: Implement request queuing in your application

### Authentication Errors
- **Check**: Endpoint URL format (must end with .azure.com/)
- **Check**: API key is correct (32 characters)
- **Check**: Deployment name matches exactly

## 🔄 Alternative Options

### Option A: Regular OpenAI (Easier)
If Azure OpenAI approval takes too long:
1. Get API key from https://platform.openai.com
2. Use regular OpenAI API (no approval needed)
3. I can modify the engine to support both

### Option B: Wait for Approval
- Keep using local processing (works great!)
- Apply for Azure OpenAI access
- Enable when approved

### Option C: Free Alternatives
- **Ollama**: Run LLMs locally
- **Hugging Face**: Free models with API
- **Google PaLM**: Alternative cloud LLM

## 📞 Need Help?

### Azure Support
- Azure Portal → Help + Support
- Community forums: https://docs.microsoft.com/answers/

### OpenAI Documentation
- Azure OpenAI docs: https://docs.microsoft.com/azure/cognitive-services/openai/

### Our System Support
- Run diagnostic: `python test_azure_openai.py`
- Check logs for detailed error messages
- Test with local processing first

---

## 🎉 Ready to Get Started?

1. **Apply for access**: https://aka.ms/oai/access
2. **Wait for approval** (1-5 business days)
3. **Follow this guide** to set up your resource
4. **Configure credentials** in your `.env` file
5. **Enjoy enhanced AI-powered queries!**

The approval process is the only real barrier - once you have access, setup takes about 15 minutes!