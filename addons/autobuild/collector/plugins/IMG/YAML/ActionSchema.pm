package IMG::YAML::ActionSchema;

use warnings;
use strict;

sub new
{
  my $class = shift;
  my $self = {};
  bless $self, $class;

  return $self;
}

sub map_all
{
  my ($self, $yaml, %map) = @_;

  for my $cat (keys %map)
  {
    for my $act (keys %{$map{$cat}})
    {
      $self->_map_action ($yaml, $cat, $act, %map);
    }
  }

}

sub _map_action
{
  my ($self, $yaml, $cat, $act, %map) = @_;

  my $ref = $$yaml{$cat}{$act};

  $map{$cat}{$act} = [ $map{$cat}{$act} ] if ref($map{$cat}{$act}) eq "HASH";
  for my $ver_map (@{$map{$cat}{$act}})
  {
    my $old = $$ver_map{'from'};
    my $new = $$ver_map{'to'};
    $self->_rename_elt ($ref, $old, $new);

    $self->_map_deps ($$ref{$new}{'consumers'}, %map);
    $self->_map_deps ($$ref{$new}{'producers'}, %map);
  }
}

sub _map_deps
{
  my $self = shift;
  my $yaml = shift;
  my %map = @_;

  for my $grp (keys %{$yaml})
  {
    for my $cat (keys %{$$yaml{$grp}})
    {
      for my $act (keys %{$$yaml{$grp}{$cat}})
      {
        if (defined $map{$cat}{$act})
        {
          my %keep;

          $map{$cat}{$act} = [ $map{$cat}{$act} ] if ref($map{$cat}{$act}) eq "HASH";

          for my $ver_map (@{$map{$cat}{$act}})
          {
            $self->_rename_elt ($$yaml{$grp}{$cat}{$act}, $$ver_map{'from'}, $$ver_map{'to'});

            $keep{$$ver_map{'to'}} = 1;
          }

          for my $ver (keys %{$$yaml{$grp}{$cat}{$act}})
          {
            delete $$yaml{$grp}{$cat}{$act}{$ver} unless $keep{$ver};
          }
        }
        else
        {
          warn "$cat/$act not described, leaving as-is";
        }
      }
    }
  }
}

sub _rename_elt
{
  my $self = shift;
  my $hashref = shift;
  my $from = shift;
  my $to = shift;

  my $tmp = $$hashref{$from};
  unless (defined $tmp)
  {
    warn "$from missing, not renaming";
    return;
  }
  delete $$hashref{$from};
  $$hashref{$to} = $tmp;
}

1;
