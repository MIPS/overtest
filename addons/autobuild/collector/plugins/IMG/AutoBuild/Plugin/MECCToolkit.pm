package IMG::AutoBuild::Plugin::MECCToolkit;

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
  my ($self, $name, $new_tk) = @_;

  my $old_cmps = IMG::CCS->new ($main::CVSROOT, "mecc/ccs/toolkit.ccs", $name, undef)->list_and_parse_all ();
  my $old_tk = $old_cmps->find_previous_version ($name, $new_tk);

  my $old_cmp = IMG::CCS->new ($main::CVSROOT, "mecc/ccs/toolkit.ccs", $name, $old_tk)->list_and_parse ();
  my $old_scripts = $old_cmp->subcomponent ("Release")->version ();
  my $old_metamtxtoolkit = $old_cmp->subcomponent ("MetaMtxToolkitRef")->version ();

  return ('BuildMECCToolkit' => $old_tk,
          'FetchMECCScripts' => $old_scripts,
          'MetaMtxToolkitRef' => $old_metamtxtoolkit);
}

sub find_new_versions
{
  my ($self, $name, $new_tk) = @_;

  my $new_cmp = IMG::CCS->new ($main::CVSROOT, "mecc/ccs/toolkit.ccs", $name, $new_tk)->list_and_parse ();
  my $new_scripts = $new_cmp->subcomponent ("Release")->version ();
  my $new_metamtxtoolkit = $new_cmp->subcomponent ("MetaMtxToolkitRef")->version ();

  return ('BuildMECCToolkit' => $new_tk,
          'FetchMECCScripts' => $new_scripts,
          'MetaMtxToolkitRef' => $new_metamtxtoolkit);
}

sub autobuild
{
  my ($self, $name, $ver) = @_;

  # Find all the components in the file
  my %old         = $self->find_old_versions ($name, $ver);
  my $old_tk      = $old{'BuildMECCToolkit'};
  my $old_scripts = $old{'FetchMECCScripts'};
  my $old_metatk  = $old{'MetaMtxToolkitRef'};
  my ($old_metastub) = $old_metatk =~ /^(\d+(?:\.\d+){2})/;

  my %new            = $self->find_new_versions ($name, $ver);
  my $new_tk         = $new{'BuildMECCToolkit'};
  my $new_scripts    = $new{'FetchMECCScripts'};
  my $new_metatk     = $new{'MetaMtxToolkitRef'};
  my ($new_metastub) = $new_metatk =~ /^(\d+(?:\.\d+){2})/;

  print "old $old_tk $old_scripts $old_metatk\n";
  print "new $new_tk $new_scripts $new_metatk\n";

  my ($export_file_handle, $export_file) = tempfile(UNLINK => 1);
  my $cmd = "neo overtest --export --schema=Action"
          . " --action=FetchMECCScripts --version=$old_scripts"
          . " --action=BuildMECCToolkit --version=$old_tk"
          . " >$export_file";
  system ("$cmd") == 0 or die;
  my $yaml_raw = `cat $export_file`;
  $yaml_raw =~ s/^.*?---/---/gs;

  my $yaml = Load($yaml_raw);
  DumpFile ("debug.1.log", $yaml);

  my %map = (
    'MECC Build' => { 'FetchMECCScripts'   => { 'from' => $old_scripts,  'to' => $new_scripts  },
                      'BuildMECCToolkit'   => { 'from' => $old_tk,       'to' => $new_tk       },
                    },
    'Testsuites' => { 'MetaMtxToolkitStub' => { 'from' => $old_metastub, 'to' => $new_metastub },
                    },
  );

  my $yaml_processor = IMG::YAML::ActionSchema->new ();
  $yaml_processor->map_all ($yaml, %map);

  my ($import_file_handle, $import_file) = tempfile(UNLINK => 1);
  DumpFile ($import_file, $yaml);
  DumpFile ("debug.2.log", $yaml);
  $cmd = "neo overtest --import --schema=Action --file=$import_file";
  system ("$cmd") == 0 or die;

  my ($testrun_file_handle, $testrun_file) = tempfile(UNLINK => 1);
  print $testrun_file_handle $self->testrun_template ($new_tk, $new_scripts, $new_metatk, $new_metastub);
  close $testrun_file_handle;

  $cmd = "neo overtest --edit --new --file $testrun_file --user mecc --go";
  system ("$cmd") == 0 or die;
}

sub testrun_template
{
  my $self         = shift;
  my $new_tk       = shift;
  my $new_scripts  = shift;
  my $new_metatk   = shift;
  my $new_metastub = shift;
  my $do_win       = $self->get_option ('WIN');

  $do_win = 1 unless defined $do_win;
  $do_win = $do_win ? 'True' : 'False';

  return <<EOF
%YAML 1.1
---
group:       MECC
description: autobuild $new_tk
definition:
  - MECC Build:
      FetchMECCScripts: $new_scripts
      BuildMECCToolkit: $new_tk
  - Testsuites:
      MetaMtxToolkitStub: $new_metastub
  - Neo Binary Components:
      MetaMtxToolkit: $new_metatk
configuration:
  - Neo Options:
      Manual Toolkit Root: root
  - MECC Build Inputs:
      MECC_DO_WINDOWS: $do_win
resources:
  - Execution Host:
      require:
        OS:                Linux
        Shared Filesystem: Cosy Cluster
        Specific Host:     Cosy 02
EOF
}

1;
