drop table if exists clients;
create table clients (
  id integer primary key autoincrement,
  password char(500)
);