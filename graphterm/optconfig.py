#!/usr/bin/env python
#

import ConfigParser
from optparse import OptionParser

try:
    import json
except ImportError:
    import simplejson as json

class _Options(object):
    pass

class OptConfig(object):
    """ Parses config file, but with option being overridden by command line
    options = { "option1": (<shortname>, [<type='flag'/'str'/'int'/'float'/'bool'>, [<default>, [<help>]]]),
                "option2": ... }
    Option type 'flag' implies command-line option only. Use 'bool' for configurable switches.
    """
    def __init__(self, usage=None, config_file=None, config_opt="config", select_opt="select",
                 use_default_section=True, file_escape="@"):
        """
        If config_opt, then command line can use config_opt to indicate different config file.
        Is select_opt, then command line can use select_opt to indicate the section of the config file to be used.
        (A default value for the select option may be specified in the DEFAULT section.)
        If use_default_section, then option values in the DEFAULT section are used,
        for options not found in a named section.
        If file_escape, it can be used to indicate filepaths for reading JSON values.
        """
        self.option_parser = OptionParser(usage=usage)
        self.config_parser = None

        self.config_file = config_file
        self.config_opt = config_opt
        self.select_opt = select_opt
        self.use_default_section = use_default_section
        self.file_escape = file_escape

        self.flags = {}
        self.opt_types = {}
        self.cfg_defaults = {}
        self.default_section = ConfigParser.DEFAULTSECT

        if config_opt:
            self.add_option(config_opt, help="Configuration file", _internal=True)
        if select_opt:
            self.add_option(select_opt, help="Configuration section selection", _internal=True)

    def add_option(self, option, short=None, opt_type="str", default=None, help=None, _internal=False):
        """ Add command/config option
        """
        if self.config_parser:
            raise Exception("Command args already parsed")

        # Cancel effect of config/select options, if user explicitly specifies them
        if not _internal and self.config_opt and option == self.config_opt:
            self.config_opt = ""
        if not _internal and self.select_opt and option == self.select_opt:
            self.select_opt = ""

        if opt_type == "flag":
            self.flags[option] = default
            self.option_parser.add_option(("-"+short) if short else "",
                                          "--"+option,
                                          dest=option,
                                          default=None,
                                          action="store_false" if default else "store_true",
                                          help=(help or None))
        else:
            self.opt_types[option] = opt_type
            if default is not None:
                if opt_type == "bool" and self.to_bool(default) is None:
                    raise Exception("Invalid boolean default value '%s' for option %s" % (default, option))
                    
                if opt_type == "json" and self.to_obj(default) is None:
                    raise Exception("Invalid JSON default value '%s' for option %s" % (default, option))
                    
                if opt_type in ("int", "float") and type(default).__name__ != opt_type:
                    raise Exception("Mismatch between option type '%s' and default value type '%s' for option %s" % (opt_type, type(default).__name__, option))
                self.cfg_defaults[option] = str(default)
            self.option_parser.add_option(("-"+short) if short else "",
                                          "--"+option,
                                          dest=option,
                                          type=opt_type if opt_type in ("int", "float") else "str",
                                          default=None,
                                          help=(help or None))

    def parse_args(self, args=None):
        """Parse command line arguments (and read config file), returning argument list.
        """
        (self.cmd_options, cmd_args) = self.option_parser.parse_args(args)

        self.cmd_optvalues = {}
        for option in self.options():
            if getattr(self.cmd_options, option, None) is not None:
                self.cmd_optvalues[option] = getattr(self.cmd_options, option)

        if self.config_opt and getattr(self.cmd_options, self.config_opt, None) is not None:
            self.config_file = getattr(self.cmd_options, self.config_opt)

        self.read_config()
        return cmd_args

    def read_config(self):
        self.config_parser = ConfigParser.SafeConfigParser(self.cfg_defaults)
        if self.config_file:
            self.config_parser.read(self.config_file)

        if self.select_opt:
            # Check for select in command line
            select = getattr(self.cmd_options, self.select_opt, None)
            if select is None and self.config_file and self.config_parser.has_option(ConfigParser.DEFAULTSECT, self.select_opt):
                # Check for select in default config section
                select = self.config_parser.get(ConfigParser.DEFAULTSECT, self.select_opt)
            if select is not None:
                self.set_section(select)
        
    def options(self):
        return self.flags.keys() + self.opt_types.keys()

    def config(self):
        return self.config_file
        
    def sections(self):
        return self.config_parser.sections()

    def has_section(self, section):
        return self.config_parser.has_section(section)

    def section(self):
        return self.default_section

    def set_section(self, section=None):
        """ Set section, if available. (Call after parsing args)
        """
        if not self.config_parser:
            raise Exception("Command args not yet parsed")

        if section and self.has_section(section):
            self.default_section = section
        else:
            self.default_section = ConfigParser.DEFAULTSECT

    def getallopts(self, section=None, config_only=False):
        options = _Options()
        for option in self.options():
            setattr(options, option, self.getopt(option, section=section, config_only=config_only))
        return options

    def getopt(self, option, default=None, section=None, config_only=False):
        """ Return option value, with command line values overriding any config file values.
        If config_only, ignore command line values.
        """
        if not self.config_parser:
            raise Exception("Command args not yet parsed")

        if not section:
            section = self.default_section

        opt_type = "flag" if option in self.flags else self.opt_types.get(option)
        value = self.cmd_optvalues.get(option) if not config_only else None
        if value is None:
            # Option not specified in command line
            if self.config_parser.has_option(section, option):
                # Use option from named section
                value = self.config_parser.get(section, option)
            elif self.use_default_section and section != ConfigParser.DEFAULTSECT and self.config_parser.has_option(ConfigParser.DEFAULTSECT, option):
                # Use option from DEFAULT section
                value = self.config_parser.get(ConfigParser.DEFAULTSECT, option)

            if value is None:
                # Option not specified in file either
                return self.flags[option] if option in self.flags else default

        if opt_type == "int":
            if (value is None or value == "") and default is not None:
                return default
            try:
                return int(value)
            except Exception, excp:
                raise Exception("Invalid int value for option %s=%s in section %s: %s" % (option, value, section, excp))
        if opt_type == "float":
            if (value is None or value == "") and default is not None:
                return default
            try:
                return float(value)
            except Exception, excp:
                raise Exception("Invalid float value for option %s=%s in section %s: %s" % (option, value, section, excp))
        if opt_type == "bool" or opt_type == "flag":
            bool_value = self.to_bool(value)
            if bool_value is None:
                raise Exception("Invalid boolean option value %s=%s in section %s" % (option, value, section))
            value = bool_value

        if opt_type == "json":
            value = value.strip()
            if value.startswith(self.file_escape):
                try:
                    # Read multiline JSON value from file (ignoring comment lines)
                    with open(value[len(self.file_escape):].strip()) as f:
                        value = "".join(line for line in f.readlines() if not line.lstrip().startswith("#"))
                except Exception:
                    value = default
            if value is not None:
                obj = self.to_obj(value)
                if obj is None:
                    raise Exception("Invalid JSON option value %s=%s in section %s" % (option, value, section))
                value = obj

        return value

    def to_obj(self, value):
        try:
            return json.loads(value)
        except Exception:
            return None

    def to_bool(self, value):
        if type(value) is bool:
            return value
        if value.lower() in ("1", "on", "true", "yes"):
            return True
        if value.lower() in ("0", "off", "false", "no"):
            return False
        return None
            

if __name__ == "__main__":
    # Try the following commands:
    # ./optconfig.py -h
    # ./optconfig.py
    # ./optconfig.py --option=cmdline_value
    # ./optconfig.py --select=section1
    # ./optconfig.py --select=section2
    # ./optconfig.py --config=""          # To ignore config file
    
    parser = OptConfig(usage="optconfig.py [options] arg1 ...", config_file="optconfig.cfg")
    parser.add_option("count", short="c", opt_type="int", help="Count")
    parser.add_option("json", short="j", opt_type="json", help="JSON Option help info")
    parser.add_option("option", short="o", help="Option help info")
    parser.add_option("test", short="t", opt_type="bool")
    parser.add_option("verbose", short="v", opt_type="flag")
    parser.parse_args()

    for option in parser.options():
        print "%s = %s (%s)" % (option, parser.getopt(option), type(parser.getopt(option)))
    
