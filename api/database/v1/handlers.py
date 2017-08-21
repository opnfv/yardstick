##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from api.database import db_session
from api.database.v1.models import Tasks
from api.database.v1.models import AsyncTasks


class TasksHandler(object):

    def insert(self, kwargs):
        task = Tasks(**kwargs)
        db_session.add(task)
        db_session.commit()
        return task

    def get_task_by_taskid(self, task_id):
        task = Tasks.query.filter_by(task_id=task_id).first()
        if not task:
            raise ValueError

        return task

    def update_attr(self, task_id, attr):
        task = self.get_task_by_taskid(task_id)

        for k, v in attr.items():
            setattr(task, k, v)
        db_session.commit()


class AsyncTaskHandler(object):
    def insert(self, kwargs):
        task = AsyncTasks(**kwargs)
        db_session.add(task)
        db_session.commit()
        return task

    def get_task_by_taskid(self, task_id):
        task = AsyncTasks.query.filter_by(task_id=task_id).first()
        if not task:
            raise ValueError

        return task

    def update_attr(self, task_id, attr):
        task = self.get_task_by_taskid(task_id)

        for k, v in attr.items():
            setattr(task, k, v)
        db_session.commit()
