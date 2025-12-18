-- EduLearn MySQL Database Initialization
USE edulearn_db;

-- Students table
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    student_number VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE NOT NULL,
    enrollment_date DATE NOT NULL,
    graduation_date DATE,
    status ENUM('Active', 'Inactive', 'Graduated', 'Suspended') DEFAULT 'Active',
    major VARCHAR(100),
    minor VARCHAR(100),
    gpa DECIMAL(3,2),
    total_credits INT DEFAULT 0,
    address TEXT,
    emergency_contact VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Instructors table
CREATE TABLE instructors (
    instructor_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    employee_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    department VARCHAR(100) NOT NULL,
    title VARCHAR(50),
    hire_date DATE NOT NULL,
    office_location VARCHAR(50),
    specializations TEXT,
    years_experience INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses table
CREATE TABLE courses (
    course_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    description TEXT,
    department VARCHAR(100) NOT NULL,
    credits INT NOT NULL,
    prerequisites TEXT,
    level ENUM('Undergraduate', 'Graduate', 'Doctoral') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Course sections table
CREATE TABLE course_sections (
    section_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    course_id INT NOT NULL,
    instructor_id INT NOT NULL,
    section_number VARCHAR(10) NOT NULL,
    semester VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    schedule_days VARCHAR(20),
    schedule_time VARCHAR(50),
    classroom VARCHAR(50),
    max_capacity INT NOT NULL,
    current_enrollment INT DEFAULT 0,
    status ENUM('Open', 'Closed', 'Cancelled') DEFAULT 'Open',
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id),
    UNIQUE KEY unique_section (course_id, section_number, semester, year)
);

-- Enrollments table
CREATE TABLE enrollments (
    enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    student_id INT NOT NULL,
    section_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    grade VARCHAR(5),
    status ENUM('Enrolled', 'Dropped', 'Completed', 'Incomplete') DEFAULT 'Enrolled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (section_id) REFERENCES course_sections(section_id),
    UNIQUE KEY unique_enrollment (student_id, section_id)
);

-- Grades table
CREATE TABLE grades (
    grade_id INT PRIMARY KEY AUTO_INCREMENT,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    enrollment_id INT NOT NULL,
    assignment_name VARCHAR(200) NOT NULL,
    assignment_type ENUM('Exam', 'Quiz', 'Homework', 'Project', 'Participation') NOT NULL,
    points_earned DECIMAL(6,2),
    points_possible DECIMAL(6,2) NOT NULL,
    percentage DECIMAL(5,2) GENERATED ALWAYS AS ((points_earned / points_possible) * 100) STORED,
    grade_date DATE NOT NULL,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
);

-- Insert sample data
INSERT INTO students (student_number, first_name, last_name, email, phone, date_of_birth, enrollment_date, major, gpa, total_credits, address, emergency_contact) VALUES
('ST001001', 'Emma', 'Williams', 'emma.williams@edulearn.edu', '555-1001', '2002-05-15', '2020-08-15', 'Computer Science', 3.75, 85, '100 College St, Apt 1A', 'Mary Williams 555-1002'),
('ST001002', 'Liam', 'Brown', 'liam.brown@edulearn.edu', '555-1003', '2001-09-22', '2019-08-20', 'Business Administration', 3.45, 98, '200 University Ave, Room 205', 'Robert Brown 555-1004'),
('ST001003', 'Olivia', 'Jones', 'olivia.jones@edulearn.edu', '555-1005', '2003-01-10', '2021-08-18', 'Psychology', 3.90, 72, '300 Student Dr, Apt 3B', 'Sarah Jones 555-1006'),
('ST001004', 'Noah', 'Garcia', 'noah.garcia@edulearn.edu', '555-1007', '2002-11-30', '2020-08-15', 'Engineering', 3.60, 88, '400 Campus Rd, Dorm B301', 'Carlos Garcia 555-1008'),
('ST001005', 'Ava', 'Miller', 'ava.miller@edulearn.edu', '555-1009', '2001-07-18', '2019-08-20', 'Biology', 3.85, 105, '500 Academic Way, Apt 2C', 'Jennifer Miller 555-1010');

INSERT INTO instructors (employee_id, first_name, last_name, email, phone, department, title, hire_date, office_location, specializations, years_experience) VALUES
('EMP001', 'Dr. Michael', 'Johnson', 'michael.johnson@edulearn.edu', '555-2001', 'Computer Science', 'Professor', '2010-08-15', 'CS Building 301', 'Artificial Intelligence, Machine Learning', 15),
('EMP002', 'Prof. Lisa', 'Davis', 'lisa.davis@edulearn.edu', '555-2002', 'Business Administration', 'Associate Professor', '2015-01-20', 'Business Hall 205', 'Finance, Strategic Management', 12),
('EMP003', 'Dr. James', 'Wilson', 'james.wilson@edulearn.edu', '555-2003', 'Psychology', 'Professor', '2008-09-01', 'Psychology Building 150', 'Cognitive Psychology, Research Methods', 18),
('EMP004', 'Prof. Sarah', 'Martinez', 'sarah.martinez@edulearn.edu', '555-2004', 'Engineering', 'Assistant Professor', '2018-08-25', 'Engineering Center 420', 'Civil Engineering, Structural Design', 8),
('EMP005', 'Dr. Robert', 'Anderson', 'robert.anderson@edulearn.edu', '555-2005', 'Biology', 'Professor', '2005-01-10', 'Science Building 275', 'Molecular Biology, Genetics', 22);

INSERT INTO courses (course_code, course_name, description, department, credits, prerequisites, level) VALUES
('CS101', 'Introduction to Programming', 'Basic programming concepts using Python', 'Computer Science', 3, 'None', 'Undergraduate'),
('CS201', 'Data Structures and Algorithms', 'Advanced programming with data structures', 'Computer Science', 4, 'CS101', 'Undergraduate'),
('BUS101', 'Principles of Management', 'Introduction to business management concepts', 'Business Administration', 3, 'None', 'Undergraduate'),
('BUS301', 'Financial Management', 'Advanced financial planning and analysis', 'Business Administration', 3, 'BUS101, MATH110', 'Undergraduate'),
('PSY101', 'General Psychology', 'Introduction to psychological principles', 'Psychology', 3, 'None', 'Undergraduate'),
('PSY301', 'Research Methods in Psychology', 'Statistical methods and research design', 'Psychology', 4, 'PSY101, STAT200', 'Undergraduate'),
('ENG201', 'Statics and Dynamics', 'Principles of engineering mechanics', 'Engineering', 4, 'MATH201, PHYS201', 'Undergraduate'),
('BIO101', 'General Biology I', 'Introduction to biological sciences', 'Biology', 4, 'None', 'Undergraduate'),
('BIO301', 'Molecular Biology', 'Advanced molecular and cellular biology', 'Biology', 4, 'BIO101, CHEM201', 'Undergraduate');

INSERT INTO course_sections (course_id, instructor_id, section_number, semester, year, schedule_days, schedule_time, classroom, max_capacity) VALUES
(1, 1, '001', 'Fall', 2024, 'MWF', '9:00-9:50 AM', 'CS Lab 101', 30),
(2, 1, '001', 'Spring', 2024, 'TTh', '10:00-11:15 AM', 'CS Lab 102', 25),
(3, 2, '001', 'Fall', 2024, 'MWF', '11:00-11:50 AM', 'Business 201', 40),
(4, 2, '001', 'Spring', 2024, 'TTh', '1:00-2:15 PM', 'Business 205', 35),
(5, 3, '001', 'Fall', 2024, 'MWF', '2:00-2:50 PM', 'Psychology 150', 50),
(6, 3, '001', 'Spring', 2024, 'TTh', '3:30-4:45 PM', 'Psychology 175', 30),
(7, 4, '001', 'Fall', 2024, 'MWF', '10:00-10:50 AM', 'Engineering 301', 35),
(8, 5, '001', 'Fall', 2024, 'TTh', '8:00-9:15 AM', 'Science 101', 40),
(9, 5, '001', 'Spring', 2024, 'MWF', '1:00-1:50 PM', 'Science 275', 25);

INSERT INTO enrollments (student_id, section_id, enrollment_date, status) VALUES
(1, 1, '2024-08-20', 'Enrolled'),
(1, 5, '2024-08-20', 'Enrolled'),
(2, 3, '2024-08-20', 'Enrolled'),
(2, 4, '2024-01-15', 'Completed'),
(3, 5, '2024-08-20', 'Enrolled'),
(3, 6, '2024-01-15', 'Completed'),
(4, 7, '2024-08-20', 'Enrolled'),
(4, 1, '2024-08-20', 'Enrolled'),
(5, 8, '2024-08-20', 'Enrolled'),
(5, 9, '2024-01-15', 'Completed');

INSERT INTO grades (enrollment_id, assignment_name, assignment_type, points_earned, points_possible, grade_date) VALUES
(1, 'Midterm Exam', 'Exam', 85.0, 100.0, '2024-10-15'),
(1, 'Programming Project 1', 'Project', 92.0, 100.0, '2024-09-30'),
(1, 'Quiz 1', 'Quiz', 18.0, 20.0, '2024-09-15'),
(2, 'Final Exam', 'Exam', 88.0, 100.0, '2024-05-10'),
(3, 'Research Paper', 'Project', 95.0, 100.0, '2024-11-01'),
(4, 'Financial Analysis Project', 'Project', 87.0, 100.0, '2024-04-25'),
(5, 'Midterm Exam', 'Exam', 91.0, 100.0, '2024-10-20'),
(6, 'Research Proposal', 'Project', 89.0, 100.0, '2024-04-15'),
(7, 'Problem Set 1', 'Homework', 95.0, 100.0, '2024-09-25'),
(8, 'Lab Report 1', 'Homework', 90.0, 100.0, '2024-09-20'),
(9, 'Final Project', 'Project', 93.0, 100.0, '2024-05-05');