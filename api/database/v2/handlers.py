##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
from api.database import db_session
from api.database.v2.models import V2Environment
from api.database.v2.models import V2Openrc
from api.database.v2.models import V2Image
from api.database.v2.models import V2Pod
from api.database.v2.models import V2Container
from api.database.v2.models import V2Project
from api.database.v2.models import V2Task


class V2EnvironmentHandler(object):

    def insert(self, kwargs):
        environment = V2Environment(**kwargs)
        db_session.add(environment)
        db_session.commit()
        return environment

    def list_all(self):
        return V2Environment.query.all()

    def get_by_uuid(self, uuid):
        environment = V2Environment.query.filter_by(uuid=uuid).first()
        if not environment:
            raise ValueError
        return environment

    def update_attr(self, uuid, attr):
        environment = self.get_by_uuid(uuid)
        for k, v in attr.items():
            setattr(environment, k, v)
        db_session.commit()

    def append_attr(self, uuid, attr):
        environment = self.get_by_uuid(uuid)
        for k, v in attr.items():
            value = getattr(environment, k)
            new = '{},{}'.format(value, v) if value else v
            setattr(environment, k, new)
        db_session.commit()

    def delete_by_uuid(self, uuid):
        environment = self.get_by_uuid(uuid)
        db_session.delete(environment)
        db_session.commit()


class V2OpenrcHandler(object):

    def insert(self, kwargs):
        openrc = V2Openrc(**kwargs)
        db_session.add(openrc)
        db_session.commit()
        return openrc

    def get_by_uuid(self, uuid):
        openrc = V2Openrc.query.filter_by(uuid=uuid).first()
        if not openrc:
            raise ValueError
        return openrc

    def delete_by_uuid(self, uuid):
        openrc = self.get_by_uuid(uuid)
        db_session.delete(openrc)
        db_session.commit()


class V2ImageHandler(object):

    def insert(self, kwargs):
        image = V2Image(**kwargs)
        db_session.add(image)
        db_session.commit()
        return image

    def get_by_uuid(self, uuid):
        image = V2Image.query.filter_by(uuid=uuid).first()
        if not image:
            raise ValueError
        return image

    def delete_by_uuid(self, uuid):
        image = self.get_by_uuid(uuid)
        db_session.delete(image)
        db_session.commit()


class V2PodHandler(object):

    def insert(self, kwargs):
        pod = V2Pod(**kwargs)
        db_session.add(pod)
        db_session.commit()
        return pod

    def get_by_uuid(self, uuid):
        pod = V2Pod.query.filter_by(uuid=uuid).first()
        if not pod:
            raise ValueError
        return pod

    def delete_by_uuid(self, uuid):
        pod = self.get_by_uuid(uuid)
        db_session.delete(pod)
        db_session.commit()


class V2ContainerHandler(object):

    def insert(self, kwargs):
        container = V2Container(**kwargs)
        db_session.add(container)
        db_session.commit()
        return container

    def get_by_uuid(self, uuid):
        container = V2Container.query.filter_by(uuid=uuid).first()
        if not container:
            raise ValueError
        return container

    def update_attr(self, uuid, attr):
        container = self.get_by_uuid(uuid)
        for k, v in attr.items():
            setattr(container, k, v)
        db_session.commit()

    def delete_by_uuid(self, uuid):
        container = self.get_by_uuid(uuid)
        db_session.delete(container)
        db_session.commit()


class V2ProjectHandler(object):

    def list_all(self):
        return V2Project.query.all()

    def insert(self, kwargs):
        project = V2Project(**kwargs)
        db_session.add(project)
        db_session.commit()
        return project

    def get_by_uuid(self, uuid):
        project = V2Project.query.filter_by(uuid=uuid).first()
        if not project:
            raise ValueError
        return project

    def update_attr(self, uuid, attr):
        project = self.get_by_uuid(uuid)
        for k, v in attr.items():
            setattr(project, k, v)
        db_session.commit()

    def append_attr(self, uuid, attr):
        project = self.get_by_uuid(uuid)
        for k, v in attr.items():
            value = getattr(project, k)
            new = '{},{}'.format(value, v) if value else v
            setattr(project, k, new)
        db_session.commit()

    def delete_by_uuid(self, uuid):
        project = self.get_by_uuid(uuid)
        db_session.delete(project)
        db_session.commit()


class V2TaskHandler(object):

    def list_all(self):
        return V2Task.query.all()

    def insert(self, kwargs):
        task = V2Task(**kwargs)
        db_session.add(task)
        db_session.commit()
        return task

    def get_by_uuid(self, uuid):
        task = V2Task.query.filter_by(uuid=uuid).first()
        if not task:
            raise ValueError
        return task

    def update_attr(self, uuid, attr):
        task = self.get_by_uuid(uuid)
        for k, v in attr.items():
            setattr(task, k, v)
        db_session.commit()

    def delete_by_uuid(self, uuid):
        task = self.get_by_uuid(uuid)
        db_session.delete(task)
        db_session.commit()
