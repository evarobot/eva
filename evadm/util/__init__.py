# coding=utf-8
import os
from vikicommon.gate.nlu import nlu_gate
from vikicommon.gate.cms import cms_gate
from vikicommon.gate.data import data_gate


PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))
