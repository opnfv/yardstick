##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from api.database import db_session
from api.database.models import Tasks


class TasksHandler(object):

    def insert(self, kwargs):
        task = Tasks(**kwargs)
        db_session.add(task)
        db_session.commit()
        return task

    def update_status(self, task, status):
        task.status = status
        db_session.commit()

    def update_error(self, task, error):
        task.error = error
        db_session.commit()

    def get_task_by_taskid(self, task_id):
        task = Tasks.query.filter_by(task_id=task_id).first()
        return task
