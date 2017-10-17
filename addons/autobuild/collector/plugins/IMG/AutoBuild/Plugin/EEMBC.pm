package IMG::AutoBuild::Plugin::EEMBC;

use warnings;
use strict;

use IMG::AutoBuild::Plugin;
our @ISA = qw(IMG::AutoBuild::Plugin);

use IMG::CCS;
use IMG::YAML::ActionSchema;
use YAML qw(Load DumpFile);
use File::Temp qw(tempfile);

sub find_old_versions
{
  my ($self, $name, $new_eembc) = @_;

  my $old_cmps = IMG::CCS->new ($main::CVSROOT, "eembc/tst.ccs", $name, undef)->list_and_parse_all ();
  my $old_eembc = $old_cmps->find_previous_version ($name, $new_eembc);

  my $old_cmp = IMG::CCS->new ($main::CVSROOT, "eembc/tst.ccs", $name, $old_eembc)->list_and_parse ();
  my $old_scripts = $old_cmp->subcomponent ("EEMBCScripts")->version ();

  return ('EEMBC' => $old_eembc,
          'EEMBCScripts' => $old_scripts);
}

sub find_new_versions
{
  my ($self, $name, $new_eembc) = @_;

  my $new_cmp = IMG::CCS->new ($main::CVSROOT, "eembc/tst.ccs", $name, $new_eembc)->list_and_parse ();
  my $new_scripts = $new_cmp->subcomponent ("EEMBCScripts")->version ();

  return ('EEMBC' => $new_eembc,
          'EEMBCScripts' => $new_scripts);
}

sub autobuild
{
  my ($self, $name, $ver) = @_;
  
  # Find all the components in the file
  my %old         = $self->find_old_versions ($name, $ver);
  my $old_eembc   = $old{'EEMBC'};
  my $old_scripts = $old{'EEMBCScripts'};

  my %new            = $self->find_new_versions ($name, $ver);
  my $new_eembc      = $new{'EEMBC'};
  my $new_scripts    = $new{'EEMBCScripts'};

  print "old $old_eembc $old_scripts\n";
  print "new $new_eembc $new_scripts\n";

  my $cmd = "neo new_source EEMBC $new_eembc";
  system("CVSROOT=$main::CVSROOT $cmd") == 0 or die "Cannot create source component";
  
  my ($export_file_handle, $export_file) = tempfile(UNLINK => 1);
  $cmd = "neo overtest --export --schema=Action"
          . " --action=EEMBC --version=$old_eembc"
          . " --action=BuildEEMBC --version=$old_scripts.%"
          . " --action=RunEEMBC --version=$old_scripts.%"
          . " >$export_file";
  print "$cmd\n";          
  system ("$cmd") == 0 or die;
  my $yaml_raw = `cat $export_file`;
  $yaml_raw =~ s/^.*?---/---/gs;

  my $yaml = Load($yaml_raw);
  DumpFile ("debug.1.log", $yaml);

  my %map = (
    'Neo Source Components'
      => { 'EEMBC'
              => { 'from' => $old_eembc, 'to' => $new_eembc },
         },
    'EEMBC Testsuite'
      => { 'BuildEEMBC' => [ ],
           'RunEEMBC'   => [ ],
         }
  );

  for my $action qw(BuildEEMBC RunEEMBC)
  {
    for my $target (keys %{$$yaml{'EEMBC Testsuite'}{$action}})
    {
      next unless $target =~ /^$old_scripts\.(.*)$/;
      push @{$map{'EEMBC Testsuite'}{$action}}, { 'from' => "$old_scripts.$1", 'to' => "$new_scripts.$1" };
    }
  }

  my $yaml_processor = IMG::YAML::ActionSchema->new ();
  $yaml_processor->map_all ($yaml, %map);

  my ($import_file_handle, $import_file) = tempfile(UNLINK => 1);
  DumpFile ($import_file, $yaml);
  DumpFile ("debug.2.log", $yaml);
  $cmd = "neo overtest --import --schema=Action --file=$import_file";
  system ("$cmd") == 0 or die;
}

1;
