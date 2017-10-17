#!/usr/bin/perl
use warnings;
use strict;

use File::Temp qw(tempdir);
use lib "./plugins";
use IMG::AutoBuild::Plugin;
use YAML qw(LoadFile);

my $CONFIG = LoadFile("autobuild.cfg");
my $DIR    = $$CONFIG{'scan-directory'};
my $DELETE = $$CONFIG{'delete-processed'};
our $CVSROOT= $$CONFIG{'cvsroot'};

my @files = find_valid_files ($DIR);

# Convert to full path
@files = map { $_ = "$DIR/$_" } @files;

exit 0 if scalar (@files) == 0;

for my $jobfile (@files)
{
  print "$jobfile\n";
  my %file = parse_file ($jobfile);
  my $diff = fetch_diff ("$file{repo}/$file{file}", $file{old_version}, $file{new_version});
  my @cmps = find_new_components ($diff);
  submit_jobs ($file{'options'}, @cmps);
  unlink $jobfile if $DELETE;
}

sub find_valid_files
{
  my $dir = shift @_;
  opendir my $dh, $dir or die "Could not find directory";
  my @files = readdir $dh;
  closedir $dh;

# Remove . and ..
  @files = grep !/^\.\.?$/, @files;

# Remove partially written files (i.e. ones without group read)
  @files = grep { -r "$dir/$_" } @files;

  return @files;
}

sub parse_file
{
  my $fn = shift @_;

  my %data = ('options' => {});
  my $std = 1;

  open my $fh, "<", "$fn" or die "Could not open file";
  while (<$fh>)
  {
    if ($std)
    {
      /REPO='(.*)'/ and do
        {
          $data{repo} = $1;
          next;
        };
      /FILE='(.*)'/ and do
        {
          $data{file} = $1;
          next;
        };
      /OLD='(.*)'/ and do
        {
          $data{old_version} = $1;
          next;
        };
      /NEW='(.*)'/ and do
        {
          $data{new_version} = $1;
          next;
        };
      /---/ and do
        {
          $std = 0;
          next;
        };
    }
    else
    {
      /([^=]+)='(.*)'/ and do
        {
          $data{options}{$1} = $2;
          next;
        };
    }
    warn "Unrecognised line '$_'";
  }
  close $fh;

  return %data;
}

sub fetch_diff
{
  my ($file, $old, $new) = @_;
  my $diff = `cvs -d$CVSROOT rdiff -r$old -r$new $file`;
  return $diff;
}

sub find_new_components
{
  my $diff = shift @_;
  my @lines = split /\n/, $diff;

  my @components;

  for (@lines)
  {
    push @components, { name => $1, new_version => $2 } if /\+ CMP (\w+)\((\d+(?:\.\d+)*),/;
  }

  return @components;
}

sub submit_jobs
{
  my %options = %{shift @_};
  my @components = @_;

  for my $cmp (@components)
  {
    my $name        = $$cmp{name};
    my $new_version = $$cmp{new_version};

    # Perl syntax for a switch stmt
    my $c = IMG::AutoBuild::Plugin::findPlugin ($name);
    if (defined $c)
    {
      $c->set_option ($_, $options{$_}) for keys %options;
      $c->autobuild ($name, $new_version);
    }
    else
    {
      printf "Ignoring component %s:%s\n", $$cmp{name}, $$cmp{new_version};
    }
  }
}
