#!/usr/bin/env python
# coding: utf-8

"""
Interface to use some functions about Log DB from CLI.
"""

import sys
import os
import datetime
import logging
import argparse
from collections import namedtuple
from collections import defaultdict

from . import common
from . import config

_logger = logging.getLogger(__package__)


def get_targets(ns, conf):
    if ns.recur:
        targets = common.recur_dir(ns.files)
    else:
        targets = common.rep_dir(ns.files)
    return targets


def get_targets_opt(ns, conf):
    if len(ns.files) == 0:
        l_path = config.getlist(conf, "general", "src_path")
        if conf.getboolean("general", "src_recur"):
            targets = common.recur_dir(l_path)
        else:
            targets = common.rep_dir(l_path)
    else:
        targets = get_targets(ns, conf)
    return targets


def generate_testdata(ns):
    from . import testlog
    if ns.conf_path is None:
        conf_path = testlog.DEFAULT_CONFIG
    else:
        conf_path = ns.conf_path
    testlog.generate_testdata(conf_path, ns.file, ns.seed)


def data_filter(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    targets = get_targets_opt(ns, conf)
    dirname = ns.dirname
    if ns.incr:
        method = "incremental"
    else:
        method = "commit"
    from . import lt_import

    lt_import.filter_org(conf, targets, dirname, method = method)


def data_from_db(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    dirname = ns.dirname
    if ns.incr:
        method = "incremental"
    else:
        method = "commit"
    reset = ns.reset

    from . import log_db
    log_db.data_from_db(conf, dirname, method, reset)


def data_from_data(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    dirname = ns.dirname
    targets = get_targets_opt(ns, conf)
    if ns.incr:
        method = "incremental"
    else:
        method = "commit"
    reset = ns.reset

    from . import log_db
    log_db.data_from_data(conf, targets, dirname, method, reset)


def db_make(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    targets = get_targets_opt(ns, conf)
    from . import log_db

    timer = common.Timer("db-make", output = _logger)
    timer.start()
    log_db.process_files(conf, targets, True, lid_header = ns.lid_header)
    timer.stop()


def db_make_init(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    targets = get_targets_opt(ns, conf)
    from . import log_db

    timer = common.Timer("db-make-init", output = _logger)
    timer.start()
    log_db.process_init_data(conf, targets, lid_header = ns.lid_header)
    timer.stop()


def db_add(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    targets = get_targets(ns, conf)
    from . import log_db

    timer = common.Timer("db-add", output = _logger)
    timer.start()
    log_db.process_files(conf, targets, False, lid_header = ns.lid_header)
    timer.stop()


def db_update(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    targets = get_targets(ns, conf)
    from . import log_db

    timer = common.Timer("db-update", output = _logger)
    timer.start()
    log_db.process_files(conf, targets, False, diff = True,
                         lid_header = ns.lid_header)
    timer.stop()


def db_anonymize(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    
    timer = common.Timer("db-anonymize", output = _logger)
    timer.start()
    log_db.anonymize(conf)
    timer.stop()


def reload_area(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    log_db.reload_area(conf)


def show_db_info(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    log_db.info(conf)


def show_lt(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    simple = ns.simple
    log_db.show_lt(conf, simple = simple)


def show_ltg(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    kwargs = {}
    if ns.group is not None:
        kwargs["group"] = ns.group
    log_db.show_lt(conf, **kwargs)


def show_lt_import(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    log_db.show_lt_import(conf)


def show_lt_import_exception(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    form = ns.format
    assert form in ("log", "message")
    targets = get_targets(ns, conf)
    from . import lt_import

    lt_import.search_exception(conf, targets, form)


def show_lt_words(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    d = log_db.agg_words(conf, target = "all")
    print(common.cli_table(sorted(d.items(), key = lambda x: x[1],
                                  reverse = True)))


def show_lt_descriptions(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    d = log_db.agg_words(conf, target = "description")
    print(common.cli_table(sorted(d.items(), key = lambda x: x[1],
                                  reverse = True)))


def show_lt_variables(ns):
    import re

    def repl_var(d):
        reobj = re.compile(r"[0-9]+")
        keys = list(d.keys())
        for k in keys:
            new_k = reobj.sub("\d", k)
            if k == new_k:
                pass
            else:
                d[new_k] += d.pop(k)


    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    d = log_db.agg_words(conf, target = "variable")
    if ns.repld:
        repl_var(d)
    print(common.cli_table(sorted(d.items(), key = lambda x: x[1],
                                  reverse = True)))


def show_lt_breakdown(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ld = log_db.LogData(conf)
    ltid = ns.ltid
    limit = ns.lines
    ret = lt_tool.breakdown_ltid(ld, ltid, limit)
    print(ret)


def show_lt_vstable(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ld = log_db.LogData(conf)
    lt_tool.search_stable_variable(ld, th = 1)


#def show_lt_vstable_rule(ns):
#    conf = config.open_config(ns.conf_path)
#    lv = logging.DEBUG if ns.debug else logging.INFO
#    config.set_common_logging(conf, logger = _logger, lv = lv)
#    from . import log_db
#    from . import lt_tool
#
#    restr = ns.word
#    update = ns.update
#    ld = log_db.LogData(conf)
#    lt_tool.search_stable_vrule(ld, restr, update)

def lttool_merge(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ltid1 = ns.ltid1
    ltid2 = ns.ltid2
    ld = log_db.LogData(conf)
    lt_tool.merge_ltid(ld, ltid1, ltid2)


def lttool_separate(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ltid = ns.ltid
    vid = ns.vid
    word = ns.word
    ld = log_db.LogData(conf)
    lt_tool.separate_ltid(ld, ltid, vid, word)


def lttool_split(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ltid = ns.ltid
    vid = ns.vid
    ld = log_db.LogData(conf)
    lt_tool.split_ltid(ld, ltid, vid)


def lttool_fix(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ltid = ns.ltid
    l_vid = ns.vids
    ld = log_db.LogData(conf)
    lt_tool.fix_ltid(ld, ltid, l_vid)


def lttool_free(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    ltid = ns.ltid
    l_wid = ns.wids
    ld = log_db.LogData(conf)
    lt_tool.free_ltid(ld, ltid, l_wid)


def lttool_fix_search(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    restr = ns.rule
    dry = ns.dry
    ld = log_db.LogData(conf)
    lt_tool.search_stable_vrule(ld, restr, dry)


def lttool_free_search(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_tool

    restr = ns.rule
    dry = ns.dry
    ld = log_db.LogData(conf)
    lt_tool.search_desc_free(ld, restr, dry)


def show_ltg_label(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import lt_label

    lt_label.list_ltlabel(conf)


def show_log_label(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import lt_label

    lt_label.count_ltlabel(conf)


def show_host(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db

    log_db.show_all_host(conf)


def show_log(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    lidflag = ns.lid

    d = parse_condition(ns.conditions)
    ld = log_db.LogData(conf)
    for e in ld.iter_lines(**d):
        if lidflag:
            print("{0} {1}".format(e.lid, e.restore_line()))
        else:
            print(e.restore_line())


def make_crf_train(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_crf

    size = int(ns.train_size)
    method = ns.method
    d = parse_condition(ns.conditions)
    ld = log_db.LogData(conf)
    iterobj = ld.iter_lines(**d)
    l_train = lt_crf.make_crf_train(conf, l_lm, size, method)
    print("\n\n".join(l_train))


def make_crf_model(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_crf

    size = int(ns.train_size)
    method = ns.method
    d = parse_condition(ns.conditions)
    ld = log_db.LogData(conf)
    iterobj = [lm for lm in ld.iter_lines(**d)]
    fn = lt_crf.make_crf_model(conf, iterobj, size, method)
    print("> {0}".format(fn))


def make_crf_model_ideal(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import log_db
    from . import lt_crf
    
    if int(ns.train_size) <= 0:
        size = None
    else:
        size = int(ns.train_size)
    ld = log_db.LogData(conf)
    fn = lt_crf.make_crf_model_ideal(conf, ld, size)
    print("> {0}".format(fn))


def make_lt_mp(ns):
    conf = config.open_config(ns.conf_path)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import lt_crf
    targets = get_targets_opt(ns, conf)
    check_import = ns.check_import

    s_tpl = lt_crf.generate_lt_mprocess(conf, targets,
                                        check_import, pal = ns.pal)
    for tpl in s_tpl:
        print(" ".join(tpl))


def parse_condition(conditions):
    """
    Args:
        conditions (list)
    """
    d = {}
    for arg in conditions:
        if not "=" in arg:
            raise SyntaxError
        key = arg.partition("=")[0]
        if key == "ltid":
            d["ltid"] = int(arg.partition("=")[-1])
        elif key == "gid":
            d["ltgid"] = int(arg.partition("=")[-1])
        elif key == "top_date":
            date_string = arg.partition("=")[-1]
            d["top_dt"] = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        elif key == "end_date":
            date_string = arg.partition("=")[-1]
            d["end_dt"] = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        elif key == "date":
            date_string = arg.partition("=")[-1]
            d["top_dt"] = datetime.datetime.strptime(date_string, "%Y-%m-%d")
            d["end_dt"] = d["top_dt"] + datetime.timedelta(days = 1)
        elif key == "host":
            d["host"] = arg.partition("=")[-1]
        elif key == "area":
            d["area"] = arg.partition("=")[-1]
    return d


def measure_crf(ns):
    ex_defaults = ["/".join((os.path.dirname(__file__), 
                             "data/measure_crf.conf.default"))]
    conf = config.open_config(ns.conf_path, ex_defaults)
    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(conf, logger = _logger, lv = lv)
    from . import lt_crf

    timer = common.Timer("measure-crf", output = _logger)
    timer.start()
    ma = lt_crf.MeasureAccuracy(conf)
    if len(ma.results) == 0:
        raise ValueError("No measure results found")
    print(ma.info())
    print()
    print(ma.result())
    if ns.failure:
        from . import log_db
        ld = log_db.LogData(conf)
        with open(ns.failure, "w") as f:
            f.write(ma.failure_report(ld))
    timer.stop()


def measure_crf_multi(ns):
    from . import lt_crf

    def process_measure_crf(conf, conf_name):
        _logger.info("process {0} start".format(conf_name))
        output = "result_" + conf_name
        ma = lt_crf.MeasureAccuracy(conf)
        if len(ma.results) == 0:
            raise ValueError("No measure results found")
        buf = []
        buf.append(ma.info())
        buf.append("")
        buf.append(ma.result())
        with open(output, "w") as f:
            f.write("\n".join(buf))
        print("> {0}".format(output))
        _logger.info("process {0} finished".format(conf_name))


    ex_defaults = ["/".join((os.path.dirname(__file__), 
                             "data/measure_crf.conf.default"))]
    l_conf = [config.open_config(conf_path, ex_defaults)
              for conf_path in ns.confs]
    l_conf_name = ns.confs[:]
    if ns.configset is not None:
        l_conf += config.load_config_group(ns.configset, ex_defaults)
        l_conf_name += config.read_config_group(ns.configset)

    if len(l_conf) == 0:
        sys.exit("No configuration file is given")
    diff_keys = ["log_template_crf.model_filename"]
    if not config.check_all_diff(ns.confs, diff_keys, l_conf):
        print(("This experiment makes no sense because model file "
               "will be overwritten !"))
        sys.exit()
    diff_keys = ns.diff
    if not config.check_all_diff(ns.confs, diff_keys, l_conf):
        print("Option value check failed, so exited")
        sys.exit()


    lv = logging.DEBUG if ns.debug else logging.INFO
    config.set_common_logging(l_conf[0], logger = _logger, lv = lv)

    import multiprocessing
    timer = common.Timer("measure-crf-multi task", output = _logger)
    timer.start()
    l_process = [multiprocessing.Process(name = args[1],
                                         target = process_measure_crf,
                                         args = args)
                 for args in zip(l_conf, l_conf_name)]
    common.mprocess_queueing(l_process, ns.pal)
    timer.stop()


def conf_defaults(ns):
    config.show_default_config()


def conf_diff(ns):
    files = ns.files[:]
    if ns.configset:
        files += config.read_config_group(ns.configset)
    config.show_config_diff(files)


def conf_minimum(ns):
    conf = config.open_config(ns.conf_path, nodefault = True, noimport = True)
    conf = config.minimize(conf)
    config.write(ns.conf_path, conf)
    print("rewrite {0}".format(ns.conf_path))


def conf_set_edit(ns):
    l_conf_name = config.read_config_group(ns.configset)
    key = ns.key
    rulestr = ns.rule

    if "(" in rulestr:
        temp = rulestr.rstrip(")").split("(")
        if not len(temp) == 2:
            raise ValueError("bad format for value specification")
        rulename, argstr = temp
        args = argstr.split(",")

        if rulename == "list":
            assert len(args) == len(l_conf_name)
            d = {key: args}
        elif rulename == "range":
            assert len(args) == 2
            start, step = [int(v) for v in args]
            l_val = [start + i * step for i in range(len(l_conf_name))]
            d = {key: l_val}
        elif rulename == "power":
            assert len(args) == 2
            start, step = [int(v) for v in args]
            l_val = [start * (i ** step) for i in range(len(l_conf_name))]
            d = {key: l_val}
        elif rulename == "withconf":
            assert len(args) == 1
            l_val = [args[0] + name for i, name in enumerate(l_conf_name)]
            d = {key: l_val}
        elif rulename == "namerange":
            assert len(args) == 1
            l_val = [args[0] + str(i) for i in range(len(l_conf_name))]
            d = {key: l_val}
        else:
            raise NotImplementedError("invalid rule name")
    else:
        l_val = [rulestr] * len(l_conf_name)
        d = {key: l_val}

    config.config_group_edit(l_conf_name, d)


def conf_shadow(ns):
    cond = {}
    incr = []
    for rule in ns.rules:
        if "=" in rule:
            key, val = rule.split("=")
            cond[key] = val
        else:
            incr.append(rule)
    l_conf_name = config.config_shadow(n = ns.number, cond = cond, incr = incr,
                                       fn = ns.conf_path, output = ns.output,
                                       ignore_overwrite = ns.force)

    if ns.configset is not None:
        config.dump_config_group(ns.configset, l_conf_name)
        print(ns.configset)


# common argument settings
OPT_DEBUG = [["--debug"],
             {"dest": "debug", "action": "store_true",
              "help": "set logging level to debug (default: info)"}]
OPT_CONFIG = [["-c", "--config"],
              {"dest": "conf_path", "metavar": "CONFIG", "action": "store",
               #"default": config.DEFAULT_CONFIG,
               "default": None,
               "help": "configuration file path for amulog"}]
OPT_CONFIG_SET = [["-s", "--configset"],
                  {"dest": "configset", "metavar": "CONFIG_SET",
                   "default": None,
                   "help": "use config group definition file"}]
OPT_RECUR = [["-r", "--recur"],
             {"dest": "recur", "action": "store_true",
              "help": "recursively search files to process"}]
OPT_TERM = [["-t", "--term"],
            {"dest": "dt_range",
             "metavar": "DATE1 DATE2", "nargs": 2,
             "help": ("datetime range, start and end in %Y-%M-%d style."
                      "(optional; defaultly use all data in database)")}]
OPT_LID = [["-l", "--lid"],
             {"dest": "lid_header", "action": "store_true",
              "help": "parse lid from head part of log message"}]
ARG_FILE = [["file"],
             {"metavar": "PATH", "action": "store",
              "help": "filepath to output"}]
ARG_FILES = [["files"],
             {"metavar": "PATH", "nargs": "+",
              "help": "files or directories as input"}]
ARG_FILES_OPT = [["files"],
                 {"metavar": "PATH", "nargs": "*",
                  "help": ("files or directories as input "
                           "(optional; defaultly read from config")}]
ARG_DBSEARCH = [["conditions"],
                {"metavar": "CONDITION", "nargs": "+",
                 "help": ("Conditions to search log messages. "
                          "Example: MODE gid=24 date=2012-10-10 ..., "
                          "Keys: ltid, gid, date, top_date, end_date, "
                          "host, area")}]


# argument settings for each modes
# description, List[args, kwargs], func
# defined after functions because these settings use functions
DICT_ARGSET = {
    "testdata": ["Generate test log data.",
                 [OPT_DEBUG, ARG_FILE,
                  [["-c", "--config"],
                   {"dest": "conf_path", "metavar": "CONFIG",
                    "action": "store", "default": None,
                    "help": ("configuration file path for testlog "
                             "(different from that for amulog)")}],
                  [["-s", "--seed"],
                   {"dest": "seed", "metavar": "INT", "action": "store",
                    "default": 0,
                    "help": "seed value to generate random values"}]],
                 generate_testdata],
    "data-filter": ["Straighten data and remove lines of undefined template.",
                    [OPT_CONFIG, OPT_DEBUG, OPT_RECUR,
                     [["-d", "--dirname"],
                      {"dest": "dirname", "metavar": "DIRNAME",
                       "action": "store",
                       "help": "directory name to output"}],
                     [["-i", "--incr"],
                      {"dest": "incr", "action": "store_true",
                       "help": "output incrementally, use with small memory"}],
                     ARG_FILES_OPT],
                    data_filter],
    "data-from-db": ["Generate log data from DB.",
                     [OPT_CONFIG, OPT_DEBUG,
                      [["-d", "--dirname"],
                       {"dest": "dirname", "metavar": "DIRNAME",
                        "action": "store",
                        "help": "directory name to output"}],
                      [["-i", "--incr"],
                       {"dest": "incr", "action": "store_true",
                        "help": "output incrementally, use with small memory"}],
                      [["--reset"],
                       {"dest": "reset", "action": "store_true",
                        "help": "reset log file directory before processing"}],
                      ],
                     data_from_db],
    "data-from-data": ["Re-arrange log file, splitting messages by date.",
                     [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, ARG_FILES_OPT,
                      [["-d", "--dirname"],
                       {"dest": "dirname", "metavar": "DIRNAME",
                        "action": "store",
                        "help": "directory name to output"}],
                      [["-i", "--incr"],
                       {"dest": "incr", "action": "store_true",
                        "help": "output incrementally, use with small memory"}],
                      [["--reset"],
                       {"dest": "reset", "action": "store_true",
                        "help": "reset log file directory before processing"}],
                      ],
                     data_from_data],
    "db-make": [("Initialize database and add log data. "
                 "This fuction works incrementaly."),
                [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, OPT_LID, ARG_FILES_OPT],
                db_make],
    "db-make-init": [("Initialize database and add log data "
                      "for given dataset. "
                      "This function does not consider "
                      "to add other data afterwards."),
                     [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, OPT_LID,
                      ARG_FILES_OPT],
                     db_make_init],
    "db-add": ["Add log data to existing database.",
               [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, OPT_LID, ARG_FILES],
               db_add],
    "db-update": [("Add newer log data (seeing timestamp range) "
                   "to existing database."),
                  [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, OPT_LID, ARG_FILES],
                  db_update],
    "db-anonymize": [("Remove variables in log messages. "
                      "(Not anonymize hostnames; to be added)"),
                     [OPT_CONFIG, OPT_DEBUG],
                     db_anonymize],
    "db-reload-area": ["Reload area definition file from config.",
                       [OPT_CONFIG, OPT_DEBUG],
                       reload_area],
    "show-db-info": ["Show abstruction of database status.",
                     [OPT_CONFIG, OPT_DEBUG, OPT_TERM],
                     show_db_info],
    "show-lt": ["Show all log templates in database.",
                [OPT_CONFIG, OPT_DEBUG,
                 [["-s", "--simple"],
                  {"dest": "simple", "action": "store_true",
                   "help": "only show log templates"}]],
                show_lt],
    "show-ltg": ["Show all log template groups and their members in database.",
                 [OPT_CONFIG, OPT_DEBUG,
                  [["-g", "--group"],
                   {"dest": "group", "action": "store", "default": None,
                    "help": "show members of given labeling group"}]],
                 show_ltg],
    "show-lt-import": ["Output log template definitions in lt_import format.",
                       [OPT_CONFIG, OPT_DEBUG,],
                       show_lt_import],
    "show-lt-import-exception": [("Output log messages in a file "
                                  "that is not defined "
                                  "in lt_import definitions."),
                                 [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, ARG_FILES,
                                  [["-f", "--format"],
                                   {"dest": "format", "action": "store",
                                    "default": "log",
                                    "help": ("message format to load: "
                                             "log: with header,"
                                             "message: without header")}]],
                                 show_lt_import_exception],
    "show-host": ["Show all hostnames in database.",
                  [OPT_CONFIG, OPT_DEBUG],
                  show_host],
    "show-ltg-label": ["Show labels for log template groups",
                       [OPT_CONFIG, OPT_DEBUG],
                       show_ltg_label],
    "show-log-label": ["Show label distributions",
                       [OPT_CONFIG, OPT_DEBUG],
                       show_log_label],
    "show-log": ["Show log messages that satisfy given conditions in args.",
                 [OPT_CONFIG, OPT_DEBUG,
                  [["--lid"],
                   {"dest": "lid", "action": "store_true",
                    "help": "show lid"}],
                  ARG_DBSEARCH],
                 show_log],
    "lttool-countall": ["Show words and their counts in all messages",
                        [OPT_CONFIG, OPT_DEBUG],
                        show_lt_words],
    "lttool-countd": ["Show description words and their counts",
                      [OPT_CONFIG, OPT_DEBUG],
                      show_lt_descriptions],
    "lttool-countv": ["Show variable words and their counts",
                      [OPT_CONFIG, OPT_DEBUG,
                       [["-d", "--digit"],
                        {"dest": "repld", "action": "store_true",
                         "help": "replace digit to \d"}]],
                      show_lt_variables],
    "lttool-breakdown": ["Show variable candidates in a log template.",
                         [OPT_CONFIG, OPT_DEBUG,
                          [["-l", "--ltid"],
                           {"dest": "ltid", "metavar": "LTID",
                            "action": "store", "type": int,
                            "help": "log template identifier to investigate"}
                           ],
                          [["-n", "--number"],
                           {"dest": "lines", "metavar": "LINES",
                            "action": "store", "type": int, "default": 5,
                            "help": "number of variable candidates to show"}
                           ]],
                         show_lt_breakdown],
    "lttool-vstable": ["Show stable variables in the template.",
                       [OPT_CONFIG, OPT_DEBUG,
                        [["-n", "--number"],
                         {"dest": "number", "metavar": "NUMBER",
                          "action": "store", "type": int, "default": 1,
                          "help": "thureshold number to be stable"}]],
                       show_lt_vstable],
    "lttool-merge": ["Merge 2 templates and generate a new template.",
                     [OPT_CONFIG, OPT_DEBUG,
                      [["ltid1"],
                       {"metavar": "LTID1", "action": "store", "type": int,
                        "help": "first log template to merge"}],
                      [["ltid2"],
                       {"metavar": "LTID2", "action": "store", "type": int,
                        "help": "second log template to merge"}],],
                     lttool_merge],
    "lttool-separate": ["Separate messages satisfying the given condition "
                        "and make it a new log template.",
                        [OPT_CONFIG, OPT_DEBUG,
                         [["ltid"],
                          {"metavar": "LTID", "action": "store", "type": int,
                           "help": "log template indentifier"}],
                         [["vid"],
                          {"metavar": "VARIABLE-ID", "action": "store",
                           "type": int,
                           "help": "variable identifier to fix"}],
                         [["word"],
                          {"metavar": "WORD", "action": "store",
                           "help": "a word to fix in the location of vid"}]],
                        lttool_separate],
    "lttool-split": ["Fix variables to split a template into tempaltes. "
                     "Use carefully because this function may cause "
                     "to generate enormous failure templates.",
                     [OPT_CONFIG, OPT_DEBUG,
                      [["ltid"],
                       {"metavar": "LTID", "action": "store", "type": int,
                        "help": "log template indentifier"}],
                      [["vid"],
                       {"metavar": "VARIABLE-ID", "action": "store",
                        "help": "variable identifier to fix"}]],
                     lttool_split],
    "lttool-fix": ["Fix specified stable variable and modify template. "
                   "If not stable, use lttool-split or lttool-separate.",
                   [OPT_CONFIG, OPT_DEBUG,
                    [["ltid"],
                     {"metavar": "LTID", "action": "store", "type": int,
                      "help": "log template to fix"}],
                    [["vids"],
                     {"metavar": "VARIABLE-IDs", "nargs": "+", "type": int,
                      "help": "variable identifiers to fix"}]],
                   lttool_fix],
    "lttool-free": ["Make a description word as a variable"
                    "and modify the template.",
                    [OPT_CONFIG, OPT_DEBUG,
                     [["ltid"],
                      {"metavar": "LTID", "action": "store", "type": int,
                       "help": "log template indentifier"}],
                     [["wids"],
                      {"metavar": "WORD-IDs", "nargs": "+", "type": int,
                       "help": "word locations to fix"}]],
                    lttool_free],
    "lttool-fix-search": ["Search templates with variables of given rule "
                          "and modify templates by fixing them.",
                          [OPT_CONFIG, OPT_DEBUG,
                           [["-d", "--dry-run"],
                            {"dest": "dry",
                             "action": "store_true", "default": False,
                             "help": "do not update templates"}],
                           [["rule"],
                            {"metavar": "RULE", "action": "store",
                             "help": "word / regular expression"}]],
                          lttool_fix_search],
    "lttool-free-search": ["Search templates with words of given rule ",
                           "and modify templates by making them variable.",
                           [OPT_CONFIG, OPT_DEBUG,
                            [["-u", "--update"],
                             {"dest": "update",
                              "action": "store_true", "default": False,
                              "help": "update templates automatically"}],
                            [["rule"],
                             {"metavar": "RULE", "action": "store",
                              "help": "word / regular expression"}]],
                           lttool_free_search],
    "make-crf-train": ["Output CRF training file for given conditions.",
                       [OPT_CONFIG, OPT_DEBUG, ARG_DBSEARCH,
                        [["-n", "--train_size"],
                         {"dest": "train_size", "action": "store",
                          "type": int, "default": 1000,
                          "help": "number of training data to sample"}],
                        [["-m", "--method"],
                         {"dest": "method", "action": "store",
                          "default": "all",
                          "help": "train data sampling method name. "
                                  "[all, random, random-va] is available."}],],
                       make_crf_train],
    "make-crf-model": ["Output CRF trained model file for given conditions.",
                       [OPT_CONFIG, OPT_DEBUG, ARG_DBSEARCH,
                        [["-n", "--train_size"],
                         {"dest": "train_size", "action": "store",
                          "type": int, "default": 1000,
                          "help": "number of training data to sample"}],
                        [["-m", "--method"],
                         {"dest": "method", "action": "store",
                          "default": "all",
                          "help": "train data sampling method name. "
                                  "[all, random, random-va] is available."}],],
                       make_crf_model],
    "make-crf-model-ideal": [("Output CRF trained model file "
                              "in ideal situation "
                              "(correct log cluster is available)."),
                             [OPT_CONFIG, OPT_DEBUG, ARG_DBSEARCH,
                              [["-n", "--train_size"],
                               {"dest": "train_size", "action": "store",
                                "type": int, "default": -1,
                                "help": ("number of training data to sample, "
                                         "if omitted use all log templates")}],
                              ],
                             make_crf_model_ideal],
    "make-lt-mp": [("Generate log templates with CRF "
                    "in multiprocessing."),
                   [OPT_CONFIG, OPT_DEBUG, OPT_RECUR, ARG_FILES_OPT,
                    [["-p", "--pal"],
                     {"dest": "pal", "action": "store",
                      "type": int, "default": 1,
                      "help": "number of processes"}],
                    [["-i", "--import"],
                     {"dest": "check_import", "action": "store_true",
                      "help": ("ignore messages corresponding to "
                               "imported log template definition "
                               "(i.e., process only unknown messages)")}],],
                   make_lt_mp],
    "measure-crf": ["Measure accuracy of CRF-based log template estimation.",
                    [OPT_DEBUG,
                     [["-f", "--failure"],
                      {"dest": "failure", "action": "store",
                       "help": "output failure report"}],
                     [["-c", "--config"],
                      {"dest": "conf_path", "metavar": "CONFIG",
                       "action": "store", "default": None,
                       "help": "extended config file for measure-lt"}],],
                    measure_crf],
    "measure-crf-multi": ["Multiprocessing of measure-crf.",
                          [OPT_DEBUG, OPT_CONFIG_SET,
                           [["-p", "--pal"],
                            {"dest": "pal", "action": "store",
                             "type": int, "default": 1,
                             "help": "number of processes"}],
                           [["-d", "--diff"],
                            {"dest": "diff", "action": "append",
                             "default": [],
                             "help": ("check configs that given option values "
                                      "are all different. This option can "
                                      "be specified multiple times. "
                                      "Example: -d general.import -d ...")}],
                           [["confs"],
                            {"metavar": "CONFIG", "nargs": "*",
                             "help": "configuration files"}]],
                          measure_crf_multi],
    "conf-defaults": ["Show default configurations.",
                     [],
                     conf_defaults],
    "conf-diff": ["Show differences of 2 configuration files.",
                  [OPT_CONFIG_SET,
                   [["files"],
                    {"metavar": "FILENAME", "nargs": "*",
                     "help": "configuration file"}]],
                   conf_diff],
    "conf-minimum": ["Remove default options and comments.",
                     [[["-o", "--overwrite"],
                       {"dest": "overwrite", "action": "store_true",
                        "help": "overwrite file instead of stdout dumping"}],
                      [["conf_path"],
                       {"metavar": "PATH",
                        "help": "config filepath to load"}]],
                      conf_minimum],
    "conf-group-edit" : ["Edit configuration files in a config group.",
                         [[["configset"],
                           {"metavar": "CONFIG_SET",
                            "help": "config group definition file to use"}],
                          [["key"],
                           {"metavar": "KEY",
                            "help": "\"SECTION.OPTION\" to edit"}],
                          [["rule"],
                           {"metavar": "RULE",
                            "help": ("Value specification rule "
                                     "defined in function-like format. "
                                     "Example: \"List(1,10,100,1000)\" "
                                     "Available format: "
                                     "list(values for each config), "
                                     "range(START,STEP), "
                                     "power(START,STEP), "
                                     "withconf(NAME),"
                                     "namerange(NAME)."
                                     "Note that 1 rule for 1 execution.")}]],
                         conf_set_edit],
    "conf-shadow": ["Copy configuration files.",
                    [OPT_CONFIG,
                     [["-f", "--force"],
                      {"dest": "force", "action": "store_true",
                       "help": "Ignore overwrite of output file"}],
                     [["-n", "--number"],
                      {"dest": "number", "metavar": "INT",
                       "action": "store", "type": int, "default": 1,
                       "help": "number of files to generate"}],
                     [["-o", "--output"],
                      {"dest": "output", "metavar": "FILENAME",
                       "action": "store", "type": str, "default": None,
                       "help": "basic output filename"}],
                     [["-s", "--configset"],
                      {"dest": "configset", "metavar": "CONFIG_SET",
                       "default": None,
                       "help": ("define config group "
                                "and dump it in given filename")}],
                     [["rules"],
                      {"metavar": "RULES", "nargs": "*",
                       "help": ("Rules to replace options. You can indicate "
                                "option, or option and its value with =. "
                                "You can use both of them together. "
                                "For example: \"general.import=hoge.conf "
                                "general.logging\"")}]],
                    conf_shadow],
}

USAGE_COMMANDS = "\n".join(["  {0}: {1}".format(key, val[0])
                            for key, val in sorted(DICT_ARGSET.items())])
USAGE = ("usage: {0} MODE [options and arguments] ...\n\n"
         "mode:\n".format(
        sys.argv[0])) + USAGE_COMMANDS

if __name__ == "__main__":
    if len(sys.argv) < 1:
        sys.exit(USAGE)
    mode = sys.argv[1]
    if mode in ("-h", "--help"):
        sys.exit(USAGE)
    commandline = sys.argv[2:]

    desc, l_argset, func = DICT_ARGSET[mode]
    ap = argparse.ArgumentParser(prog = " ".join(sys.argv[0:2]),
                                 description = desc)
    for args, kwargs in l_argset:
        ap.add_argument(*args, **kwargs)
    ns = ap.parse_args(commandline)
    func(ns)

