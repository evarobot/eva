# coding=utf-8
import os
from evecms.services.service import EVECMSService
from vikinlu.service import NLUService

PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))

cms_rpc = EVECMSService()
nlu_robot = NLUService()
