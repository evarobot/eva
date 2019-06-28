# coding=utf-8
import os
from evashare.gate.nlu import nlu_gate
from evashare.gate.cms import cms_gate
from evashare.gate.data import data_gate


PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))
