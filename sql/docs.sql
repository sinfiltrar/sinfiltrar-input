CREATE TABLE docs
(
    id varchar(255) PRIMARY KEY,
    from_email varchar(255),
    slug varchar(255),
    subject varchar(255),
    short_text varchar(255),
    body text,
    body_plain text,
    attachments jsonb,
    meta jsonb,
    received_at timestamp,
    created_at timestamp NOT NULL DEFAULT current_timestamp
);
