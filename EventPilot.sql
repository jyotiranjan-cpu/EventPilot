-- 1. Create and Use Database
CREATE DATABASE IF NOT EXISTS EventPilot;
USE EventPilot;

-- 2. Create Admin Table (Must be created first for Foreign Keys)
CREATE TABLE IF NOT EXISTS admin_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'superadmin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

insert into admin_data(username,email,password_hash,role) values('Jyotiranjan','jyotiranjann135@gmail.com',
'scrypt:32768:8:1$7lF5PdZmAhXyPKou$9c2423aa0e8ee876b6f2c96b9557e9ded0189171f80422e3ea694b822eda34ce2d53f8b78b373e23c3b8d6603c686e83ed5edb76f43fc08e7988f87e1f481207','superadmin');
-- password: Jyoti2005

-- 3. Create Organizer (User) Table
CREATE TABLE IF NOT EXISTS user_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    firstname VARCHAR(50),
    lastname VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_no VARCHAR(20),  -- Changed to VARCHAR for symbols like +91
    address TEXT,
    state varchar(50),
    city VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



-- 4. Create Vendor Table (With Verification Logic)
CREATE TABLE IF NOT EXISTS vendor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Personal Login Info
    firstname VARCHAR(50),
    lastname VARCHAR(50),
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_no VARCHAR(20),

    -- Business Details
    business_name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- e.g. 'Catering', 'DJ'
    description TEXT,
    address TEXT,
    state varchar(50),
    city VARCHAR(50),
    starting_price DECIMAL(10,2),
    
    -- Verification Logic (As requested)
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    verified_by INT, -- Link to the Admin who clicked 'Approve'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Connect verified_by to Admin Table
    FOREIGN KEY (verified_by) REFERENCES admin_data(id) ON DELETE SET NULL
);

-- 5. Create Bookings Table (Connects User & Vendor)
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    vendor_id INT NOT NULL,
    event_date DATE NOT NULL,
    event_type VARCHAR(50), -- e.g. 'Wedding', 'Birthday'
    status ENUM('pending', 'accepted', 'rejected', 'completed', 'cancelled') DEFAULT 'pending',
    total_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Links
    FOREIGN KEY (user_id) REFERENCES user_data(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_id) REFERENCES vendor_data(id) ON DELETE CASCADE
);

USE EventPilot;

CREATE TABLE IF NOT EXISTS otp_store (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    purpose text NOT NULL, -- e.g. 'registration', 'login', 'reset_pass'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS temp_registrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
