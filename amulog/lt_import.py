#!/usr/bin/env python
# coding: utf-8

import os
import logging

from . import common
from . import lt_common
from . import lt_misc

_logger = logging.getLogger(__package__)


class LTGenImport(lt_common.LTGen):

    def __init__(self, table, sym, filename, mode, lp):
        super(LTGenImport, self).__init__(table, sym)
        self._table = table
        self._d_def = common.IDDict(lambda x: tuple(x))
        self.searchtree = lt_misc.LTSearchTree(sym)
        self._lp = lp
        #logparser.LogParser(conf, sep_variable = True)
        self._open_def(filename, mode)

    def _open_def(self, filename, mode):
        cnt = 0
        if not os.path.exists(filename):
            raise ValueError("log_template_import.def_path is invalid")
        with open(filename, 'r') as f:
            for line in f:
                if mode == "plain":
                    mes = line.rstrip("\n")
                elif mode == "ids":
                    line = line.rstrip("\n")
                    mes = line.partition(" ")[2].strip()
                else:
                    raise ValueError("imvalid import_mode {0}".format(
                            self.mode))
                ltw, lts = self._lp.split_message(mes)
                defid = self._d_def.add(ltw)
                self.searchtree.add(defid, ltw)
                cnt += 1
        _logger.info("{0} template imported".format(cnt))

    def process_line(self, l_w, l_s):
        defid = self.searchtree.search(l_w)
        if defid is None:
            _logger.debug(
                    "No log template found for message : {0}".format(l_w))
            return None, None
        else:
            tpl = self._d_def.get(defid)
            if self._table.exists(tpl):
                tid = self._table.get_tid(tpl)
                return tid, self.state_unchanged
            else:
                tid = self._table.add(tpl)
                return tid, self.state_added


def init_ltgen_import(conf, table, sym):
    fn = conf.get("log_template_import", "def_path")
    mode = conf.get("log_template_import", "mode")
    from . import logparser
    lp = logparser.LogParser(conf, sep_variable = True)
    return LTGenImport(table, sym, fn, mode, lp)


def search_exception(conf, targets, form):
    
    from . import logparser
    def_path = conf.get("log_template_import", "def_path")
    sym = conf.get("log_template", "variable_symbol")
    mode = conf.get("log_template_import", "mode")
    table = lt_common.TemplateTable()
    temp_lp = logparser.LogParser(conf, sep_variable = True)
    ltgen = LTGenImport(table, sym, def_path, mode, temp_lp)

    for fn in targets:
        _logger.info("lt_import job for ({0}) start".format(fn))
        for org, l_w, l_s in logparser.iter_lines(conf, fn, form):
            tid, dummy = ltgen.process_line(l_w, l_s)
            if tid is None:
                print(org)
        _logger.info("lt_import job for ({0}) done".format(fn))


def filter_org(conf, targets, dirname, style = "date", method = "commit"):
    from . import logparser
    from . import log_db
    from . import strutil
    lp = logparser.LogParser(conf)
    def_path = conf.get("log_template_import", "def_path")
    sym = conf.get("log_template", "variable_symbol")
    mode = conf.get("log_template_import", "mode")
    table = lt_common.TemplateTable()
    temp_lp = logparser.LogParser(conf, sep_variable = True)
    ltgen = LTGenImport(table, sym, def_path, mode, temp_lp)
    rod = log_db.RestoreOriginalData(dirname, style = style, method = method)

    for fn in targets:
        _logger.info("lt_import job for ({0}) start".format(fn))
        with open(fn, "r") as f:
            for line in f:
                dt, org_host, l_w, l_s = lp.process_line(line)
                if l_w is None: continue
                l_w = [strutil.add_esc(w) for w in l_w]
                tid, dummy = ltgen.process_line(l_w, l_s)
                if tid is not None:
                    rod.add_str(dt, line.rstrip("\n"))
        rod.commit()
        _logger.info("lt_import job for ({0}) done".format(fn))


#if __name__ == "__main__":
#    import sys
#    import optparse
#    import config
#    import log_db
#    usage = "usage: {0} [options] fn".format(sys.argv[0])
#    op = optparse.OptionParser(usage)
#    op.add_option("-c", "--config", action="store",
#            dest="conf", type="string", default=config.DEFAULT_CONFIG_NAME,
#            help="configuration file path")
#    op.add_option("-r", action="store_true", dest="recur",
#            default=False, help="search log file recursively")
#    op.add_option("--debug", action="store_true", dest="debug",
#            default=False, help="set logging level to DEBUG")
#    options, args = op.parse_args()
#
#    conf = config.open_config(options.conf)
#    lv = logging.DEBUG if options.debug else logging.INFO
#    config.set_common_logging(conf, _logger, [], lv = lv)
#
#    targets = log_db._get_targets(conf, args, options.recur)
#    search_exception(conf, targets)


