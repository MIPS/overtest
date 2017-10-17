package IMG::AutoBuild::Plugin::Test;

use warnings;
use strict;

use IMG::AutoBuild::Plugin;
our @ISA = qw(IMG::AutoBuild::Plugin);

sub autobuild
{
  my ($self, $name, $version) = @_;
  print "Submitting test job $name $version\n";
}

1;
