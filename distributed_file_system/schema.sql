drop table if exists files;
create table files (
  file_id char(500) primary key,
  transaction_id char(500),
  file LONGBLOB
  shadow_file LONGBLOB
);