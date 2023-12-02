-- Create the users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR NOT NULL,
    ditto_unit_url VARCHAR
);

-- Create the conversations table with a foreign key reference to users
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    viewed_at TIMESTAMP NOT NULL,
    chat_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create the chats table with foreign key references to conversations
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conv_id INTEGER NOT NULL,
    is_user BOOLEAN NOT NULL,
    msg VARCHAR NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (conv_id) REFERENCES conversations(id)
);

-- Create the migrations table
CREATE TABLE IF NOT EXISTS migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    executed_at TIMESTAMP NOT NULL
);

-- Insert sample data into users and conversations tables
INSERT INTO
    users (username, ditto_unit_url)
SELECT
    'user1',
    'http://localhost:42032'
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            users
    );

INSERT INTO
    conversations (user_id, title, created_at, viewed_at)
SELECT
    1,
    'sample conversation',
    datetime('now'),
    datetime('now')
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            conversations
    );

-- Insert sample data into migrations table
INSERT INTO
    migrations (name, executed_at)
SELECT
    'create_tables',
    datetime('now')
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            migrations
        WHERE
            name = 'create_tables'
            AND id = 1
    );