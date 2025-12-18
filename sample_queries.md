# Sample Queries for Enhanced Multi-Tenant NLP2SQL System

## TechCorp (PostgreSQL) - Product & Sales Data

### Basic Product Queries
```
Show me all products
List all products in our inventory
What products do we have?
Display product catalog
```

### Enhanced Filtering Queries (Fine-tuned for Ollama)
```
How many products cost less than $50?
Show me products under $100
List products between $25 and $75
Find products over $200
```

### Category & Brand Filtering
```
Count products in Electronics category
Show me all Electronics products
List products in Home & Garden category
How many Clothing items do we have?
Find all products by Apple brand
```

### Advanced Aggregation Queries
```
What's the average product price?
Show me the most expensive product
Find the cheapest item in Electronics
Calculate total inventory value
What's the price range of our products?
```

### Sales & Customer Analysis
```
How many sales did we have this month?
Show me top 10 customers by purchase amount
List recent orders from last week
What's our total revenue this quarter?
Find customers who spent more than $500
```

### Inventory Management
```
Which products are low in stock?
Show inventory levels by warehouse
List products with zero quantity
Find items that need restocking
What's our total inventory count?
```

## HealthPlus (MySQL) - Healthcare Data

### Patient Management
```
How many patients do we have?
Show me all active patients
List patients by age group
Find patients born in 1985
Count male vs female patients
```

### Appointment Scheduling
```
How many appointments today?
Show me tomorrow's schedule
List pending appointments
Find cancelled appointments this week
What's the average appointment duration?
```

### Medical Records & Treatments
```
Show treatments by Dr. Smith
List all cardiology procedures
Find patients with diabetes diagnosis
Count emergency room visits
What's the most common treatment type?
```

### Billing & Insurance
```
Show unpaid bills over $1000
List insurance claims this month
Find patients with outstanding balances
Calculate total revenue from treatments
Show average treatment costs
```

## FinanceHub (PostgreSQL) - Financial Data

### Account Management
```
Show all active accounts
List accounts with balance over $10000
Find accounts opened this year
Count business vs personal accounts
What's the total deposits this month?
```

### Transaction Analysis
```
Show recent transactions over $5000
List suspicious transactions
Find international transfers
Calculate daily transaction volume
Show top 10 largest transactions
```

### Investment Portfolio
```
Display portfolio performance
Show stocks with gains over 10%
List dividend-paying investments
Find underperforming assets
Calculate total portfolio value
```

## RetailMax (MongoDB) - E-commerce Data

### Product Catalog
```
Show me all products
List products by category
Find products with 5-star ratings
Show discounted items
Count products by brand
```

### Sales & Orders
```
How many orders today?
Show high-value orders over $200
List recent customer purchases
Find best-selling products
Calculate monthly revenue
```

### Customer Analytics
```
Show top customers by spending
Find new customers this month
List customers by location
Show customer loyalty metrics
Find customers with multiple orders
```

## EduLearn (MySQL) - Educational Data

### Student Management
```
How many students are enrolled?
Show students by program
List honor roll students
Find students with GPA over 3.5
Count international students
```

### Course & Enrollment
```
Show most popular courses
List available course sections
Find courses with low enrollment
Calculate average class size
Show course completion rates
```

### Academic Performance
```
Display grade distribution
Show failing students needing help
List Dean's List recipients
Calculate department averages
Find improvement trends
```

## Advanced Multi-Table Queries

### Cross-Reference Analysis
```
Show customers with their order history
List products with their sales performance
Find patients with their treatment costs
Display accounts with transaction summaries
Show students with their course enrollments
```

### Time-Based Analytics
```
Compare sales this month vs last month
Show quarterly growth trends
Find seasonal purchase patterns
Analyze year-over-year performance
Display weekly activity summaries
```

### Business Intelligence Queries
```
What are our top revenue generators?
Show cost vs profit analysis
Find operational efficiency metrics
Calculate customer lifetime value
Display market share by category
```

## Security & Permission Testing

### Role-Based Access
```
# Viewer Role - Read-only queries
Show me product information
List customer details
Display account summaries

# Developer Role - Technical queries
Show database performance metrics
List system usage statistics
Find data quality issues

# Analyst Role - Advanced analytics
Calculate complex financial ratios
Show predictive trend analysis
Generate comprehensive reports

# Manager Role - Department-wide data
Show team performance metrics
List department budgets
Find resource allocation data

# Admin Role - Full system access
Display all organizational data
Show system configuration
List user activity logs
```

## Natural Language Variations

### Conversational Style
```
"Can you show me how our sales are doing?"
"I need to see which products aren't selling well"
"What's the deal with our inventory levels?"
"Tell me about our customer satisfaction"
```

### Business Context Queries
```
"We're planning a promotion - show me products under $30"
"For the board meeting, I need Q3 revenue numbers"
"Help me find patients who missed appointments"
"Show me which courses need more marketing"
```

## Complex Filtering (Enhanced with Ollama Fine-tuning)

### Price Range Filtering
```
Find products between $10 and $50
Show items under twenty dollars
List expensive products over 200 bucks
Products costing exactly $99.99
```

### Date Range Filtering
```
Orders from last 30 days
Sales between January and March
Appointments scheduled next week
Transactions from yesterday
```

### Multiple Condition Filtering
```
Electronics products under $100 with high ratings
Male patients over 65 with diabetes
Large transactions over $10K from business accounts
Computer Science courses with more than 20 students
```

## Testing the Enhanced System

To test these queries:

1. **Start the system:**
   ```bash
   # Terminal 1: API Server
   cd "D:\Fundae\Multi Tenant NLP2SQL"
   python -m src.main
   
   # Terminal 2: Streamlit UI
   python -m streamlit run streamlit_app.py
   ```

2. **Login with organization-specific accounts:**
   - TechCorp: `user@techcorp.com`
   - HealthPlus: `user@healthplus.com`
   - FinanceHub: `user@financehub.com`
   - RetailMax: `user@retailmax.com`
   - EduLearn: `user@edulearn.com`

3. **Try the enhanced filtering queries** to see the Ollama fine-tuning improvements in action!

## Expected Improvements

With the fine-tuned Ollama integration, you should see:
- ✅ Better price filtering: "less than $50" correctly extracts `price < 50`
- ✅ Improved category matching: "Electronics" properly filters category
- ✅ Enhanced count operations: "How many" generates `COUNT(*)` queries
- ✅ Consistent org_id isolation for multi-tenant security
- ✅ More accurate SQL generation for complex natural language queries