##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from __future__ import absolute_import
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from api.database import Base


class Tasks(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    task_id = Column(String(30))
    status = Column(Integer)
    error = Column(String(120))
    result = Column(Text)
    details = Column(String(120))

    def __repr__(self):
        return '<Task %r>' % Tasks.task_id


class AsyncTasks(Base):
    __tablename__ = 'asynctasks'
    id = Column(Integer, primary_key=True)
    task_id = Column(String(30))
    status = Column(Integer)
    error = Column(String(120))

    def __repr__(self):
        return '<Task %r>' % AsyncTasks.task_id
