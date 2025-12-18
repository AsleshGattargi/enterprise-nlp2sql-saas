# Azure OpenAI Integration Setup

This guide will help you integrate Azure OpenAI with the Multi-Tenant NLP2SQL system for enhanced natural language query processing.

## 🎯 Benefits of Azure OpenAI Integration

- **Superior Query Understanding**: GPT-4 provides much better natural language comprehension
- **Complex Query Support**: Handle sophisticated queries with joins, aggregations, and filters
- **Context Awareness**: Understands business context and user intent better
- **Multi-language Support**: Works with queries in multiple languages
- **Learning Capability**: Adapts to organization-specific terminology

## 📋 Prerequisites

1. **Azure Subscription**: You need an active Azure subscription
2. **Azure OpenAI Resource**: Access to Azure OpenAI service (requires approval)
3. **Model Deployment**: A deployed GPT-4 or GPT-3.5-turbo model

## 🚀 Step-by-Step Setup

### Step 1: Create Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Azure OpenAI"
4. Click "Create" and fill in:
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new or use existing
   - **Region**: Choose a supported region (e.g., East US, West Europe)
   - **Name**: Your resource name (e.g., `mycompany-openai`)
   - **Pricing Tier**: Standard S0

### Step 2: Deploy a Model

1. Go to your Azure OpenAI resource
2. Click "Go to Azure OpenAI Studio" 
3. Navigate to "Deployments"
4. Click "Create new deployment"
5. Configure deployment:
   - **Model**: GPT-4 or GPT-35-Turbo
   - **Deployment name**: `nlp2sql-gpt4` (or your preferred name)
   - **Version**: Latest available
   - **Deployment type**: Standard

### Step 3: Get Your Credentials

1. In Azure Portal, go to your OpenAI resource
2. Click "Keys and Endpoint"
3. Copy the following information:
   - **Endpoint**: `https://your-resource-name.openai.azure.com/`
   - **Key**: One of the API keys
   - **API Version**: Use `2024-02-15-preview`

### Step 4: Update Configuration

Edit your `.env` file and update the Azure OpenAI settings:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_KEY=your-actual-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT=nlp2sql-gpt4
AZURE_OPENAI_MODEL=gpt-4
ENABLE_AZURE_OPENAI=true
```

**Replace:**
- `your-resource-name` with your Azure OpenAI resource name
- `your-actual-api-key-here` with your actual API key
- `nlp2sql-gpt4` with your actual deployment name

### Step 5: Test the Integration

Run the test script to verify everything is working:

```bash
python test_azure_openai.py
```

You should see all tests pass:
```
Results: 3/3 tests passed
[SUCCESS] All tests passed! Azure OpenAI integration is ready.
```

## 🧪 Testing with Queries

Once configured, restart your application and try these enhanced queries:

### Simple Queries
- "Show me all products"
- "How many customers do we have?"
- "List sales from last month"

### Complex Queries  
- "Show me the top 5 products by revenue this quarter"
- "Find customers who haven't made a purchase in the last 6 months"
- "What's the average order value for each product category?"

### Business Intelligence Queries
- "Compare this month's sales to last month"
- "Which products have the highest profit margins?"
- "Show me customer retention rates by region"

## ⚙️ Configuration Options

### Model Selection
- **GPT-4**: Best quality, higher cost, slower response
- **GPT-3.5-Turbo**: Good quality, lower cost, faster response

### Temperature Settings
The system uses `temperature=0.1` for consistent, focused SQL generation. You can adjust this in the code:

```python
temperature=0.1  # More deterministic (recommended for SQL)
temperature=0.3  # More creative (experimental)
```

### Token Limits
- Default: `max_tokens=1000` 
- Increase for very complex queries
- Decrease to save costs

## 🔧 Troubleshooting

### Common Issues

**1. Authentication Errors**
```
Error: The API deployment for this resource does not exist
```
- Check your deployment name in `.env`
- Verify the model is deployed in Azure OpenAI Studio

**2. Rate Limiting**
```
Error: Rate limit exceeded
```
- Wait a moment and retry
- Consider upgrading your Azure OpenAI pricing tier

**3. Model Not Available**
```
Error: The model 'gpt-4' is not available
```
- Check if GPT-4 is available in your region
- Use GPT-3.5-Turbo as alternative

**4. Endpoint Issues**
```
Error: Could not connect to Azure OpenAI service
```
- Verify your endpoint URL is correct
- Check your API key is valid
- Ensure your resource is active

### Debug Mode

Enable detailed logging by setting in your `.env`:
```env
LOG_LEVEL=DEBUG
```

Then check logs for detailed Azure OpenAI interactions.

### Fallback Behavior

If Azure OpenAI fails, the system automatically falls back to local processing, so your application will continue working.

## 💰 Cost Considerations

### Pricing (as of 2024)
- **GPT-4**: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- **GPT-3.5-Turbo**: ~$0.0015 per 1K input tokens, ~$0.002 per 1K output tokens

### Cost Optimization
1. **Use GPT-3.5-Turbo** for simple queries
2. **Cache common queries** to avoid repeated API calls
3. **Monitor usage** in Azure Portal
4. **Set spending limits** to avoid unexpected costs

### Estimated Monthly Costs
- **Light usage** (100 queries/day): ~$15-30/month
- **Medium usage** (500 queries/day): ~$75-150/month  
- **Heavy usage** (2000 queries/day): ~$300-600/month

## 🔐 Security Best Practices

1. **Rotate API Keys**: Change keys regularly
2. **Use Key Vault**: Store keys in Azure Key Vault for production
3. **Monitor Usage**: Watch for unusual activity
4. **Network Security**: Restrict access to your Azure OpenAI resource
5. **Data Privacy**: Ensure queries don't contain sensitive customer data

## 📈 Performance Optimization

### Response Times
- **GPT-3.5-Turbo**: ~1-3 seconds
- **GPT-4**: ~3-8 seconds

### Optimization Strategies
1. **Parallel Processing**: Process multiple queries simultaneously
2. **Caching**: Cache common query patterns
3. **Smart Routing**: Use local processing for simple queries
4. **Connection Pooling**: Reuse HTTP connections

## 🎯 Advanced Features

### Custom Prompts
You can customize the system prompts in `src/nlp2sql_engine.py` to:
- Add industry-specific terminology
- Include business rules and constraints
- Customize output formats
- Add validation logic

### HDT Integration
The system integrates with Human Digital Twins to provide:
- Role-based query suggestions
- Personalized explanations
- Context-aware responses
- User-specific optimizations

## 📞 Support

If you encounter issues:
1. Check this documentation first
2. Review Azure OpenAI service health
3. Test with the provided test script
4. Check application logs for detailed errors

---

**🎉 Congratulations!** You now have enterprise-grade natural language to SQL conversion powered by Azure OpenAI!