CREATE TABLE docs
(
    id varchar(255) PRIMARY KEY,  -- the s3 object key
    from_email varchar(255),
    slug varchar(255),  -- for user facing id
    issued_at timestamp,
    title varchar(255),
    short_text varchar(255),
    body_html text,  -- html
    body_plain text,  -- just words
    body_md text DEFAULT NULL,  -- only basic styling and images from html
    media jsonb,
    meta jsonb,
    created_at timestamp NOT NULL DEFAULT current_timestamp
);
