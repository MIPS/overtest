<?php
include_once('includes.inc');

htmlHeader("Development Status");

?>
<h1>Current Features</h1>
<h2>Actions</h2>
<ul>
<li>Describe either simple units of work or testsuites</li>
<li>Are implemented using a python module</li>
<li>Utilise an execution framework to run commands</li>
<li>Are versioned to model changes over time</li>
<li>Can expose configurable options to a user</li>
<li>Can require resources with specific features</li>
<li>Can store extended results relating to the work they do</li>
</ul>
<h2>Execution Framework</h2>
<ul>
<li>Finds execution hosts based on required features</li>
<li>Allocates areas to store log files from executed commands</li>
<li>Allocates local areas to store files and data (per execution host)</li>
<li>Cleans up after tests have run (archiving)</li>
<li>Provides easy access to configuration settings</li>
<li>Provides easy access to allocated resources</li>
<li>Provides routines to submit extended result information</li>
<li>Prodives routines to submit results (and extended results) for tests in a testsuite</li>
<li>Provides a standalone script to submit results from within an existing testsuite</li>
</ul>
<h2>Dependencies</h2>
<ul>
<li>Model the relationship between one version of an action to one version of another action</li>
<li>Guarantee that a producer has completed before a consumer is executed</li>
<li>Allow actions to execute in parallel where there is no interdependency</li>
<li>Can be weak, such that they only represent a logical relationship rather than a real requirement (version only dependency)</li>
<li>Can specify that the consumer executes on the same host as the producer (A host match)</li>
<li>Can be grouped to describe the situation where one version of any action in the group, is required</li>
<li>Ensure that whenever an action is executed, one version of one action in each dependency group has executed</li>
</ul>
<h2>Configuration options</h2>
<ul>
<li>Are typed to provide simple validation checks (int, bool, string)</li>
<li>Have default values</li>
<li>Can be set by a user or by another action</li>
<li>Can be defined as multiple choice</li>
</ul>
<h2>Testruns</h2>
<ul>
<li>Describe a set of versioned actions to run</li>
<li>Include configuration settings</li>
<li>Include additional resource requirements</li>
<li>Can be prioritised</li>
<li>Can be set to start after a specific time</li>
<li>Can be paused, aborted, archived and deleted</li>
<li>Will automatically abort if any task fails</li>
<li>Can be set to an external state where systems other than overtest can submit results</li>
<li>Can be created through a graphical web interface or a commandline based utility</li>
<li>Can be described as a YAML control file</li>
</ul>
<h2>Execution Hosts</h2>
<ul>
<li>Used to model machines that an action can run on</li>
<li>Are similar to resources but an execution host is required for every action</li>
<li>Can be grouped such that testruns can be directed to certain sets of machines (for fairness)</li>
<li>Define a certain number of tasks that can execute concurrently</li>
<li>can have their concurrency level altered dynamically</li>
<li>Are implemented as python daemons, one of which runs on each host</li>
<li>Can be remotely shutdown or restarted</li>
<li>Will not fail even in the event of the Overtest database disappearing</li>
<li class="notdone">Can be claimed from the system, or concurrency level scheduled</li>
</ul>
<h2>Resources</h2>
<ul>
<li>Are used to describe anything that a test needs (an execution host is a special resource)</li>
<li>Describe various features they provide in the form of attributes</li>
<li>Can be initialised using the same framework as actions execute. With the obvious difference being that other resources except the execution host cannot be used</li>
<li>Are automatically allocated to tasks when needed</li>
<li>Can be reserved such that they are not allocated unless specific features are requested</li>
<li>Can be linked such that acquisition of one resource implies acquisition of another</li>
<li>Can be claimed for manual use. Manual claims take precedence over automated claims and are queued on a first come first served basis</li>
</ul>

<h1>Features in progress</h1>
<ul>
<li>Some way of rsyncing 'safe' results files from secure machines</li>
<li>Find a way of passing dependency checking and host allocation errors back to the web interface</li>
<li>DLS: Automatic command line based update of new versions and dependencies</li>
<li>MPF: Results analysis requires tracking of gold status</li>
<li>Re-entrant actions to allow testruns to be paused mid way through a task or allow a task to 'yield' after partial completion</li>
</ul>

<?

htmlFooter();

?>
