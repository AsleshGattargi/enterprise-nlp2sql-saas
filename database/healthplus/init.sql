-- HealthPlus MySQL Database Initialization
USE healthplus_db;

-- Patients table
CREATE TABLE patients (
    patient_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('M', 'F', 'Other') NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    emergency_contact VARCHAR(100),
    insurance_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Doctors table
CREATE TABLE doctors (
    doctor_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    specialization VARCHAR(100),
    license_number VARCHAR(50) UNIQUE,
    phone VARCHAR(20),
    email VARCHAR(100),
    department VARCHAR(50),
    years_experience INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treatments table
CREATE TABLE treatments (
    treatment_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    treatment_name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    base_cost DECIMAL(10,2),
    duration_minutes INT,
    requires_equipment BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments table
CREATE TABLE appointments (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    treatment_id INT,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled', 'No-Show') DEFAULT 'Scheduled',
    notes TEXT,
    total_cost DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id)
);

-- Medical records table
CREATE TABLE medical_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_id INT,
    diagnosis TEXT,
    prescription TEXT,
    lab_results TEXT,
    record_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- Insert sample data
INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address, emergency_contact, insurance_id) VALUES
('Alice', 'Johnson', '1985-03-15', 'F', '555-0101', 'alice.johnson@email.com', '123 Maple St, City', 'Bob Johnson 555-0102', 'INS001'),
('Charlie', 'Brown', '1990-07-22', 'M', '555-0103', 'charlie.brown@email.com', '456 Oak Ave, City', 'Mary Brown 555-0104', 'INS002'),
('Eva', 'Davis', '1978-11-08', 'F', '555-0105', 'eva.davis@email.com', '789 Pine Rd, City', 'John Davis 555-0106', 'INS003'),
('Michael', 'Wilson', '1992-05-30', 'M', '555-0107', 'michael.wilson@email.com', '321 Elm St, City', 'Sarah Wilson 555-0108', 'INS004'),
('Sarah', 'Martinez', '1988-12-18', 'F', '555-0109', 'sarah.martinez@email.com', '654 Birch Ave, City', 'Carlos Martinez 555-0110', 'INS005');

INSERT INTO doctors (first_name, last_name, specialization, license_number, phone, email, department, years_experience) VALUES
('Dr. James', 'Smith', 'Cardiology', 'LIC001', '555-0201', 'dr.smith@healthplus.org', 'Cardiology', 15),
('Dr. Emily', 'Johnson', 'Pediatrics', 'LIC002', '555-0202', 'dr.johnson@healthplus.org', 'Pediatrics', 8),
('Dr. Robert', 'Wilson', 'Orthopedics', 'LIC003', '555-0203', 'dr.wilson@healthplus.org', 'Orthopedics', 12),
('Dr. Lisa', 'Garcia', 'Dermatology', 'LIC004', '555-0204', 'dr.garcia@healthplus.org', 'Dermatology', 6),
('Dr. David', 'Rodriguez', 'Internal Medicine', 'LIC005', '555-0205', 'dr.rodriguez@healthplus.org', 'Internal Medicine', 20);

INSERT INTO treatments (treatment_name, description, category, base_cost, duration_minutes, requires_equipment) VALUES
('Annual Checkup', 'Comprehensive annual physical examination', 'Preventive Care', 150.00, 60, FALSE),
('Blood Test', 'Complete blood count and chemistry panel', 'Diagnostic', 85.00, 15, TRUE),
('X-Ray', 'Digital X-ray imaging', 'Diagnostic', 120.00, 30, TRUE),
('ECG', 'Electrocardiogram heart monitoring', 'Diagnostic', 95.00, 20, TRUE),
('Vaccination', 'Immunization administration', 'Preventive Care', 45.00, 15, FALSE),
('Physical Therapy Session', 'Rehabilitation therapy session', 'Therapeutic', 80.00, 45, FALSE),
('Dermatology Consultation', 'Skin condition assessment', 'Consultation', 200.00, 45, FALSE);

INSERT INTO appointments (patient_id, doctor_id, treatment_id, appointment_date, appointment_time, status, total_cost) VALUES
(1, 1, 1, '2024-01-15', '09:00:00', 'Completed', 150.00),
(2, 2, 2, '2024-01-16', '10:30:00', 'Completed', 85.00),
(3, 3, 3, '2024-01-17', '14:00:00', 'Completed', 120.00),
(4, 4, 4, '2024-01-18', '11:15:00', 'Completed', 95.00),
(5, 5, 1, '2024-01-19', '15:30:00', 'Completed', 150.00),
(1, 2, 5, '2024-01-20', '08:45:00', 'Scheduled', 45.00),
(2, 3, 6, '2024-01-21', '13:00:00', 'Scheduled', 80.00);

INSERT INTO medical_records (patient_id, doctor_id, appointment_id, diagnosis, prescription, record_date) VALUES
(1, 1, 1, 'Hypertension, well controlled', 'Lisinopril 10mg daily, continue current regimen', '2024-01-15'),
(2, 2, 2, 'Iron deficiency anemia', 'Iron sulfate 325mg twice daily, recheck in 6 weeks', '2024-01-16'),
(3, 3, 3, 'Mild osteoarthritis in knee', 'Physical therapy 3x/week, ibuprofen as needed', '2024-01-17'),
(4, 4, 4, 'Normal cardiac rhythm', 'No treatment required, annual follow-up', '2024-01-18'),
(5, 5, 5, 'Routine physical - healthy', 'Continue current lifestyle, annual checkup', '2024-01-19');