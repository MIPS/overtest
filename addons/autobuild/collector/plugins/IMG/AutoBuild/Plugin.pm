package IMG::AutoBuild::Plugin;

use warnings;
use strict;

my %plugins;

sub new
{
  my $class = shift;
  my $self = {};

  $self->{_options} = {};

  bless $self, $class;

  return $self;
}

sub set_option
{
  my ($self, $name, $value) = @_;

  $self->{_options}->{$name} = $value;
}

sub get_option
{
  my ($self, $name) = @_;

  return $self->{_options}->{$name};
}

sub findPlugin
{
  no strict;
  my ($component) = @_;

  return undef unless defined $plugins{$component};

  my $class = $plugins{$component};
  return $class->new();
}

for my $inc (@INC)
{
  my $plugindir = "$inc/IMG/AutoBuild/Plugin";
  my $plugincls = "IMG::AutoBuild::Plugin";

  if (-d $plugindir)
  {
    opendir my $dir, $plugindir or die;
    while ($_ = readdir $dir)
    {
      next unless /\.pm$/;
      s/\.pm$//;
      require "$plugindir/$_.pm";
      $plugins{$_} = sprintf "%s::%s", $plugincls, $_;
    }
    closedir $dir;
  }
}

1;
