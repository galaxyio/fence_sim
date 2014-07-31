#!/usr/bin/python

import sys, getopt, time, os, uuid, pycurl
import pexpect, re, atexit, syslog
import __main__

## do not add code here.
#BEGIN_VERSION_GENERATION
RELEASE_VERSION="4.0.2"
BUILD_DATE="(built Tue Jun 10 06:59:12 UTC 2014)"
REDHAT_COPYRIGHT="Copyright (C) Red Hat, Inc. 2004-2010 All rights reserved."
#END_VERSION_GENERATION

LOG_MODE_VERBOSE = 100
LOG_MODE_QUIET = 0

EC_GENERIC_ERROR   = 1
EC_BAD_ARGS        = 2
EC_LOGIN_DENIED    = 3
EC_CONNECTION_LOST = 4
EC_TIMED_OUT       = 5
EC_WAITING_ON      = 6
EC_WAITING_OFF     = 7
EC_STATUS          = 8
EC_STATUS_HMC      = 9
EC_PASSWORD_MISSING = 10
EC_INVALID_PRIVILEGES = 11

TELNET_PATH = "/usr/bin/telnet"
SSH_PATH    = "/usr/bin/ssh"
SSL_PATH    = "/usr/bin/gnutls-cli"
SUDO_PATH   = "/usr/bin/sudo"

all_opt = {
	"help"    : {
		"getopt" : "h",
		"longopt" : "help",
		"help" : "-h, --help                     Display this help and exit",
		"required" : "0",
		"shortdesc" : "Display help and exit",
		"order" : 54 },
	"version" : { 
		"getopt" : "V",
		"longopt" : "version",
		"help" : "-V, --version                  Output version information and exit",
		"required" : "0",
		"shortdesc" : "Display version information and exit",
		"order" : 53 },
	"verbose" : {
		"getopt" : "v",
		"longopt" : "verbose",
		"help" : "-v, --verbose                  Verbose mode",
		"required" : "0",
		"shortdesc" : "Verbose mode",
		"order" : 51 },
	"debug" : {
		"getopt" : "D:",
		"longopt" : "debug-file", 
		"help" : "-D, --debug-file=[debugfile]   Debugging to output file",
		"required" : "0",
		"shortdesc" : "Write debug information to given file",
		"order" : 52 },
	"delay" : {
		"getopt" : "f:",
		"longopt" : "delay",
		"help" : "--delay=[seconds]              Wait X seconds before fencing is started",
		"required" : "0",
		"shortdesc" : "Wait X seconds before fencing is started",
		"default" : "0",
		"order" : 200 },
	"agent"   : {
		"getopt" : "",
		"help" : "",
		"order" : 1 },
	"web"    : {
		"getopt" : "",
		"help" : "",
		"order" : 1 },
	"action" : {
		"getopt" : "o:",
		"longopt" : "action",
		"help" : "-o, --action=[action]          Action: status, reboot (default), off or on",
		"required" : "1",
		"shortdesc" : "Fencing Action",
		"default" : "reboot",
		"order" : 1 },
	"fabric_fencing" : {
		"getopt" : "",
		"help" : "",
		"order" : 1 },
	"ipaddr" : {
		"getopt" : "a:",
		"longopt" : "ip",
		"help" : "-a, --ip=[ip]                  IP address or hostname of fencing device",
		"required" : "1",
		"shortdesc" : "IP Address or Hostname",
		"order" : 1 },
	"ipport" : {
		"getopt" : "u:",
		"longopt" : "ipport",
		"help" : "-u, --ipport=[port]            TCP/UDP port to use",
		"required" : "0",
		"shortdesc" : "TCP/UDP port to use for connection with device",
		"order" : 1 },		
	"login" : {
		"getopt" : "l:",
		"longopt" : "username",
		"help" : "-l, --username=[name]          Login name",
		"required" : "?",
		"shortdesc" : "Login Name",
		"order" : 1 },
	"no_login" : {
		"getopt" : "b:",
		"longopt" : "no_login",
		"help" : "-b, --no_login                 No Login Needed",
		"required" : "?",
		"shortdesc" : "No Login Needed",
		"order" : 1 },
	"no_password" : {
		"getopt" : "",
		"help" : "",
		"order" : 1 },
	"no_port" : {
		"getopt" : "",
		"help" : "",
		"order" : 1 },	
	"passwd" : {
		"getopt" : "p:",
		"longopt" : "password",
		"help" : "-p, --password=[password]      Login password or passphrase",
		"required" : "0",
		"shortdesc" : "Login password or passphrase",
		"order" : 1 },
	"passwd_script" : {
		"getopt" : "S:",
		"longopt" : "password-script",
		"help" : "-S, --password-script=[script] Script to run to retrieve password",
		"required" : "0",
		"shortdesc" : "Script to retrieve password",
		"order" : 1 },
	"identity_file" : {
		"getopt" : "k:",
		"longopt" : "identity-file",
		"help" : "-k, --identity-file=[filename] Identity file (private key) for ssh ",
		"required" : "0",
		"shortdesc" : "Identity file for ssh",
		"order" : 1 },
	"drac_version" : {
		"getopt" : "d:",
		"longopt" : "drac-version",
		"help" : "-d, --drac-version=[version]   Force DRAC version to use",
		"required" : "0",
		"shortdesc" : "Force DRAC version to use",
		"order" : 1 },
	"cmd_prompt" : {
		"getopt" : "c:",
		"longopt" : "command-prompt",
		"help" : "-c, --command-prompt=[prompt]  Force Python regex for command prompt",
		"shortdesc" : "Force Python regex for command prompt",
		"required" : "0",
		"order" : 1 },
	"secure" : {
		"getopt" : "x",
		"longopt" : "ssh",
		"help" : "-x, --ssh                      Use ssh connection",
		"shortdesc" : "SSH connection",
		"required" : "0",
		"order" : 1 },
	"ssh_options" : {
		"getopt" : "X:",
		"longopt" : "ssh-options",
		"help" : "--ssh-options=[options]	  SSH options to use",
		"shortdesc" : "SSH options to use",
		"required" : "0",
		"order" : 1 },
	"ssl" : {
		"getopt" : "z",
		"longopt" : "ssl",
		"help" : "-z, --ssl                      Use ssl connection",
		"required" : "0",
		"shortdesc" : "SSL connection",
		"order" : 1 },
	"ssl_insecure" : {
		"getopt" : "9",
		"longopt" : "ssl-insecure",
		"help" : "--ssl-insecure                 Use ssl connection without verifying certificate",
		"required" : "0",
		"shortdesc" : "SSL connection without verifying fence device's certificate",
		"order" : 1 },
	"ssl_secure" : {
		"getopt" : "9",
		"longopt" : "ssl-secure",
		"help" : "--ssl-secure                   Use ssl connection with verifying certificate",
		"required" : "0",
		"shortdesc" : "SSL connection with verifying fence device's certificate",
		"order" : 1 },
	"notls" : {
		"getopt" : "t",
		"longopt" : "notls",
		"help" : "-t, --notls                    Disable TLS negotiation and force SSL3.0.\n" +
	"                                        This should only be used for devices that do not support TLS1.0 and up.",
		"required" : "0",
		"shortdesc" : "Disable TLS negotiation",
		"order" : 1 },
	"port" : {
		"getopt" : "n:",
		"longopt" : "plug",
		"help" : "-n, --plug=[id]                Physical plug number on device, UUID or\n" + 
        "                                        identification of machine",
		"required" : "1",
		"shortdesc" : "Physical plug number, name of virtual machine or UUID",
		"order" : 1 },
	"switch" : {
		"getopt" : "s:",
		"longopt" : "switch",
		"help" : "-s, --switch=[id]              Physical switch number on device",
		"required" : "0",
		"shortdesc" : "Physical switch number on device",
		"order" : 1 },
	"exec" : {
		"getopt" : "e:",
		"longopt" : "exec",
		"help" : "-e, --exec=[command]           Command to execute",
		"required" : "0",
		"shortdesc" : "Command to execute",
		"order" : 1 },
	"vmware_type" : {
		"getopt" : "d:",
		"longopt" : "vmware_type",
		"help" : "-d, --vmware_type=[type]       Type of VMware to connect",
		"required" : "0",
		"shortdesc" : "Type of VMware to connect",
		"order" : 1 },
	"vmware_datacenter" : {
		"getopt" : "s:",
		"longopt" : "vmware-datacenter",
		"help" : "-s, --vmware-datacenter=[dc]   VMWare datacenter filter",
		"required" : "0",
		"shortdesc" : "Show only machines in specified datacenter",
		"order" : 2 },
	"snmp_version" : {
		"getopt" : "d:",
		"longopt" : "snmp-version",
		"help" : "-d, --snmp-version=[version]   Specifies SNMP version to use",
		"required" : "0",
		"shortdesc" : "Specifies SNMP version to use (1,2c,3)",
		"order" : 1 },
	"community" : {
		"getopt" : "c:",
		"longopt" : "community",
		"help" : "-c, --community=[community]    Set the community string",
		"required" : "0",
		"shortdesc" : "Set the community string",
		"order" : 1},
	"snmp_auth_prot" : {
		"getopt" : "b:",
		"longopt" : "snmp-auth-prot",
		"help" : "-b, --snmp-auth-prot=[prot]    Set authentication protocol (MD5|SHA)",
		"required" : "0",
		"shortdesc" : "Set authentication protocol (MD5|SHA)",
		"order" : 1},
	"snmp_sec_level" : {
		"getopt" : "E:",
		"longopt" : "snmp-sec-level",
		"help" : "-E, --snmp-sec-level=[level]   Set security level\n"+
		"                                  (noAuthNoPriv|authNoPriv|authPriv)",
		"required" : "0",
		"shortdesc" : "Set security level (noAuthNoPriv|authNoPriv|authPriv)",
		"order" : 1},
	"snmp_priv_prot" : {
		"getopt" : "B:",
		"longopt" : "snmp-priv-prot",
		"help" : "-B, --snmp-priv-prot=[prot]    Set privacy protocol (DES|AES)",
		"required" : "0",
		"shortdesc" : "Set privacy protocol (DES|AES)",
		"order" : 1},
	"snmp_priv_passwd" : {
		"getopt" : "P:",
		"longopt" : "snmp-priv-passwd",
		"help" : "-P, --snmp-priv-passwd=[pass]  Set privacy protocol password",
		"required" : "0",
		"shortdesc" : "Set privacy protocol password",
		"order" : 1},
	"snmp_priv_passwd_script" : {
		"getopt" : "R:",
		"longopt" : "snmp-priv-passwd-script",
		"help" : "-R, --snmp-priv-passwd-script  Script to run to retrieve privacy password",
		"required" : "0",
		"shortdesc" : "Script to run to retrieve privacy password",
		"order" : 1},
	"inet4_only" : {
		"getopt" : "4",
		"longopt" : "inet4-only",
		"help" : "-4, --inet4-only               Forces agent to use IPv4 addresses only",
		"required" : "0",
		"shortdesc" : "Forces agent to use IPv4 addresses only",
		"order" : 1 },
	"inet6_only" : {
		"getopt" : "6",
		"longopt" : "inet6-only",
		"help" : "-6, --inet6-only               Forces agent to use IPv6 addresses only",
		"required" : "0",
		"shortdesc" : "Forces agent to use IPv6 addresses only",
		"order" : 1 },
	"separator" : {
		"getopt" : "C:",
		"longopt" : "separator",
		"help" : "-C, --separator=[char]         Separator for CSV created by 'list' operation",
		"default" : ",", 
		"required" : "0",
		"shortdesc" : "Separator for CSV created by operation list",
		"order" : 100 },
	"login_timeout" : {
		"getopt" : "y:",
		"longopt" : "login-timeout",
		"help" : "--login-timeout=[seconds]      Wait X seconds for cmd prompt after login",
		"default" : "5", 
		"required" : "0",
		"shortdesc" : "Wait X seconds for cmd prompt after login",
		"order" : 200 },
	"shell_timeout" : {
		"getopt" : "Y:",
		"longopt" : "shell-timeout",
		"help" : "--shell-timeout=[seconds]      Wait X seconds for cmd prompt after issuing command",
		"default" : "3", 
		"required" : "0",
		"shortdesc" : "Wait X seconds for cmd prompt after issuing command",
		"order" : 200 },
	"power_timeout" : {
		"getopt" : "g:",
		"longopt" : "power-timeout",
		"help" : "--power-timeout=[seconds]      Test X seconds for status change after ON/OFF",
		"default" : "20", 
		"required" : "0",
		"shortdesc" : "Test X seconds for status change after ON/OFF",
		"order" : 200 },
	"power_wait" : {
		"getopt" : "G:",
		"longopt" : "power-wait",
		"help" : "--power-wait=[seconds]         Wait X seconds after issuing ON/OFF",
		"default" : "0", 
		"required" : "0",
		"shortdesc" : "Wait X seconds after issuing ON/OFF",
		"order" : 200 },
	"missing_as_off" : {
		"getopt" : "M",
		"longopt" : "missing-as-off",
		"help" : "--missing-as-off               Missing port returns OFF instead of failure",
		"required" : "0",
		"shortdesc" : "Missing port returns OFF instead of failure",
		"order" : 200 },
	"retry_on" : {
		"getopt" : "F:",
		"longopt" : "retry-on",
		"help" : "--retry-on=[attempts]          Count of attempts to retry power on",
		"default" : "1",
		"required" : "0",
		"shortdesc" : "Count of attempts to retry power on",
		"order" : 201 },
	"session_url" : {
		"getopt" : "s:",
		"longopt" : "session-url",
		"help" : "-s, --session-url              URL to connect to XenServer on",
		"required" : "1",
		"shortdesc" : "The URL of the XenServer host.",
		"order" : 1},
	"sudo" : {
		"getopt" : "d",
		"longopt" : "use-sudo",
		"help" : "--use-sudo                     Use sudo (without password) when calling 3rd party software",
		"required" : "0",
		"shortdesc" : "Use sudo (without password) when calling 3rd party sotfware.",
		"order" : 205}
}

# options which are added automatically if 'key' is encountered ("default" is always added)
DEPENDENCY_OPT = {
		"default" : [ "help", "debug", "verbose", "version", "action", "agent", \
			"power_timeout", "shell_timeout", "login_timeout", "power_wait", "retry_on", "delay", \
                        "no_login" ],
		"passwd" : [ "passwd_script" ],
		"secure" : [ "identity_file", "ssh_options" ],
		"ipaddr" : [ "ipport", "inet4_only", "inet6_only" ],
		"port" : [ "separator" ],
		"ssl" : [ "ssl_secure", "ssl_insecure" ],
		"community" : [ "snmp_auth_prot", "snmp_sec_level", "snmp_priv_prot", \
			"snmp_priv_passwd", "snmp_priv_passwd_script" ]
	}

class fspawn(pexpect.spawn):
	def __init__(self, options, command):
		pexpect.spawn.__init__(self, command)
		self.opt = options
		
	def log_expect(self, options, pattern, timeout):
		result = self.expect(pattern, timeout)
		if options["log"] >= LOG_MODE_VERBOSE:
			options["debug_fh"].write(self.before + self.after)
		return result

	# send EOL according to what was detected in login process (telnet)
	def send_eol(self, message):
		self.send(message + self.opt["eol"])

        def die(self, errstr):
                self.terminate()
def atexit_handler():
	try:
		sys.stdout.close()
		os.close(1)
	except IOError:
		sys.stderr.write("%s failed to close standard output\n"%(sys.argv[0]))
		syslog.syslog(syslog.LOG_ERR, "Failed to close standard output")
		sys.exit(EC_GENERIC_ERROR)

def add_dependency_options(options):
	## Add options which are available for every fence agent
	added_opt = [] 
	for x in options + ["default"]:
		if DEPENDENCY_OPT.has_key(x):
			added_opt.extend([y for y in DEPENDENCY_OPT[x] if options.count(y) == 0])
	return added_opt


def version(command, release, build_date, copyright_notice):
	print command, " ", release, " ", build_date
	if len(copyright_notice) > 0:
		print copyright_notice

def fail_usage(message = ""):
	if len(message) > 0:
		sys.stderr.write(message+"\n")
	sys.stderr.write("Please use '-h' for usage\n")
	sys.exit(EC_GENERIC_ERROR)

def fail(error_code):
	message = {
		EC_LOGIN_DENIED : "Unable to connect/login to fencing device",
		EC_CONNECTION_LOST : "Connection lost",
		EC_TIMED_OUT : "Connection timed out",
		EC_WAITING_ON : "Failed: Timed out waiting to power ON",
		EC_WAITING_OFF : "Failed: Timed out waiting to power OFF",
		EC_STATUS : "Failed: Unable to obtain correct plug status or plug is not available",
		EC_STATUS_HMC :
			"Failed: Either unable to obtain correct plug status, partition is not available or incorrect HMC version used",
		EC_PASSWORD_MISSING : "Failed: You have to set login password",
		EC_INVALID_PRIVILEGES : "Failed: The user does not have the correct privileges to do the requested action."
	}[error_code] + "\n"
	sys.stderr.write(message)
	syslog.syslog(syslog.LOG_ERR, message)
	sys.exit(EC_GENERIC_ERROR)

def usage(avail_opt):
	print "Usage:"
	print "\t" + os.path.basename(sys.argv[0]) + " [options]"
	print "Options:"

	sorted_list = [ (key, all_opt[key]) for key in avail_opt ]
	sorted_list.sort(lambda x, y: cmp(x[1]["order"], y[1]["order"]))

	for key, value in sorted_list:
		if len(value["help"]) != 0:
			print "   " + value["help"]

def metadata(avail_opt, options, docs):
	sorted_list = [ (key, all_opt[key]) for key in avail_opt ]
	sorted_list.sort(lambda x, y: cmp(x[1]["order"], y[1]["order"]))

	print "<?xml version=\"1.0\" ?>"
	print "<resource-agent name=\"" + os.path.basename(sys.argv[0]) + "\" shortdesc=\"" + docs["shortdesc"] + "\" >"
	if "symlink" in docs:
		for (symlink, desc) in docs["symlink"]:
			print "<symlink name=\"" + symlink + "\" shortdesc=\"" + desc + "\"/>"
	print "<longdesc>" + docs["longdesc"] + "</longdesc>"
	if docs.has_key("vendorurl"):
		print "<vendor-url>" + docs["vendorurl"] + "</vendor-url>"
	print "<parameters>"
	for option, _value in sorted_list:
		if all_opt[option].has_key("shortdesc"):
			print "\t<parameter name=\"" + option + "\" unique=\"0\" required=\"" + all_opt[option]["required"] + "\">"

			default = ""
			if all_opt[option].has_key("default"):
				default = str(all_opt[option]["default"])
			elif options.has_key("--" + all_opt[option]["longopt"]) and all_opt[option]["getopt"].endswith(":"):
				if options["--" + all_opt[option]["longopt"]]:
					try:
						default = options["--" + all_opt[option]["longopt"]]
					except TypeError:
						## @todo/@note: Currently there is no clean way how to handle lists
						## we can create a string from it but we can't set it on command line
						default = str(options["--" + all_opt[option]["longopt"]])
			elif options.has_key("--" + all_opt[option]["longopt"]):
				default = "true"

			if default:
				default = default.replace("&", "&amp;" )
				default = default.replace('"', "&quot;" )
				default = default.replace('<', "&lt;" )
				default = default.replace('>', "&gt;" )
				default = default.replace("'", "&apos;" )
				default = "default=\"" + default + "\" "

			mixed = all_opt[option]["help"]
			## split it between option and help text
			res = re.compile("^(.*--\S+)\s+", re.IGNORECASE | re.S).search(mixed)
			if (None != res):
				mixed = res.group(1)
			mixed = mixed.replace("<", "&lt;").replace(">", "&gt;")
			print "\t\t<getopt mixed=\"" + mixed + "\" />"

			if all_opt[option]["getopt"].count(":") > 0:
				print "\t\t<content type=\"string\" "+default+" />"
			else:
				print "\t\t<content type=\"boolean\" "+default+" />"
				
			print "\t\t<shortdesc lang=\"en\">" + all_opt[option]["shortdesc"] + "</shortdesc>"
			print "\t</parameter>"
	print "</parameters>"
	print "<actions>"
	if avail_opt.count("fabric_fencing") == 1:
		## do 'unfence' at the start
		print "\t<action name=\"on\" automatic=\"1\"/>"
	else:
		print "\t<action name=\"on\" automatic=\"0\"/>"
	print "\t<action name=\"off\" />"

	if avail_opt.count("fabric_fencing") == 0:
		print "\t<action name=\"reboot\" />"

	print "\t<action name=\"status\" />"
	print "\t<action name=\"list\" />"
	print "\t<action name=\"monitor\" />"
	print "\t<action name=\"metadata\" />"	
	print "</actions>"
	print "</resource-agent>"

def process_input(avail_opt):
	avail_opt.extend(add_dependency_options(avail_opt))

	##
	## Set standard environment
	#####
	os.putenv("LANG", "C")
	os.putenv("LC_ALL", "C")

	##
	## Prepare list of options for getopt
	#####
	getopt_string = ""
	longopt_list = [ ]
	for k in avail_opt:
		if all_opt.has_key(k):
			getopt_string += all_opt[k]["getopt"]
		else:
			fail_usage("Parse error: unknown option '"+k+"'")

		if all_opt.has_key(k) and all_opt[k].has_key("longopt"):
			if all_opt[k]["getopt"].endswith(":"):
				longopt_list.append(all_opt[k]["longopt"] + "=")
			else:
				longopt_list.append(all_opt[k]["longopt"])

	##
	## Read options from command line or standard input
	#####
	if len(sys.argv) > 1:
		try:
			opt, _args = getopt.gnu_getopt(sys.argv[1:], getopt_string, longopt_list)
		except getopt.GetoptError, error:
			fail_usage("Parse error: " + error.msg)

		## Transform short getopt to long one which are used in fencing agents
		#####
		old_opt = opt
		opt = { }
		for o in dict(old_opt).keys():
			if o.startswith("--"):
				for x in all_opt.keys():
					if all_opt[x].has_key("longopt") and "--" + all_opt[x]["longopt"] == o:
						opt["--" + all_opt[x]["longopt"]] = dict(old_opt)[o]
			else:
				for x in all_opt.keys():
					if all_opt[x].has_key("getopt") and all_opt[x].has_key("longopt") and \
						("-" + all_opt[x]["getopt"] == o or "-" + all_opt[x]["getopt"].rstrip(":") == o):
						opt["--" + all_opt[x]["longopt"]] = dict(old_opt)[o]
				opt[o] = dict(old_opt)[o]

		## Compatibility Layer
		#####
		z = dict(opt)
		if z.has_key("--plug") == 1:
			z["-m"] = z["--plug"]

		opt = z
		##
		#####
	else:
		opt = { }
		name = ""
		for line in sys.stdin.readlines():
			line = line.strip()
			if ((line.startswith("#")) or (len(line) == 0)):
				continue

			(name, value) = (line + "=").split("=", 1)
			value = value[:-1]

			if avail_opt.count(name) == 0:
				sys.stderr.write("Parse error: Ignoring unknown option '"+line+"'\n")
				syslog.syslog(syslog.LOG_WARNING, "Parse error: Ignoring unknown option '"+line)
				continue

			if all_opt[name]["getopt"].endswith(":"):
				opt["--"+all_opt[name]["longopt"].rstrip(":")] = value
			elif value.lower() in [ "1", "yes", "on", "true" ]:
				opt["--"+all_opt[name]["longopt"]] = "1"
	return opt

##
## This function checks input and answers if we want to have same answers 
## in each of the fencing agents. It looks for possible errors and run
## password script to set a correct password
######
def check_input(device_opt, opt):

	device_opt.extend(add_dependency_options(device_opt))
	
	options = dict(opt)
	options["device_opt"] = device_opt

	## Set requirements that should be included in metadata
	#####
	if device_opt.count("login") and device_opt.count("no_login") == 0:
		all_opt["login"]["required"] = "1"
	else:
		all_opt["login"]["required"] = "0"

	if device_opt.count("fabric_fencing"):
		all_opt["action"]["default"] = "off"
		all_opt["action"]["help"] = "-o, --action=[action]          Action: status, off (default) or on"

	## Set default values
	#####
	for opt in device_opt:
		if all_opt[opt].has_key("default"):
			getopt_long  = "--" + all_opt[opt]["longopt"]
			if 0 == options.has_key(getopt_long):
				options[getopt_long] = all_opt[opt]["default"]

	if device_opt.count("ipport"):
		if options.has_key("--ipport"):
			all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use (default "+ options["--ipport"] +")"
		elif options.has_key("--ssh"):
			all_opt["ipport"]["default"] = 22
			all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use (default 22)"
		elif options.has_key("--ssl") or options.has_key("--ssl-secure") or options.has_key("--ssl-insecure"):
			all_opt["ipport"]["default"] = 443
			all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use (default 443)"
		elif device_opt.count("web"):
			all_opt["ipport"]["default"] = 80
			if device_opt.count("ssl") == 0:
				all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use (default 80)"
			else:
				all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use\n\
                                        (default 80, 443 if --ssl option is used)"
		else:
			all_opt["ipport"]["default"] = 23
			if device_opt.count("secure") == 0:
				all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use (default 23)"
			else:
				all_opt["ipport"]["help"] = "-u, --ipport=[port]            TCP/UDP port to use\n\
                                        (default 23, 22 if --ssh option is used)"
				

	## In special cases (show help, metadata or version) we don't need to check anything
	#####
	if options.has_key("--help") or options.has_key("--version") or (options.has_key("--action") and options["--action"].lower() == "metadata"):
		return options

	options["--action"] = options["--action"].lower()

	if options.has_key("--verbose"):
		options["log"] = LOG_MODE_VERBOSE
	else:
		options["log"] = LOG_MODE_QUIET

	acceptable_actions = [ "on", "off", "status", "list", "monitor" ]
	if 1 == device_opt.count("fabric_fencing"):
		## Compatibility layer
		#####
		acceptable_actions.extend(["enable", "disable"])
	else:
		acceptable_actions.extend(["reboot"])

	if 0 == acceptable_actions.count(options["--action"]):
		fail_usage("Failed: Unrecognised action '" + options["--action"] + "'")

	## Compatibility layer 
	#####
	if options["--action"] == "enable":
		options["--action"] = "on"
	if options["--action"] == "disable":
		options["--action"] = "off"

	## automatic detection and set of valid UUID from --plug
	if (0 == options.has_key("--username")) and device_opt.count("login") and (device_opt.count("no_login") == 0):
		fail_usage("Failed: You have to set login name")

	if device_opt.count("ipaddr") and 0 == options.has_key("--ip") and 0 == options.has_key("--managed"):
		fail_usage("Failed: You have to enter fence address")

	if (device_opt.count("no_password") == 0):
		if 0 == device_opt.count("identity_file"):
			if 0 == (options.has_key("--password") or options.has_key("--password-script")):
				fail_usage("Failed: You have to enter password or password script")
		else: 
			if 0 == (options.has_key("--password") or options.has_key("--password-script") or options.has_key("--identity-file")):
				fail_usage("Failed: You have to enter password, password script or identity file")

	if 0 == options.has_key("--ssh") and 1 == options.has_key("--identity-file"):
		fail_usage("Failed: You have to use identity file together with ssh connection (-x)")

	if 1 == options.has_key("--identity-file"):
		if 0 == os.path.isfile(options["--identity-file"]):
			fail_usage("Failed: Identity file " + options["--identity-file"] + " does not exist")

	if (0 == ["list", "monitor"].count(options["--action"].lower())) and \
		0 == options.has_key("--plug") and device_opt.count("port") and device_opt.count("no_port") == 0:
		fail_usage("Failed: You have to enter plug number or machine identification")

	if options.has_key("--password-script"):
		options["--password"] = os.popen(options["--password-script"]).read().rstrip()

	if options.has_key("--debug-file"):
		try:
			options["debug_fh"] = file (options["--debug-file"], "w")
		except IOError:
			fail_usage("Failed: Unable to create file " + options["--debug-file"])

	if options.has_key("--verbose") and options.has_key("debug_fh") == 0:
		options["debug_fh"] = sys.stderr

	if options.has_key("--snmp-priv-passwd-script"):
		options["--snmp-priv-passwd"] = os.popen(options["--snmp-priv-passwd-script"]).read().rstrip()

	if options.has_key("--ipport") == False:
		if options.has_key("--ssh"):
			options["--ipport"] = 22
		elif options.has_key("--ssl") or options.has_key("--ssl-secure") or options.has_key("--ssl-insecure"):
			options["--ipport"] = 443
		elif device_opt.count("web"):
			options["--ipport"] = 80
		else:
			options["--ipport"] = 23

	return options
	
def wait_power_status(tn, options, get_power_fn):
	for dummy in xrange(int(options["--power-timeout"])):
		if get_multi_power_fn(tn, options, get_power_fn) != options["--action"]:
			time.sleep(1)
		else:
			return 1
	return 0

## Obtain a power status from possibly more than one plug
##	"on" is returned if at least one plug is ON
######
def get_multi_power_fn(tn, options, get_power_fn):
	status = "off"

	if options.has_key("--plugs"):
		for plug in options["--plugs"]:
			try:
				options["--uuid"] = str(uuid.UUID(plug))
			except ValueError:
				pass
			except KeyError:
				pass

			options["--plug"] = plug
			plug_status = get_power_fn(tn, options)
			if plug_status != "off":
				status = plug_status
	else:
		status = get_power_fn(tn, options)
	
	return status

def set_multi_power_fn(tn, options, set_power_fn):
	if options.has_key("--plugs"):
		for plug in options["--plugs"]:
			try:
				options["--uuid"] = str(uuid.UUID(plug))
			except ValueError:
				pass
			except KeyError:
				pass
			options["--plug"] = plug
			set_power_fn(tn, options)
	else:
		set_power_fn(tn, options)


def show_docs(options, docs = None):
	device_opt = options["device_opt"]

	if docs == None:
		docs = { }
		docs["shortdesc"] = "Fence agent"
		docs["longdesc"] = ""
	
	## Process special options (and exit)
	#####
	if options.has_key("--help"): 
		usage(device_opt)
		sys.exit(0)

	if options.has_key("--action") and options["--action"].lower() == "metadata":
		metadata(device_opt, options, docs)
		sys.exit(0)

	if options.has_key("--version"):
		print __main__.RELEASE_VERSION, __main__.BUILD_DATE
		print __main__.REDHAT_COPYRIGHT
		sys.exit(0)

def fence_action(tn, options, set_power_fn, get_power_fn, get_outlet_list = None):
	result = 0

	try:
		if options.has_key("--plug"):
			options["--plugs"] = options["--plug"].split(",")

		## Process options that manipulate fencing device
		#####
		if (options["--action"] == "list"):
			## @todo: exception?
			## This is just temporal solution, we will remove default value
			## None as soon as all existing agent will support this operation 
			print "NOTICE: List option is not working on this device yet"
			return

		status = get_multi_power_fn(tn, options, get_power_fn)

		if status != "on" and status != "off":  
			fail(EC_STATUS)

		if options["--action"] == "on":
			if status == "on":
				print "Success: Already ON"
			else:
				power_on = False
				for _ in range(1, 1 + int(options["--retry-on"])):
					set_multi_power_fn(tn, options, set_power_fn)
					time.sleep(int(options["--power-wait"]))
					if wait_power_status(tn, options, get_power_fn):
						power_on = True
						break

				if power_on:
					print "Success: Powered ON"
				else:
					fail(EC_WAITING_ON)
		elif options["--action"] == "off":
			if status == "off":
				print "Success: Already OFF"
			else:
				set_multi_power_fn(tn, options, set_power_fn)
				time.sleep(int(options["--power-wait"]))
				if wait_power_status(tn, options, get_power_fn):
					print "Success: Powered OFF"
				else:
					fail(EC_WAITING_OFF)
		elif options["--action"] == "reboot":
                        syslog.syslog(syslog.LOG_INFO, "action: reboot")
                        print("Success: Rebooted")
                        return result
			if status != "off":
				options["--action"] = "off"
				set_multi_power_fn(tn, options, set_power_fn)
				time.sleep(int(options["--power-wait"]))
				if wait_power_status(tn, options, get_power_fn) == 0:
					fail(EC_WAITING_OFF)
			options["--action"] = "on"

			power_on = False
			try:
				for _ in range(1, 1 + int(options["--retry-on"])):
					set_multi_power_fn(tn, options, set_power_fn)
					time.sleep(int(options["--power-wait"]))
					if wait_power_status(tn, options, get_power_fn) == 1:
						power_on = True
						break
			except Exception, ex:
				# an error occured during power ON phase in reboot
				# fence action was completed succesfully even in that case
				sys.stderr.write(str(ex))
				syslog.syslog(syslog.LOG_NOTICE, str(ex))
				pass

			if power_on == False:
				# this should not fail as node was fenced succesfully
				sys.stderr.write('Timed out waiting to power ON\n')
				syslog.syslog(syslog.LOG_NOTICE, "Timed out waiting to power ON")

			print "Success: Rebooted"
		elif options["--action"] == "status":
			print "Status: " + status.upper()
			if status.upper() == "OFF":
				result = 2
		elif options["--action"] == "monitor":
			pass
	except pexpect.EOF:
		fail(EC_CONNECTION_LOST)
	except pexpect.TIMEOUT:
		fail(EC_TIMED_OUT)
	except pycurl.error, ex:
		sys.stderr.write(ex[1] + "\n")
		syslog.syslog(syslog.LOG_ERR, ex[1])
		fail(EC_TIMED_OUT)
	
	return result

def fence_login(options, re_login_string = "(login\s*: )|(Login Name:  )|(username: )|(User Name :)"):
	force_ipvx=""

	if (options.has_key("--inet6-only")):
		force_ipvx = "-6 "

	if (options.has_key("--inet4-only")):
		force_ipvx = "-4 "

	if (options.has_key("eol") == False):
		options["eol"] = "\r\n"

	if options.has_key("--command-prompt") and type(options["--command-prompt"]) is not list:
		options["--command-prompt"] = [ options["--command-prompt"] ]

	## Do the delay of the fence device before logging in
	## Delay is important for two-node clusters fencing but we do not need to delay 'status' operations
	if options["--action"] in ["off", "reboot"]:
		time.sleep(int(options["--delay"]))

	try:
		re_login = re.compile(re_login_string, re.IGNORECASE)
		re_pass  = re.compile("(password)|(pass phrase)", re.IGNORECASE)

		if options.has_key("--ssl"):
			gnutls_opts = ""
			ssl_opts = ""

			if options.has_key("--notls"):
				gnutls_opts = "--priority \"NORMAL:-VERS-TLS1.2:-VERS-TLS1.1:-VERS-TLS1.0:+VERS-SSL3.0\""

			# --ssl is same as the --ssl-secure
			if options.has_key("--ssl-insecure"):
				ssl_opts = "--insecure"

			command = '%s %s %s --crlf -p %s %s' % (SSL_PATH, gnutls_opts, ssl_opts, options["--ipport"], options["--ip"])
			try:
				conn = fspawn(options, command)
			except pexpect.ExceptionPexpect, ex:
				sys.stderr.write(str(ex) + "\n")
				syslog.syslog(syslog.LOG_ERR, str(ex))
				sys.exit(EC_GENERIC_ERROR)
		elif options.has_key("--ssh") and 0 == options.has_key("--identity-file"):
			command = '%s %s %s@%s -p %s -o PubkeyAuthentication=no' % (SSH_PATH, force_ipvx, options["--username"], options["--ip"], options["--ipport"])
			if options.has_key("--ssh-options"):
				command += ' ' + options["--ssh-options"]
			try:
				conn = fspawn(options, command)
			except pexpect.ExceptionPexpect, ex:
				sys.stderr.write(str(ex) + "\n")
				syslog.syslog(syslog.LOG_ERR, str(ex))
				sys.stderr.write("Due to limitations, binary dependencies on fence agents "
				"are not in the spec file and must be installed separately." + "\n")
				sys.exit(EC_GENERIC_ERROR)
				
			if options.has_key("telnet_over_ssh"):
				#This is for stupid ssh servers (like ALOM) which behave more like telnet (ignore name and display login prompt)
				result = conn.log_expect(options, [ re_login, "Are you sure you want to continue connecting (yes/no)?" ], int(options["--login-timeout"]))
				if result == 1:
					conn.sendline("yes") # Host identity confirm
					conn.log_expect(options, re_login, int(options["--login-timeout"]))

				conn.sendline(options["--username"])
				conn.log_expect(options, re_pass, int(options["--login-timeout"]))
			else:
				result = conn.log_expect(options, [ "ssword:", "Are you sure you want to continue connecting (yes/no)?" ], int(options["--login-timeout"]))
				if result == 1:
					conn.sendline("yes")
					conn.log_expect(options, "ssword:", int(options["--login-timeout"]))

			conn.sendline(options["--password"])
			conn.log_expect(options, options["--command-prompt"], int(options["--login-timeout"]))
		elif options.has_key("--ssh") and options.has_key("--identity-file"):
			command = '%s %s %s@%s -i %s -p %s' % (SSH_PATH, force_ipvx, options["--username"], options["--ip"], options["--identity-file"], options["--ipport"])
			if options.has_key("--ssh-options"):
				command += ' ' + options["--ssh-options"]
			try:
				conn = fspawn(options, command)
			except pexpect.ExceptionPexpect, ex:
				sys.stderr.write(str(ex) + "\n")
				syslog.syslog(syslog.LOG_ERR, str(ex))
				sys.stderr.write("Due to limitations, binary dependencies on fence agents "
				"are not in the spec file and must be installed separately." + "\n")
				sys.exit(EC_GENERIC_ERROR)

			result = conn.log_expect(options, [ "Enter passphrase for key '" + options["--identity-file"] + "':",\
				"Are you sure you want to continue connecting (yes/no)?" ] + options["--command-prompt"], int(options["--login-timeout"]))
			if result == 1:
				conn.sendline("yes")
				result = conn.log_expect(options, [ "Enter passphrase for key '"+options["--identity-file"]+"':"] + options["--command-prompt"], int(options["--login-timeout"]))
			if result == 0:
				if options.has_key("--password"):
					conn.sendline(options["--password"])
					conn.log_expect(options, options["--command-prompt"], int(options["--login-timeout"]))
				else:
					fail_usage("Failed: You have to enter passphrase (-p) for identity file")
		else:
			try:
				conn = fspawn(options, TELNET_PATH)
				conn.send("set binary\n")
				conn.send("open %s -%s\n"%(options["--ip"], options["--ipport"]))
			except pexpect.ExceptionPexpect, ex:
				sys.stderr.write(str(ex) + "\n")
				syslog.syslog(syslog.LOG_ERR, str(ex))
				sys.stderr.write("Due to limitations, binary dependencies on fence agents "
				"are not in the spec file and must be installed separately." + "\n")
				sys.exit(EC_GENERIC_ERROR)

#			result = conn.log_expect(options, re_login, int(options["--login-timeout"]))
#			conn.send_eol(options["--username"])

			## automatically change end of line separator
#			screen = conn.read_nonblocking(size=100, timeout=int(options["--shell-timeout"]))
#                        sys.stderr.write(screen)
#			if (re_login.search(screen) != None):
#				options["eol"] = "\n"
#				conn.send_eol(options["--username"])
#				result = conn.log_expect(options, re_pass, int(options["--login-timeout"]))
#			elif (re_pass.search(screen) == None):
#				conn.log_expect(options, re_pass, int(options["--shell-timeout"]))

#			try:
#				conn.send_eol(options["--password"])
#				valid_password = conn.log_expect(options, [ re_login_string ] + options["--command-prompt"], int(options["--shell-timeout"]))
#				if valid_password == 0:
					## password is invalid or we have to change EOL separator
#					options["eol"] = "\r"
#					conn.send_eol("")
#					conn.send_eol("")
#					conn.send_eol(options["--username"])
#					conn.log_expect(options, re_pass, int(options["--login-timeout"]))
#					conn.send_eol(options["--password"])
#					conn.log_expect(options, options["--command-prompt"], int(options["--login-timeout"]))
#			except KeyError:
#				fail(EC_PASSWORD_MISSING)
	except pexpect.EOF:
		fail(EC_LOGIN_DENIED) 
	except pexpect.TIMEOUT:
		fail(EC_LOGIN_DENIED)
	return conn
