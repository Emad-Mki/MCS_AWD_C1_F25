-- Create admin user (email: admin, password: admin)
INSERT INTO users (name, email, password_hash, is_admin) VALUES
('Admin User', 'admin', 'scrypt:32768:8:1$8O12pUsgOeV2ao9e$9dfdffad298e0f8bd5ca4a37b9b51974ebd4391422e3c39da137679dfdb88f6bdb206aeef63e31ca9531b5c225bf43c3b277e47aa02d27257998446923839075', TRUE);

-- Insert sample offerings with availability and image_url
INSERT INTO offerings (title, description, availability, image_url, is_active) VALUES
('Python Basics Course', 'Learn Python from scratch through practical lessons, exercises, and beginner-friendly projects.', 'available', NULL, TRUE),
('Web Development Program', 'Build modern web applications using HTML, CSS, JavaScript, Flask, and real deployment workflows.', 'available', NULL, TRUE),
('Business Automation Service', 'Automate repetitive business tasks and workflows using practical tools and custom integrations.', 'available', NULL, TRUE),
('Graphic Design Service', 'Get professional design support for branding, digital content, and visual communication needs.', 'coming_soon', NULL, TRUE),
('Membership Coaching Program', 'Join a guided subscription-based coaching program with ongoing support and structured resources.', 'available', NULL, TRUE),
('Excel Automation Training', 'Master spreadsheet automation, formulas, data cleanup, and reporting workflows for business use.', 'ended', NULL, FALSE),
('WhatsApp Integration Service', 'Set up smart communication and customer workflow automation using WhatsApp-based systems.', 'coming_soon', NULL, TRUE);
