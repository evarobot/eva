# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/
import time
import os


PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))


def object_to_dict(obj, attr_list):
    ret = {}
    for attr in attr_list:
        ret[attr] = getattr(obj, attr)
    return ret


# 单例类的装饰器
def singleton(cls):
    """
    @param cls:类名, 注意不是类实例
    """
    _instance = {}

    def _wrapper(*args, **kwargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)
        return _instance[cls]
    return _wrapper


# 计算函数执行时间的花费
def func_execute_time_cost(func):
    """
    @param func:函数对象实例
    """
    def _wrapper(*args, **kwargs):
        start_time = time.time()
        res = func(*args, **kwargs)
        now_time = time.time()
        cost_time = (now_time - start_time)
        print("cost time =%f" % cost_time)
        return res
    return _wrapper


# 高效过滤文件件辅助函数
def any_true(predicate, sequence):
    return True in map(predicate, sequence)


# 高效的过滤出指定文件
def filter_files_efficient(folder_path, filters, return_file_list):
    """
    :param  folder_path: 文件夹路径
    :param  filters: 要过滤出的文件, eg: filters =['.md', '.yml', '.rst']
    :param  return_file_list:返回值
    :return return_file_list : 返回文件列表
    """
    for file_name in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, file_name)):
            filter_files_efficient(os.path.join(folder_path, file_name), filters, return_file_list)
        elif any_true(file_name.endswith, filters):
            return_file_list.append(os.path.join(folder_path, file_name))
