// MongoDB Schema for RetailMax (org-004)
// Connect to MongoDB and create RetailMax database

use retailmax_db;

// Products Collection
db.products.insertMany([
    {
        _id: ObjectId(),
        org_id: "org-004",
        product_id: "RETAIL-001",
        name: "Summer T-Shirt",
        category: "Clothing",
        price: 19.99,
        sku: "SHIRT-SUM-001",
        description: "Comfortable cotton summer t-shirt",
        sizes: ["S", "M", "L", "XL"],
        colors: ["Red", "Blue", "Green", "White"],
        created_at: new Date("2024-01-15")
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        product_id: "RETAIL-002",
        name: "Denim Jeans",
        category: "Clothing",
        price: 59.99,
        sku: "JEANS-DEN-002",
        description: "Classic fit denim jeans",
        sizes: ["28", "30", "32", "34", "36"],
        colors: ["Blue", "Black"],
        created_at: new Date("2024-01-16")
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        product_id: "RETAIL-003",
        name: "Running Shoes",
        category: "Footwear",
        price: 89.99,
        sku: "SHOES-RUN-003",
        description: "Lightweight running shoes",
        sizes: ["7", "8", "9", "10", "11", "12"],
        colors: ["Black", "White", "Grey"],
        created_at: new Date("2024-01-17")
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        product_id: "RETAIL-004",
        name: "Baseball Cap",
        category: "Accessories",
        price: 24.99,
        sku: "CAP-BASE-004",
        description: "Adjustable baseball cap",
        sizes: ["One Size"],
        colors: ["Red", "Blue", "Black", "White"],
        created_at: new Date("2024-01-18")
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        product_id: "RETAIL-005",
        name: "Leather Wallet",
        category: "Accessories",
        price: 39.99,
        sku: "WALLET-LEA-005",
        description: "Genuine leather bifold wallet",
        sizes: ["One Size"],
        colors: ["Brown", "Black"],
        created_at: new Date("2024-01-19")
    }
]);

// Inventory Collection
db.inventory.insertMany([
    {
        _id: ObjectId(),
        org_id: "org-004",
        inventory_id: "INV-001",
        product_id: "RETAIL-001",
        store_location: "Downtown Store",
        quantity_by_size: {
            "S": 25,
            "M": 40,
            "L": 35,
            "XL": 20
        },
        total_quantity: 120,
        last_updated: new Date("2024-01-20")
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        inventory_id: "INV-002",
        product_id: "RETAIL-002",
        store_location: "Mall Store",
        quantity_by_size: {
            "28": 15,
            "30": 25,
            "32": 30,
            "34": 25,
            "36": 15
        },
        total_quantity: 110,
        last_updated: new Date("2024-01-21")
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        inventory_id: "INV-003",
        product_id: "RETAIL-003",
        store_location: "Sports Store",
        quantity_by_size: {
            "7": 10,
            "8": 15,
            "9": 20,
            "10": 25,
            "11": 15,
            "12": 10
        },
        total_quantity: 95,
        last_updated: new Date("2024-01-22")
    }
]);

// Sales Collection
db.sales.insertMany([
    {
        _id: ObjectId(),
        org_id: "org-004",
        sale_id: "SALE-001",
        customer: {
            name: "Jennifer Adams",
            email: "jennifer@email.com",
            phone: "555-2001"
        },
        items: [
            {
                product_id: "RETAIL-001",
                name: "Summer T-Shirt",
                size: "M",
                color: "Blue",
                quantity: 2,
                unit_price: 19.99,
                total_price: 39.98
            }
        ],
        total_amount: 39.98,
        payment_method: "Credit Card",
        store_location: "Downtown Store",
        sale_date: new Date("2024-01-25"),
        sales_person: "John Doe"
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        sale_id: "SALE-002",
        customer: {
            name: "Robert Miller",
            email: "robert@email.com",
            phone: "555-2002"
        },
        items: [
            {
                product_id: "RETAIL-002",
                name: "Denim Jeans",
                size: "32",
                color: "Blue",
                quantity: 1,
                unit_price: 59.99,
                total_price: 59.99
            },
            {
                product_id: "RETAIL-004",
                name: "Baseball Cap",
                size: "One Size",
                color: "Red",
                quantity: 1,
                unit_price: 24.99,
                total_price: 24.99
            }
        ],
        total_amount: 84.98,
        payment_method: "Cash",
        store_location: "Mall Store",
        sale_date: new Date("2024-01-26"),
        sales_person: "Jane Smith"
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        sale_id: "SALE-003",
        customer: {
            name: "Lisa Thompson",
            email: "lisa@email.com",
            phone: "555-2003"
        },
        items: [
            {
                product_id: "RETAIL-003",
                name: "Running Shoes",
                size: "9",
                color: "Black",
                quantity: 1,
                unit_price: 89.99,
                total_price: 89.99
            }
        ],
        total_amount: 89.99,
        payment_method: "Debit Card",
        store_location: "Sports Store",
        sale_date: new Date("2024-01-27"),
        sales_person: "Mike Johnson"
    }
]);

// Customers Collection
db.customers.insertMany([
    {
        _id: ObjectId(),
        org_id: "org-004",
        customer_id: "CUST-001",
        name: "Jennifer Adams",
        email: "jennifer@email.com",
        phone: "555-2001",
        address: {
            street: "123 Fashion St",
            city: "Retail City",
            state: "RC",
            zip: "12345"
        },
        loyalty_points: 85,
        total_purchases: 159.97,
        registration_date: new Date("2024-01-15"),
        preferred_categories: ["Clothing", "Accessories"]
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        customer_id: "CUST-002",
        name: "Robert Miller",
        email: "robert@email.com",
        phone: "555-2002",
        address: {
            street: "456 Style Ave",
            city: "Retail City",
            state: "RC",
            zip: "12346"
        },
        loyalty_points: 120,
        total_purchases: 244.97,
        registration_date: new Date("2024-01-16"),
        preferred_categories: ["Clothing", "Footwear"]
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        customer_id: "CUST-003",
        name: "Lisa Thompson",
        email: "lisa@email.com",
        phone: "555-2003",
        address: {
            street: "789 Trend Rd",
            city: "Retail City",
            state: "RC",
            zip: "12347"
        },
        loyalty_points: 95,
        total_purchases: 179.98,
        registration_date: new Date("2024-01-17"),
        preferred_categories: ["Footwear", "Accessories"]
    }
]);

// Store Locations Collection
db.store_locations.insertMany([
    {
        _id: ObjectId(),
        org_id: "org-004",
        store_id: "STORE-001",
        name: "Downtown Store",
        address: {
            street: "100 Main St",
            city: "Retail City",
            state: "RC",
            zip: "12300"
        },
        manager: "Sarah Johnson",
        phone: "555-3001",
        email: "downtown@retailmax.com",
        operating_hours: {
            monday: "9:00 AM - 9:00 PM",
            tuesday: "9:00 AM - 9:00 PM",
            wednesday: "9:00 AM - 9:00 PM",
            thursday: "9:00 AM - 9:00 PM",
            friday: "9:00 AM - 10:00 PM",
            saturday: "9:00 AM - 10:00 PM",
            sunday: "10:00 AM - 8:00 PM"
        },
        categories: ["Clothing", "Accessories"]
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        store_id: "STORE-002",
        name: "Mall Store",
        address: {
            street: "200 Shopping Center Dr",
            city: "Retail City",
            state: "RC",
            zip: "12301"
        },
        manager: "David Wilson",
        phone: "555-3002",
        email: "mall@retailmax.com",
        operating_hours: {
            monday: "10:00 AM - 9:00 PM",
            tuesday: "10:00 AM - 9:00 PM",
            wednesday: "10:00 AM - 9:00 PM",
            thursday: "10:00 AM - 9:00 PM",
            friday: "10:00 AM - 10:00 PM",
            saturday: "10:00 AM - 10:00 PM",
            sunday: "11:00 AM - 7:00 PM"
        },
        categories: ["Clothing", "Accessories", "Footwear"]
    },
    {
        _id: ObjectId(),
        org_id: "org-004",
        store_id: "STORE-003",
        name: "Sports Store",
        address: {
            street: "300 Athletic Way",
            city: "Retail City",
            state: "RC",
            zip: "12302"
        },
        manager: "Emily Davis",
        phone: "555-3003",
        email: "sports@retailmax.com",
        operating_hours: {
            monday: "8:00 AM - 8:00 PM",
            tuesday: "8:00 AM - 8:00 PM",
            wednesday: "8:00 AM - 8:00 PM",
            thursday: "8:00 AM - 8:00 PM",
            friday: "8:00 AM - 9:00 PM",
            saturday: "8:00 AM - 9:00 PM",
            sunday: "9:00 AM - 7:00 PM"
        },
        categories: ["Footwear", "Sports Equipment"]
    }
]);

// Create indexes for better performance
db.products.createIndex({ "org_id": 1, "category": 1 });
db.products.createIndex({ "org_id": 1, "sku": 1 }, { unique: true });
db.sales.createIndex({ "org_id": 1, "sale_date": 1 });
db.sales.createIndex({ "org_id": 1, "customer.email": 1 });
db.inventory.createIndex({ "org_id": 1, "product_id": 1 });
db.customers.createIndex({ "org_id": 1, "email": 1 }, { unique: true });

print("RetailMax MongoDB database setup completed!");
print("Collections created: products, inventory, sales, customers, store_locations");
print("Sample data inserted and indexes created.");