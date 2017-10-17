package IMG::CCS;

use warnings;
use strict;

use Sort::Versions;
use File::Temp qw(tempfile);

sub new
{
  my $class   = shift;
  my $cvsroot = shift;
  my $file    = shift;
  my $cmp     = shift;
  my $ver     = shift;
  my $self    = {};
  bless $self, $class;

  $self->cvsroot ($cvsroot);
  $self->component_file ($file);
  $self->component ($cmp);
  $self->version ($ver);

  return $self;
}

sub parse
{
  my $self = shift;
  my $text = shift;
  my $cmp  = shift;
  my $ver  = shift;

  $text =~ s/.*?(CMP="$cmp", VN="$ver".*?\n\n).*/$1/gs;

  my @lines = split /\n/, $text;
  for (@lines)
  {
    /^cvs update/
      and do { next };
    /^CWD=/
      and do { next };
    /^CMP="([^"]*)", VN="([^"]*)", ISTM="([^"])", CF="([^"]*)", CP="([^"]*)", DESC="([^"]*)"/
      and do
      {
        $self->component     ($1);
        $self->version       ($2);
        $self->istm          ($3);
        $self->component_file($4);
        $self->component_path($5);
        $self->description   ($6);
        next;
      };
    /^LINE="([^"]*)", CPNT="(.*?)"$/
      and do
      {
        $self->add_note      ($2);
        next;
      };

    /^SUB="([^"]*)", VN="([^"]*)", ISTM="([^"])", CF="([^"]*)", DESC="([^"]*)"/
      and do
      {
        $self->subcomponent ($1, IMG::CCS->new ($self->cvsroot(), $4, $1, $2));
        next;
      };
    /^$/ and do { next };
    die "Unknown line $_";
  }
  $self->is_version_bundle (0);
}

sub parse_all
{
  my $self = shift;
  my $text = shift;
  my $cmp  = shift;
  my $ver  = shift;

  $self->component ($cmp);
  $self->version (undef);

  my @lines = split /\n/, $text;
  for (@lines)
  {
    /^CMP="([^"]*)", VN="([^"]*)", ISTM="([^"])", CF="([^"]*)", CP="([^"]*)", DESC="([^"]*)"/
      and do
      {
        my $sub = IMG::CCS->new ($self->cvsroot(), $4, $1, $2);
        $sub->istm          ($3);
        $sub->component_path($5);
        $sub->description   ($6);
        $self->subcomponent ("$1:$2", $sub);
        next;
      };

    /^LINE="([^"]*)", CPNT="(.*?)"$/
      and do { next; };

    /^SUB="([^"]*)", VN="([^"]*)", ISTM="([^"])", CF="([^"]*)", DESC="([^"]*)"/
      and do { next; };

    /^CWD=/
      and do { next };

    /^cvs update/
      and do { next };

    /^$/
      and do { next };
    die "Unknown line $_";
  }
  $self->is_version_bundle (1);
}

sub list
{
  my $self = shift;
  my $file = shift;
  my ($fh, $fn) = tempfile(UNLINK => 1);
  my $cvsroot = $self->cvsroot();
  system ("cvs -q -d$cvsroot co -p $file > $fn");
  my $s = `ccs -c $fn list`;
  return $s;
}

sub list_and_parse
{
  my $self = shift;
  my $file = $self->component_file ();
  my $cmp  = $self->component ();
  my $ver  = $self->version ();
  $self->parse ($self->list ($file), $cmp, $ver);
  return $self;
}

sub list_and_parse_all
{
  my $self = shift;
  my $file = $self->component_file ();
  my $cmp  = $self->component ();
  my $ver  = $self->version ();
  $self->parse_all ($self->list ($file), $cmp, $ver);
  return $self;
}

for my $field qw(component version istm component_file component_path description is_version_bundle cvsroot)
{
  my $slot = __PACKAGE__ . "::$field";
  no strict "refs";
  *$field = sub {
    my $self = shift;
    $self->{$slot} = shift if @_;
    return $self->{$slot};
  };
}

for my $field qw(add_note)
{
  my $slot = __PACKAGE__ . "::$field";
  no strict "refs";
  *$field = sub {
    my $self = shift;
    push @{$self->{$slot}}, @_ if @_;
    return undef;
  };
}

for my $field qw(subcomponent)
{
  my $slot = __PACKAGE__ . "::$field";
  no strict "refs";
  *$field = sub {
    my $self = shift;
    my $sub = shift;
    $self->{$slot}->{$sub} = shift if @_;
    return $self->{$slot}->{$sub};
  };
}

sub subcomponents
{
  my $slot = __PACKAGE__ . "::subcomponent";
  my $self = shift;
  return keys %{$self->{$slot}};
}

sub find_previous_version
{
  my $self = shift;
  die unless $self->is_version_bundle();
  my $cmpname = shift;
  my $cmpver = shift;

  my @cmpver_parts = split /\./, $cmpver;

  my @old_cmp_vers = $self->subcomponents ();
  # Restrict results to the correct component name
  @old_cmp_vers = grep /^$cmpname/, @old_cmp_vers;
  s/^$cmpname:// for @old_cmp_vers;
  # Remove templates
  @old_cmp_vers = grep !/#/, @old_cmp_vers;
  # Ensure all have the same length
  @old_cmp_vers = grep { my @tmp = split /\./; scalar(@tmp) == scalar(@cmpver_parts) } @old_cmp_vers;
  # Restrict to older versions
  @old_cmp_vers = grep { versioncmp($_, $cmpver) == -1 } @old_cmp_vers;
  # Get the newest 'old' version
  @old_cmp_vers = sort versioncmp @old_cmp_vers;
  return pop @old_cmp_vers;
}

1;
