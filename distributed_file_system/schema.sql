drop table if exists files;
create table files (
  file_id char(500) primary key,
  transaction_id varchar(500),
  last_update_user_id integer,
  file LONGBLOB,
  shadow_file LONGBLOB
);