--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

--
-- Name: ovt_configoptiontype_configoptiontypeid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_configoptiontype_configoptiontypeid_seq', 3, true);


--
-- Name: ovt_lifecyclestate_lifecyclestateid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_lifecyclestate_lifecyclestateid_seq', 4, true);


--
-- Name: ovt_notifyentity_notifyentityid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_notifyentity_notifyentityid_seq', 4, true);


--
-- Name: ovt_notifymethod_notifymethodid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_notifymethod_notifymethodid_seq', 2, true);


--
-- Name: ovt_notifytype_notifytypeid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_notifytype_notifytypeid_seq', 4, true);


--
-- Name: ovt_resourcestatus_resourcestatusid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_resourcestatus_resourcestatusid_seq', 8, true);


--
-- Name: ovt_resourcetype_resourcetypeid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_resourcetype_resourcetypeid_seq', 1, true);


--
-- Name: ovt_resulttype_resulttypeid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_resulttype_resulttypeid_seq', 4, true);


--
-- Name: ovt_runstatus_runstatusid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_runstatus_runstatusid_seq', 19, true);


--
-- Name: ovt_attribute_attributeid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_attribute_attributeid_seq', 6, true);


--
-- Name: ovt_attributevalue_attributevalueid_seq; Type: SEQUENCE SET; Schema: public; Owner: overtest
--

SELECT pg_catalog.setval('ovt_attributevalue_attributevalueid_seq', 11, true);


--
-- Data for Name: ovt_configoptiontype; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_configoptiontype (configoptiontypeid, configoptiontypename) FROM stdin;
1	integer
2	string
3	boolean
\.


--
-- Data for Name: ovt_lifecyclestate; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_lifecyclestate (lifecyclestateid, lifecyclestatename, visible, visiblebydefault, valid) FROM stdin;
1	OK	t	t	t
2	Deprecated	f	f	t
3	Unavailable	f	f	f
4	OK (hidden)	t	f	t
\.


--
-- Data for Name: ovt_notifyentity; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_notifyentity (notifyentityid, notifyentityname) FROM stdin;
1	testrunid
2	testrungroupid
3	userid
4	testsuiteid
\.


--
-- Data for Name: ovt_notifymethod; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_notifymethod (notifymethodid, notifymethodname) FROM stdin;
1	Growl
2	Email
\.


--
-- Data for Name: ovt_notifytype; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_notifytype (notifytypeid, notifytypename, emailtemplate, growltemplate, growltitletemplate) FROM stdin;
1	Testrun Status Change	At %date% testrun %[testrunid]% in %[testrungroupid]% transitioned from %from% to %to%	At %date% testrun %[testrunid]% transitioned from %from% to %to%	Testrun [%testrunid%] %to%
2	Testrun Status Change Verbose	At %date% testrun %[testrunid]% in %[testrungroupid]% transitioned from %from% to %to%	At %date% testrun [%testrunid%] transitioned from %from% to %to	Testrun [%testrunid%] %to%
3	Testsuite Completed	<h3>%[testsuiteid]%</h3>\n<b>Owner</b> %[userid]%<br />\n<b>Testrun</b> %[testrunid]%<br />\n<b>Testrun Group</b> %[testrungroupid]%<br />\n\n%testsuite%	%[testsuiteid]%	%[testsuiteid]%
4	Testrun Group Completed	<h3>%[testrungroupid]%</h3>\n\n%testsuites%	%testsuites%	Testrun Group Completed
\.


--
-- Data for Name: ovt_notifytypeentity; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_notifytypeentity (notifytypeid, notifyentityid) FROM stdin;
1	1
2	1
1	2
2	2
1	3
2	3
3	1
3	2
3	3
3	4
4	2
4	3
\.


--
-- Data for Name: ovt_resourcestatus; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_resourcestatus (resourcestatusid, status) FROM stdin;
1	OK
2	RESTART
3	DISABLED
4	CLAIMED
5	DISABLE
6	OFFLINE
7	UPDATING
8	HISTORIC
\.


--
-- Data for Name: ovt_resourcetype; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_resourcetype (resourcetypeid, resourcetypename) FROM stdin;
1	Execution Host
\.


--
-- Data for Name: ovt_resulttype; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_resulttype (resulttypeid, resulttypename) FROM stdin;
1	string
2	integer
3	float
4	boolean
\.


--
-- Data for Name: ovt_runstatus; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_runstatus (runstatusid, status, description, iseditable, goenabled, pauseenabled, abortenabled, archiveenabled, deleteenabled, checkenabled, externalenabled, equivcheck, isverbose, resultsvalid) FROM stdin;
1	CREATION	Planning testrun	t	f	f	f	f	t	t	t	f	t	f
2	READYTOCHECK	Awaiting dependency checking	f	f	f	f	f	f	f	f	f	t	f
3	CHECKFAILED	Manual dependency resolution required	t	f	f	f	f	t	t	f	f	f	f
4	CHECKED	Awaiting Host Allocation	f	f	f	f	f	f	f	f	f	f	f
5	HOSTALLOCATED	Awaiting Execution	f	f	t	t	f	f	f	f	t	t	f
6	RUNNING	Run in progress	f	f	t	t	f	f	f	f	t	f	f
7	PAUSED	Paused	f	t	f	t	f	f	f	f	t	f	f
8	ABORTED	Aborted	f	f	f	f	t	t	f	f	t	f	f
9	COMPLETED	Complete	f	f	f	f	t	t	f	f	t	f	t
10	ALLOCATIONFAILED	Execution Host allocation failed	t	f	f	f	f	t	t	f	f	f	f
11	DELETING	Delete in progress	f	f	f	f	f	f	f	f	f	t	f
12	ARCHIVING	Archive in progress	f	f	f	f	f	f	f	f	t	t	t
13	ARCHIVED	Archived	f	f	f	f	f	t	f	f	t	f	t
14	READYTODELETE	Awaiting deletion	f	f	f	f	f	f	f	f	f	t	f
15	READYTOARCHIVE	Awaiting archive	f	f	f	f	f	f	f	f	t	t	t
16	ABORTING	Abort in progress	f	f	f	f	f	f	f	f	t	t	f
17	EXTERNAL	External execution	f	f	f	f	f	t	f	f	t	t	t
18	TEMPLATE	Template testrun	t	f	f	f	f	t	f	f	f	f	f
\.


--
-- Data for Name: ovt_attribute; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_attribute (attributeid, attributename, lookup, resourcetypeid) FROM stdin;
1	Processor	t	1
2	OS	t	1
3	Linux Distibution	t	1
4	Shared Filesystem	t	1
5	Specific Host	t	1
6	Overtest rootdir	f	1
\.


--
-- Data for Name: ovt_attributevalue; Type: TABLE DATA; Schema: public; Owner: overtest
--

COPY ovt_attributevalue (attributevalueid, attributeid, value, mustrequest) FROM stdin;
1	1	x86 compat	f
2	1	x86	f
3	1	x86_64	f
4	2	Linux	f
5	2	Windows	f
6	2	Darwin	f
7	3	CentOS 3	f
8	3	CentOS 4	f
9	3	CentOS 5	f
10	3	CentOS 6	f
11	3	RHEL Server 5	f
\.

--
-- PostgreSQL database dump complete
--

