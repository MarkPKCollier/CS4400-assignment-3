drop table if exists clients;
create table clients (
  id integer primary key autoincrement,
  password char(500),
  access_level char(1)
);