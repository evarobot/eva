# coding=utf-8
import os
from evecms.services.service import EVECMSService

PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))

cms_rpc = EVECMSService()
