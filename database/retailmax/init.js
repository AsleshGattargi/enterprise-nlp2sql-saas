// RetailMax MongoDB Database Initialization
db = db.getSiblingDB('retailmax_db');

// Create collections and insert sample data

// Products collection
db.products.insertMany([
    {
        product_id: "PROD001",
        org_id: "org-004",
        name: "Wireless Bluetooth Headphones",
        category: "Electronics",
        subcategory: "Audio",
        brand: "TechSound",
        price: 99.99,
        cost: 45.00,
        sku: "TS-WBH-001",
        barcode: "1234567890123",
        description: "High-quality wireless Bluetooth headphones with noise cancellation",
        specifications: {
            battery_life: "30 hours",
            connectivity: "Bluetooth 5.0",
            weight: "250g",
            color_options: ["Black", "White", "Blue"]
        },
        inventory: {
            quantity_available: 150,
            quantity_reserved: 25,
            reorder_level: 20,
            warehouse_location: "A-15-3"
        },
        supplier: {
            supplier_id: "SUP001",
            name: "TechSound Manufacturing",
            contact: "orders@techsound.com"
        },
        created_at: new Date("2023-01-15"),
        updated_at: new Date("2024-01-15")
    },
    {
        product_id: "PROD002",
        org_id: "org-004",
        name: "Smartphone Case Premium",
        category: "Accessories",
        subcategory: "Phone Cases",
        brand: "GuardPro",
        price: 29.99,
        cost: 12.50,
        sku: "GP-SCP-002",
        barcode: "1234567890124",
        description: "Premium protective smartphone case with military-grade protection",
        specifications: {
            material: "TPU + PC",
            compatibility: ["iPhone 14", "iPhone 15"],
            features: ["Drop Protection", "Wireless Charging Compatible"]
        },
        inventory: {
            quantity_available: 300,
            quantity_reserved: 45,
            reorder_level: 50,
            warehouse_location: "B-08-2"
        },
        supplier: {
            supplier_id: "SUP002",
            name: "GuardPro Accessories",
            contact: "sales@guardpro.com"
        },
        created_at: new Date("2023-02-20"),
        updated_at: new Date("2024-01-16")
    },
    {
        product_id: "PROD003",
        org_id: "org-004",
        name: "Gaming Mechanical Keyboard",
        category: "Electronics",
        subcategory: "Computer Peripherals",
        brand: "GameMaster",
        price: 149.99,
        cost: 75.00,
        sku: "GM-GMK-003",
        barcode: "1234567890125",
        description: "RGB mechanical gaming keyboard with custom switches",
        specifications: {
            switch_type: "Blue Mechanical",
            backlight: "RGB",
            connectivity: "USB-C",
            layout: "Full Size"
        },
        inventory: {
            quantity_available: 85,
            quantity_reserved: 15,
            reorder_level: 25,
            warehouse_location: "C-12-1"
        },
        supplier: {
            supplier_id: "SUP003",
            name: "GameMaster Electronics",
            contact: "wholesale@gamemaster.com"
        },
        created_at: new Date("2023-03-10"),
        updated_at: new Date("2024-01-17")
    }
]);

// Customers collection
db.customers.insertMany([
    {
        customer_id: "CUST001",
        org_id: "org-004",
        first_name: "John",
        last_name: "Smith",
        email: "john.smith@email.com",
        phone: "555-0101",
        address: {
            street: "123 Main St",
            city: "Seattle",
            state: "WA",
            zip_code: "98101",
            country: "USA"
        },
        demographics: {
            age_group: "35-44",
            gender: "M",
            income_bracket: "75k-100k"
        },
        preferences: {
            categories: ["Electronics", "Gaming"],
            brands: ["TechSound", "GameMaster"],
            communication: "email",
            language: "English"
        },
        loyalty: {
            tier: "Gold",
            points: 2500,
            total_spent: 1250.75,
            member_since: new Date("2022-06-15")
        },
        created_at: new Date("2022-06-15"),
        updated_at: new Date("2024-01-15")
    },
    {
        customer_id: "CUST002",
        org_id: "org-004",
        first_name: "Sarah",
        last_name: "Johnson",
        email: "sarah.johnson@email.com",
        phone: "555-0102",
        address: {
            street: "456 Oak Ave",
            city: "Portland",
            state: "OR",
            zip_code: "97201",
            country: "USA"
        },
        demographics: {
            age_group: "25-34",
            gender: "F",
            income_bracket: "50k-75k"
        },
        preferences: {
            categories: ["Accessories", "Electronics"],
            brands: ["GuardPro"],
            communication: "sms",
            language: "English"
        },
        loyalty: {
            tier: "Silver",
            points: 850,
            total_spent: 425.50,
            member_since: new Date("2023-01-20")
        },
        created_at: new Date("2023-01-20"),
        updated_at: new Date("2024-01-16")
    }
]);

// Orders collection
db.orders.insertMany([
    {
        order_id: "ORD001",
        org_id: "org-004",
        customer_id: "CUST001",
        order_date: new Date("2024-01-15"),
        status: "Delivered",
        payment: {
            method: "Credit Card",
            card_last4: "1234",
            amount_paid: 179.97,
            payment_date: new Date("2024-01-15"),
            transaction_id: "TXN001"
        },
        shipping: {
            method: "Standard",
            address: {
                street: "123 Main St",
                city: "Seattle",
                state: "WA",
                zip_code: "98101",
                country: "USA"
            },
            cost: 9.99,
            tracking_number: "TRK001",
            shipped_date: new Date("2024-01-16"),
            delivered_date: new Date("2024-01-18")
        },
        items: [
            {
                product_id: "PROD001",
                name: "Wireless Bluetooth Headphones",
                quantity: 1,
                unit_price: 99.99,
                total_price: 99.99
            },
            {
                product_id: "PROD003",
                name: "Gaming Mechanical Keyboard",
                quantity: 1,
                unit_price: 149.99,
                total_price: 149.99
            }
        ],
        totals: {
            subtotal: 249.98,
            tax: 19.99,
            shipping: 9.99,
            discount: 0.00,
            total: 279.96
        },
        created_at: new Date("2024-01-15"),
        updated_at: new Date("2024-01-18")
    },
    {
        order_id: "ORD002",
        org_id: "org-004",
        customer_id: "CUST002",
        order_date: new Date("2024-01-16"),
        status: "Processing",
        payment: {
            method: "PayPal",
            amount_paid: 32.48,
            payment_date: new Date("2024-01-16"),
            transaction_id: "TXN002"
        },
        shipping: {
            method: "Express",
            address: {
                street: "456 Oak Ave",
                city: "Portland",
                state: "OR",
                zip_code: "97201",
                country: "USA"
            },
            cost: 14.99,
            tracking_number: "TRK002"
        },
        items: [
            {
                product_id: "PROD002",
                name: "Smartphone Case Premium",
                quantity: 2,
                unit_price: 29.99,
                total_price: 59.98
            }
        ],
        totals: {
            subtotal: 59.98,
            tax: 4.80,
            shipping: 14.99,
            discount: 10.00,
            total: 69.77
        },
        created_at: new Date("2024-01-16"),
        updated_at: new Date("2024-01-16")
    }
]);

// Sales analytics collection
db.sales_analytics.insertMany([
    {
        date: new Date("2024-01-15"),
        org_id: "org-004",
        daily_metrics: {
            total_orders: 5,
            total_revenue: 1250.50,
            total_units_sold: 12,
            average_order_value: 250.10,
            new_customers: 2
        },
        product_performance: [
            {
                product_id: "PROD001",
                units_sold: 3,
                revenue: 299.97
            },
            {
                product_id: "PROD002",
                units_sold: 7,
                revenue: 209.93
            },
            {
                product_id: "PROD003",
                units_sold: 2,
                revenue: 299.98
            }
        ],
        category_performance: [
            {
                category: "Electronics",
                revenue: 599.95,
                units_sold: 5
            },
            {
                category: "Accessories",
                revenue: 209.93,
                units_sold: 7
            }
        ]
    }
]);

// Inventory tracking collection
db.inventory_movements.insertMany([
    {
        movement_id: "MOV001",
        org_id: "org-004",
        product_id: "PROD001",
        movement_type: "Sale",
        quantity: -1,
        reference_id: "ORD001",
        timestamp: new Date("2024-01-15T10:30:00Z"),
        notes: "Order fulfillment"
    },
    {
        movement_id: "MOV002",
        org_id: "org-004",
        product_id: "PROD002",
        movement_type: "Sale",
        quantity: -2,
        reference_id: "ORD002",
        timestamp: new Date("2024-01-16T14:15:00Z"),
        notes: "Order fulfillment"
    },
    {
        movement_id: "MOV003",
        org_id: "org-004",
        product_id: "PROD001",
        movement_type: "Restock",
        quantity: 50,
        reference_id: "PO001",
        timestamp: new Date("2024-01-17T09:00:00Z"),
        notes: "Purchase order delivery"
    }
]);

// Create indexes for better query performance
db.products.createIndex({ "product_id": 1 });
db.products.createIndex({ "org_id": 1 });
db.products.createIndex({ "category": 1, "subcategory": 1 });
db.products.createIndex({ "sku": 1 });

db.customers.createIndex({ "customer_id": 1 });
db.customers.createIndex({ "org_id": 1 });
db.customers.createIndex({ "email": 1 });

db.orders.createIndex({ "order_id": 1 });
db.orders.createIndex({ "org_id": 1 });
db.orders.createIndex({ "customer_id": 1 });
db.orders.createIndex({ "order_date": 1 });
db.orders.createIndex({ "status": 1 });

db.sales_analytics.createIndex({ "date": 1, "org_id": 1 });
db.inventory_movements.createIndex({ "product_id": 1, "timestamp": 1 });