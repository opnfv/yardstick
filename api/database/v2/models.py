##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
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
from sqlalchemy import DateTime
from sqlalchemy import Boolean

from api.database import Base


class V2Environment(Base):
    __tablename__ = 'v2_environment'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    name = Column(String(30))
    description = Column(Text)
    openrc_id = Column(String(10))
    image_id = Column(String(30))
    container_id = Column(Text)
    pod_id = Column(String(10))
    time = Column(DateTime)


class V2Openrc(Base):
    __tablename__ = 'v2_openrc'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    name = Column(String(30))
    description = Column(Text)
    environment_id = Column(String(30))
    content = Column(Text)
    time = Column(DateTime)


class V2Image(Base):
    __tablename__ = 'v2_image'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    name = Column(String(30))
    description = Column(Text)
    environment_id = Column(String(30))


class V2Container(Base):
    __tablename__ = 'v2_container'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    name = Column(String(30))
    environment_id = Column(String(30))
    status = Column(Integer)
    port = Column(Integer)
    time = Column(String(30))


class V2Pod(Base):
    __tablename__ = 'v2_pod'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    environment_id = Column(String(30))
    content = Column(Text)
    time = Column(String(30))


class V2Project(Base):
    __tablename__ = 'v2_project'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    name = Column(String(30))
    description = Column(Text)
    time = Column(DateTime)
    tasks = Column(Text)


class V2Task(Base):
    __tablename__ = 'v2_task'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(30))
    name = Column(String(30))
    description = Column(Text)
    project_id = Column(String(30))
    environment_id = Column(String(30))
    time = Column(DateTime)
    case_name = Column(String(30))
    suite = Column(Boolean)
    content = Column(Text)
    result = Column(Text)
    error = Column(Text)
    status = Column(Integer)
