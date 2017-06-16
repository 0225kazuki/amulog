#!/usr/bin/env python
# coding: utf-8

import os
import re
import ipaddress
import logging
import random
import datetime
from collections import defaultdict

import pycrfsuite

from . import lt_common
from . import host_alias
from .crf import items
from .crf import convert

_logger = logging.getLogger(__package__)
DEFAULT_FEATURE_TEMPLATE = "/".join((os.path.dirname(__file__),
                                     "data/crf_template"))


class LTGenCRF(lt_common.LTGen):
    LABEL_DESC = "D"
    LABEL_VAR = "V"
    LABEL_DUMMY = "N"

    def __init__(self, table, sym, model, verbose, template, lwobj):
        super(LTGenCRF, self).__init__(table, sym)
        self.model = model
        self.verbose = verbose
        #self._middle = middle
        self._template = template

        self.trainer = None
        self.tagger = None
        self.converter = convert.FeatureExtracter(self._template)
        self._lwobj = lwobj
        #if self._middle == "re":
        #    self._lwobj = LabelWord(conf)
        #elif len(self._middle) > 0 :
        #    raise NotImplementedError

    def _middle_label(self, w):
        if self._middle == "re":
            return self._lwobj.label(w)
        else:
            return w

    def init_trainer(self, alg = "lbfgs", verbose = False):
        self.trainer = pycrfsuite.Trainer(verbose = verbose)
        self.trainer.select(alg, "crf1d")
        d = {} # for parameter tuning, edit this
        if len(d) > 0:
            self.trainer.set_params(d)

    def train(self, iterable_items):
        for lineitem in iterable_items:
            xseq = self.converter.feature(lineitem)
            yseq = self.converter.label(lineitem)
            self.trainer.append(xseq, yseq)
        self.trainer.train(self.model)

    def train_from_file(self, fp):
        self.train(items.iter_items_from_file(fp))

    def init_tagger(self):
        if not os.path.exists(self.model):
            raise IOError("No trained CRF model for LTGenCRF")
        self.tagger = pycrfsuite.Tagger()
        self.tagger.open(self.model)

    def close_tagger(self):
        if not self.tagger is None:
            self.tagger.close()

    def label_line(self, lineitems):
        if self.tagger is None:
            self.init_tagger()
        fset = self.converter.feature(lineitems)
        l_label = self.tagger.tag(fset)        
        return l_label

    def process_line(self, l_w, l_s):
        lineitems = items.line2items(l_w, midlabel_func = self._middle_label,
                                      dummy_label = self.LABEL_DUMMY)
        l_label = self.label_line(lineitems)
        tpl = []
        for w, label in zip(l_w, l_label):
            if label == self.LABEL_DESC:
                tpl.append(w)
            elif label == self.LABEL_VAR:
                tpl.append(self._sym)
            elif label == self.LABEL_DUMMY:
                raise ValueError("Some word labeled as DUMMY in LTGenCRF")
            else:
                raise ValueError("Unknown labels in LTGenCRF")

        if self._table.exists(tpl):
            tid = self._table.get_tid(tpl)
            return tid, self.state_unchanged
        else:
            tid = self._table.add(tpl)
            return tid, self.state_added


class LabelWord():

    def __init__(self, conf):
        self._d_re = {}

        self._d_re["DIGIT"] = [re.compile(r"^\d+$")]
        self._d_re["DATE"] = [re.compile(r"^\d{2}/\d{2}$"),
                              re.compile(r"^\d{4}-\d{2}-\d{2}")]
        self._d_re["TIME"] = [re.compile(r"^\d{2}:\d{2}:\d{2}$")]

        self._other = "OTHER"
        self._ha = host_alias.HostAlias(conf)
        self._host = "HOST"

    def label(self, word):
        ret = self.isipaddr(word)
        if ret is not None:
            return ret

        if self._ha.isknown(word):
            return self._host
        
        for k, l_reobj in self._d_re.items():
            for reobj in l_reobj:
                if reobj.match(word):
                    return k
        
        return self._other

    @staticmethod
    def isipaddr(word):
        try:
            ret = ipaddress.ip_address(str(word))
            if isinstance(ret, ipaddress.IPv4Address):
                return "IPv4ADDR"
            elif isinstance(ret, ipaddress.IPv6Address):
                return "IPv6ADDR"
            else:
                raise TypeError("ip_address returns unknown type? {0}".format(
                        str(ret)))
        except ValueError:
            return None


class MeasureAccuracy():

    def __init__(self, conf):
        from . import log_db
        self.ld = log_db.LogData(conf)
        self.ld.init_ltmanager()
        self.conf = conf
        self.measure_lt_method = conf.get("measure_lt", "lt_method")
        self.sample_from = conf.get("measure_lt", "sample_from")
        self.sample_rules = self._rules(
            conf.get("measure_lt", "sample_rules"))
        self.trials = conf.getint("measure_lt", "train_trials")
        self.results = []
        
        if self.sample_from == "cross":
            self.cross_k = conf.getint("measure_lt", "cross_k")
            assert self.trials <= self.cross_k, "trials is larger than k"
            self._eval_cross()
        elif self.sample_from == "diff":
            self.sample_train_rules = self._rules(
                conf.get("measure_lt", "sample_train_rules"))
            self.train_sample_method = conf.get("measure_lt",
                                                "train_sample_method")
            self.train_size = conf.getint("measure_lt", "train_size")
            self._eval_diff(self.sample_from)
        elif self.sample_from == "file":
            self.fn = conf.get("measure_lt", "sample_from_file")
            self.train_sample_method = conf.get("measure_lt",
                                                "train_sample_method")
            self.train_size = conf.getint("measure_lt", "train_size")
            self._eval_diff(self.sample_from)
        else:
            raise NotImplementedError

    @staticmethod
    def _rules(rulestr):
        ret = {}
        l_rule = [rule.strip() for rule in rulestr.split(",")]
        for rule in l_rule:
            if rule == "":
                continue
            key, val = [v.strip() for v in rule.split("=")]
            if key in ("host", "area"):
                ret[key] = val
            elif key == "top_date":
                assert not "top_dt" in ret
                ret["top_dt"] = datetime.datetime.strptime(val, "%Y-%m-%d")
            elif key == "top_dt":
                assert not "top_dt" in ret
                ret["top_dt"] = datetime.datetime.strptime(val,
                                                           "%Y-%m-%d %H:%M:%S")
            elif key == "end_date":
                assert not "end_dt" in ret
                ret["end_dt"] = datetime.datetime.strptime(
                    val, "%Y-%m-%d") + datetime.timedelta(days = 1)
            elif key == "end_dt":
                assert not "end_dt" in ret
                ret["end_dt"] = datetime.datetime.strptime(val,
                                                           "%Y-%m-%d %H:%M:%S")
            else:
                raise NotImplementedError
        return ret

    def _eval_cross(self):

        def divide_size(size, groups):
            base = int(size // groups)
            ret = [base] * groups
            surplus = size - (base * groups)
            for i in range(surplus):
                ret[i] += 1
            assert sum(ret) == size
            return ret

        def agg_dict(l_d):
            keyset = set()
            for d in l_d:
                keyset.update(d.keys())

            new_d = defaultdict(int)
            for ltid in keyset:
                for d in l_d:
                    new_d[ltid] += d[ltid]
            return new_d

        l_labeled = [] # (ltid, train)
        for line in self.ld.iter_lines(**self.sample_rules):
            l_labeled.append((line.lt.ltid, items.line2train(line)))
        random.shuffle(l_labeled)

        l_group = []
        l_group_ltidmap = [] # {ltid: cnt}
        basenum = 0
        for size in divide_size(len(l_labeled), self.cross_k):
            l_ltid, l_lm = zip(*l_labeled[basenum:basenum+size])
            l_group.append(l_lm)
            d = defaultdict(int)
            for ltid in l_ltid:
                d[ltid] += 1
            l_group_ltidmap.append(d)
            basenum += size
        assert sum([len(g) for g in l_group]) == len(l_labeled)
        del l_labeled

        for trial in range(self.trials):
            l_train = None
            l_test = []
            l_test_ltidmap = []
            for gid, group, ltidmap in zip(range(self.cross_k),
                                           l_group, l_group_ltidmap):
                if gid == trial:
                    assert l_train is None
                    l_train = group
                    train_ltidmap = ltidmap
                else:
                    l_test += group
                    l_test_ltidmap.append(ltidmap)
            test_ltidmap = agg_dict(l_test_ltidmap)

            d_result = self._trial(l_train, l_test,
                                   train_ltidmap, test_ltidmap)
            self.results.append(d_result)

    def _eval_diff(self, method):

        if method == "diff":
            l_test, test_ltidmap = self._load_test_diff()
        elif method == "file":
            l_test, test_ltidmap = self._load_test_file()

        l_train_all = [] # (ltid, lineitems)
        for line in self.ld.iter_lines(**self.sample_train_rules):
            l_labeled.append((line.lt.ltid, items.line2train(line)))

        if self.train_sample_rules == "all":
            if self.train_size > 1:
                raise UserWarning(("measure_lt.train_size is ignored "
                                   "because the results must be static"))
            l_ltid, l_train = zip(*l_train_all)
            train_ltidmap = defaultdict(int)
            for ltid in l_ltid:
                train_ltidmap[ltid] += 1
            d_result = self._trial(l_train, l_test,
                                   train_ltidmap, test_ltidmap)
            self.results.append(d_result)
        elif self.train_sample_rules == "random":
            for i in range(self.trials):
                l_sampled = random.sample(l_train_all, self.train_size)
                l_ltid, l_train = zip(*l_sampled)
                train_ltidmap = defaultdict(int)
                for ltid in l_ltid:
                    train_ltidmap[ltid] += 1
                d_result = self._trial(l_train, l_test,
                                       train_ltidmap, test_ltidmap)
                self.results.append(d_result)
            pass
        elif self.train_sample_rules == "random-va":
            raise NotImplementedError

    def _load_test_diff(self):
        l_test = []
        test_ltidmap = defaultdict(int)
        for line in self.ld.iter_lines(**self.sample_train_rules):
            l_test.append(items.line2train(line))
            test_ltidmap[ltid] += 1
        return l_test, test_ltidmap

    def _load_test_file(self):
        l_test = []
        for lineitems in items.iter_items_from_file(self.fn):
            l_test.append(lineitems)
        return l_test, defaultdict(int)

    def _trial(self, l_train, l_test, d_ltid_train, d_ltid_test):

        def form_template(ltgen, l_w, l_label):
            tpl = []
            for w, label in zip(l_w, l_label):
                if label == ltgen.LABEL_DESC:
                    tpl.append(w)
                elif label == ltgen.LABEL_VAR:
                    tpl.append(ltgen._sym)
                elif label == ltgen.LABEL_DUMMY:
                    raise ValueError("Some word labeled as DUMMY in LTGenCRF")
                else:
                    raise ValueError
            return tpl

        table = self.ld.ltm._table
        ltgen = lt_common.init_ltgen(self.conf, table, "crf")

        ltgen.init_trainer()
        ltgen.train(l_train)

        wa_numer = 0.0
        wa_denom = 0.0
        la_numer = 0.0
        la_denom = 0.0
        ta_numer = 0.0
        ta_denom = 0.0

        for lineitems in l_test:
            l_correct = items.items2label(lineitems)
            l_w = [item[0] for item in lineitems]
            l_label_correct = [item[-1] for item in lineitems]
            tpl = form_template(ltgen, l_w, l_label_correct)
            l_label = ltgen.label_line(lineitems)

            for w_correct, w_label in zip(l_correct, l_label):
                wa_denom += 1
                if w_correct == w_label:
                    wa_numer += 1
            assert ltgen._table.exists(tpl)
            ltid = ltgen._table.get_tid(tpl)
            cnt = d_ltid_test[ltid]
            la_denom += 1
            ta_denom += 1.0 / cnt
            if l_correct == l_label:
                la_numer += 1
                ta_numer += 1.0 / cnt

        d_result = {"word_acc": wa_numer / wa_denom,
                    "line_acc": la_numer / la_denom,
                    "tpl_acc": ta_numer / ta_denom,
                    "train_size": len(l_train),
                    "test_size": len(l_test),
                    "train_tpl_size": len(d_ltid_train),
                    "test_tpl_size": len(d_ltid_test)}
        return d_result

    def print_info(self):
        print("# Experiment for measuring log template generation accuracy")
        if self.sample_from == "cross":
            print("# type: Cross-validation (k = {0})".format(self.cross_k))
        elif self.sample_from in ("diff", "file"):
            print("# type: Experiment with different data range / domain")
            if self.sample_from == "diff":
                print("# train-source: db({0})".format(
                    self.sample_train_rules))
            elif self.sample_from == "file":
                print("# train-source: file({0})".format(self.fn))
            print("# test-source: db({0})".format(self.sample_rules))
        print("# trials: {0}".format(self.trials))

    def print_result(self):
        import numpy as np
        for rid, result in enumerate(self.results):
            print("Experiment {0}".format(rid))
            for key, val in result.items():
                print(key, val)
            print()

        print("# General result")
        arr_wa = np.array([d["word_acc"] for d in self.results])
        wa = np.average(arr_wa)
        wa_err = np.std(arr_wa) / np.sqrt(arr_wa.size)
        print("Average word accuracy: {0} (err: {1})".format(wa, wa_err))

        arr_la = np.array([d["line_acc"] for d in self.results])
        la = np.average(arr_la)
        la_err = np.std(arr_la) / np.sqrt(arr_la.size)
        print("Average line accuracy: {0} (err: {1})".format(la, la_err))

        arr_ta = np.array([d["tpl_acc"] for d in self.results])
        ta = np.average(arr_ta)
        ta_err = np.std(arr_ta) / np.sqrt(arr_ta.size)
        print("Average template accuracy: {0} (err: {1})".format(ta, ta_err))


def init_ltgen_crf(conf, table, sym):
    model = conf.get("log_template_crf", "model_filename")
    verbose = conf.getboolean("log_template_crf", "verbose")
    middle = conf.get("log_template_crf", "middle_label")
    if middle == "re":
        lwobj = LabelWord(conf)
    elif len(middle) > 0:
        raise NotImplementedError
    else:
        lwobj = None
    template = conf.get("log_template_crf", "feature_template")
    return LTGenCRF(table, sym, model, verbose, template, lwobj)


