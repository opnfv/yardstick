'use strict';

/**
 * get data factory
 */


var Base_URL;
var Grafana_URL;

angular.module('yardStickGui2App')
    .factory('mainFactory', ['$resource','$rootScope','$http', '$location', 'toaster',function($resource, $rootScope ,$http ,$location, toaster) {

        Base_URL = 'http://' + $location.host() + ':' + $location.port();
        Grafana_URL = 'http://' + $location.host();

        return {

            postEnvironmentVariable: function() {
                return $resource(Base_URL + '/api/v2/yardstick/openrcs', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            uploadOpenrc: function() {
                return $resource(Base_URL + '/ap/v2/yardstick/openrcs', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            getEnvironmentList: function() {
                return $resource(Base_URL+ '/api/v2/yardstick/environments', {}, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            getEnvironmentDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/openrcs/:openrc_id', { openrc_id: "@openrc_id" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            addEnvName: function() {
                return $resource(Base_URL + '/api/v2/yardstick/environments', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            ItemDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/environments/:envId', { envId: "@envId" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            ImageDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/images/:image_id', { image_id: "@image_id" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            podDeatil: function() {
                return $resource(Base_URL + '/api/v2/yardstick/pods/:podId', { podId: "@podId" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            containerDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/containers/:containerId', { containerId: "@containerId" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            ImageList: function() {
                return $resource(Base_URL + '/api/v2/yardstick/images', {}, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            getImage: function(){
                return $resource(Base_URL + '/api/v2/yardstick/images/:imageId', {imageId: "@imageId"}, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            deleteImage: function() {
                return $resource(Base_URL + '/api/v2/yardstick/images/:imageId', { imageId: '@imageId' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            uploadImage: function() {
                return $resource(Base_URL + '/api/v2/yardstick/images', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            uploadImageByUrl: function() {
                return $resource(Base_URL + '/api/v2/yardstick/images', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            getPodDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/pods/:podId', { podId: "@podId" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            runAcontainer: function() {
                return $resource(Base_URL + '/api/v2/yardstick/containers', { podId: "@podId" }, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            getTestcaselist: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testcases', {}, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            getTestcaseDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testcases/:testcasename', { testcasename: "@testcasename" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            suiteList: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testsuites', {}, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            suiteDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testsuites/:suiteName', { suiteName: "@suiteName" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            suiteCreate: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testsuites', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            projectList: function() {
                return $resource(Base_URL + '/api/v2/yardstick/projects', {}, {
                    'get': {
                        method: 'GET'
                    }
                })
            },
            createProjectName: function() {
                return $resource(Base_URL + '/api/v2/yardstick/projects', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            getProjectDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/projects/:project_id', { project_id: "@project_id" }, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            createTask: function() {
                return $resource(Base_URL + '/api/v2/yardstick/tasks', {}, {
                    'post': {
                        method: 'POST'
                    }
                })
            },
            getTaskDetail: function() {
                return $resource(Base_URL + '/api/v2/yardstick/tasks/:taskId', { taskId: "@taskId" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },

            getTaskLog: function(){
                return $resource(Base_URL + '/api/v2/yardstick/tasks/:taskId/log?index=:index', { taskId: "@taskId", index: "@index" }, {
                    'get': {
                        method: 'GET'
                    }
                })
            },

            taskAddEnv: function() {
                return $resource(Base_URL + '/api/v2/yardstick/tasks/:taskId', { taskId: "@taskId" }, {
                    'put': {
                        method: 'PUT'
                    }
                })
            },
            //delete operate
            deleteEnv: function() {
                return $resource(Base_URL + '/api/v2/yardstick/environments/:env_id', { env_id: '@env_id' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deleteOpenrc: function() {
                return $resource(Base_URL + '/api/v2/yardstick/openrcs/:openrc', { openrc: '@openrc' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deletePod: function() {
                return $resource(Base_URL + '/api/v2/yardstick/pods/:podId', { podId: '@podId' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deleteContainer: function() {
                return $resource(Base_URL + '/api/v2/yardstick/containers/:containerId', { containerId: '@containerId' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deleteTestCase: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testcases/:caseName', { caseName: '@caseName' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deleteTestSuite: function() {
                return $resource(Base_URL + '/api/v2/yardstick/testsuites/:suite_name', { suite_name: '@suite_name' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deleteProject: function() {
                return $resource(Base_URL + '/api/v2/yardstick/projects/:project_id', { project_id: '@project_id' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            deleteTask: function() {
                return $resource(Base_URL + '/api/v2/yardstick/tasks/:task_id', { task_id: '@task_id' }, {
                    'delete': {
                        method: 'DELETE'
                    }
                })
            },
            errorHandler1: function(response){
                toaster.pop({
                    'type': 'error',
                    'title': 'error',
                    'body': response.result,
                    'showCloseButton': true
                });
            },
            errorHandler2: function(response){
                toaster.pop({
                    'type': 'error',
                    'title': response.status,
                    'body': response.statusText,
                    'showCloseButton': true
                });
            }

        };
    }]);
