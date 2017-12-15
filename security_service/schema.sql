drop table if exists clients;
create table clients (
  id integer primary key autoincrement,
  password char(500),
  access_level char(1)
);

insert into clients (password, access_level) values ('test1', 'a');
insert into clients (password, access_level) values ('test1', 'a');
insert into clients (password, access_level) values ('test1', 'a');