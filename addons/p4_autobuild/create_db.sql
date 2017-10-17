create table p4_paths (
  id serial not null primary key,
  path text not null);
create table bld_watches (
  id serial not null primary key,
  name text not null unique);
create table bld_watches_paths (
  path_id int not null references p4_paths,
  watch_id int not null references bld_watches);

create table bld_subscribers (
  id serial not null primary key,
  email text not null unique);
create table bld_subscribers_watches (
  subscriber_id int not null references bld_subscribers,
  watch_id int not null references bld_watches,
  primary key(subscriber_id, watch_id));

create table ovt_testrun (
  id int not null primary key,
  completed bool not null default false,
  passed bool default null,
  notified bool not null default false);

create table p4_changes (
  changelist int not null,
  username text not null,
  watch_id int not null references bld_watches,
  primary key (changelist, watch_id),
  overtest_testrun_id int references ovt_testrun);

-- smtp_fqdn and smtp_port ought to be in a seperate table but at the moment
-- it's unnecessary complication
create table bld_host_configs (
  fqdn text not null primary key,
  smtp_fqdn text not null,
  smtp_port int not null);
insert into bld_host_config (fqdn, smtp_fqdn, smtp_port)
       values ('meta01.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25), 
              ('meta02.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25), 
              ('meta03.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25), 
              ('meta04.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25), 
              ('meta05.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25), 
              ('klmeta05.kl.imgtec.org', 'klmail01.kl.imgtec.org', 25),
              ('klmeta06.kl.imgtec.org', 'klmail01.kl.imgtec.org', 25),
              ('cosy01.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25),
              ('cosy02.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25),
              ('cosy03.kl.imgtec.org',   'klmail01.kl.imgtec.org', 25);

create or replace view bld_subscribers_for_watch as
       select bld_subscribers_watches.watch_id, bld_subscribers.id as subscriber_id, bld_subscribers.email
              from bld_subscribers_watches join bld_subscribers
              on bld_subscribers_watches.subscriber_id = bld_subscribers.id;

create or replace view bld_watches_for_subscriber as
       select bld_subscribers_watches.subscriber_id, bld_watches.id as watch_id, bld_watches.name
              from bld_subscribers_watches join bld_watches
              on bld_subscribers_watches.watch_id = bld_watches.id;

create or replace view p4_paths_for_watch as
       select bld_watches_paths.watch_id, p4_paths.id as path_id, p4_paths.path
              from bld_watches_paths join p4_paths
              on bld_watches_paths.path_id = p4_paths.id;
