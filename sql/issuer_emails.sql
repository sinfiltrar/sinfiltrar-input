CREATE TABLE issuer_emails
(
    email varchar(255) PRIMARY KEY,
    issuer_id varchar(255),
    created_at timestamp NOT NULL DEFAULT current_timestamp
);
