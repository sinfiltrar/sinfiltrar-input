CREATE TABLE issuers
(
    id varchar(255) PRIMARY KEY,
    slug varchar(255),
    name varchar(255),
    created_at timestamp NOT NULL DEFAULT current_timestamp
);
