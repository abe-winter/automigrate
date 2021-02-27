-- sql.sql
-- example schema file with git history we rely on in tests

create extension if not exists "uuid-ossp";

create type letters as enum ('a', 'b');

create table t1 (a int primary key, b text);
create index t1a on t1 (a);
create table t2 (a int primary key);
