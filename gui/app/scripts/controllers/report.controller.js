'use strict';

angular.module('yardStickGui2App')
    .controller('ReportController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog',
        function ($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog) {


            init();


            function init() {
                getDetailTaskForList();



            }
            $scope.goBack = function goBack() {
                window.history.back();
            }

            function getDetailTaskForList(id) {
                mainFactory.getTaskDetail().get({
                    'taskId': $stateParams.taskId
                }).$promise.then(function (response) {
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
                        $scope.result = response.result.task;
                        $scope.testcaseinfo = response.result.task.result.testcases;
                        var key = Object.keys($scope.testcaseinfo);
                        $scope.testcaseResult = $scope.testcaseinfo[key];
                        console.log($scope.testcaseResult);
                        console.log($scope.result);
                        $scope.envIdForTask = response.result.task.environment_id;
                        getItemIdDetail();
                        console.log($scope.envIdForTask);

                    }
                }, function (error) {

                })
            }

            $scope.goToExternal = function goToExternal(id) {
                var url = External_URL +':'+$scope.jumpPort+'/dashboard/db'+ '/' + id;

                window.open(url, '_blank');
            }

            //请求env信息，然后请求container信息
            function getItemIdDetail() {
                $scope.displayContainerInfo = [];
                mainFactory.ItemDetail().get({
                    'envId': $scope.envIdForTask
                }).$promise.then(function (response) {
                    if (response.status == 1) {
                        if (response.result.environment.container_id.grafana != null) {
                            getConDetail(response.result.environment.container_id.grafana);

                        } else {
                            $scope.jumpPort = 3000;
                        }


                    }
                }, function (error) {
                    alert('Something Wrong!');
                })
            }

            function getConDetail(id) {
                mainFactory.containerDetail().get({
                    'containerId': id
                }).$promise.then(function (response) {
                    if (response.status == 1) {
                        // $scope.podData = response.result;
                        $scope.jumpPort=response.result.container.port;
                        console.log($scope.jumpPort);
                    }

                }, function (error) {

                })

            }







        }
    ]);
