drop table if exists locks;
create table locks (
  file_id char(500) primary key,
  locked int not null
);