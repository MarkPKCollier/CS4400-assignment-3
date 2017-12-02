drop table if exists file;
create table files (
  file_id char(500) primary key,
  file LONGBLOB not null
);