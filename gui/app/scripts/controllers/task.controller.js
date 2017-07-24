'use strict';

angular.module('yardStickGui2App')
    .controller('TaskController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog) {


            init();


            function init() {
                getDetailTaskForList();

            }

            function getDetailTaskForList() {
                mainFactory.getTaskDetail().get({
                    'taskId': $stateParams.taskId
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        if (response.result.task.status == -1) {
                            response.result.task['stausWidth'] = '5%';
                        } else if (response.result.task.status == 0) {
                            response.result.task['stausWidth'] = '50%';
                        } else if (response.result.task.status == 1) {
                            response.result.task['stausWidth'] = '100%';
                        } else if (response.result.task.status == 2) {
                            response.result.task['stausWidth'] = 'red';
                        }

                        $scope.taskDetailData = response.result.task;
                        if ($scope.taskDetailData.environment_id != null) {
                            getItemIdDetail($scope.taskDetailData.environment_id);
                        }

                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }


            function getItemIdDetail(id) {
                mainFactory.ItemDetail().get({
                    'envId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.displayEnv = response.result.environment;

                        if (response.result.environment.pod_id != null) {
                            getPodDetail(response.result.environment.pod_id);
                        } else if (response.result.environment.image_id != null) {
                            getImageDetail(response.result.environment.image_id);
                        } else if (response.result.environment.openrc_id != null) {
                            getOpenrcDetail(response.result.environment.openrc_id != null);
                        } else if (response.result.environment.container_id.length != 0) {
                            $scope.displayContainerDetail = [];
                            var containerArray = response.result.environment.container_id;
                            for (var i = 0; i < containerArray.length; i++) {
                                getContainerId(containerArray[i]);
                            }

                        }
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'fail',
                            body: response.error_msg,
                            timeout: 3000
                        });
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            //getopenRcid
            function getOpenrcDetail(openrcId) {
                mainFactory.getEnvironmentDetail().get({
                    'openrc_id': openrcId
                }).$promise.then(function(response) {
                    //openrc数据
                    $scope.openrcInfo = response.result;
                    // buildToEnvInfo($scope.openrcInfo.openrc)
                }, function(response) {

                })
            }


            //getImgDetail
            function getImageDetail(id) {
                mainFactory.ImageDetail().get({
                    'image_id': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.imageDetail = response.result.image;

                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            //getPodDetail
            function getPodDetail(id) {
                mainFactory.podDeatil().get({
                    'podId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.podDetail = response.result.pod;
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }
            //getContainerDetail
            function getContainerId(containerId) {
                mainFactory.containerDetail().get({
                    'containerId': containerId
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.container = response.result.container;
                        $scope.displayContainerDetail.push($scope.container);

                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'fail',
                            body: response.error_msg,
                            timeout: 3000
                        });
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }
            $scope.goBack = function goBack() {
                window.history.back();
            }








        }
    ]);