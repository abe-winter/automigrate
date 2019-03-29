-- sql.sql
-- example schema file with git history we rely on in tests

create table t1 (a int primary key, b int);
create index t1a on t1 (a);
create table t2 (a int primary key);
