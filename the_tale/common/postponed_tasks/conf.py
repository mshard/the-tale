# coding: utf-8

from dext.common.utils.app_settings import app_settings

postponed_tasks_settings = app_settings('POSTPONED_TASKS', # pylint: disable=C0103
                                        TASK_WAIT_DELAY = 0.5,
                                        TASK_LIVE_TIME = 1*24*60*60) # all ended tasks will be removed after this time has passed
