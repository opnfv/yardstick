'use strict';

angular.module('yardStickGui2App')
    .controller('ContainerController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog) {


            init();
            $scope.showloading = false;

            $scope.displayContainerInfo = [];
            $scope.containerList = [{ value: 'create_influxdb', name: "InfluxDB" }, { value: 'create_grafana', name: "Grafana" }]

            function init() {


                $scope.uuid = $stateParams.uuid;
                $scope.createContainer = createContainer;
                $scope.openChooseContainnerDialog = openChooseContainnerDialog;


                getItemIdDetail();

            }

            function getItemIdDetail() {
                $scope.displayContainerInfo = [];
                mainFactory.ItemDetail().get({
                    'envId': $scope.uuid
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.envName = response.result.environment.name;
                        $scope.containerId = response.result.environment.container_id;
                        if ($scope.containerId != null) {

                            var keysArray = Object.keys($scope.containerId);
                            for (var k in $scope.containerId) {
                                getConDetail($scope.containerId[k]);
                            }
                        } else {
                            $scope.podData = null;
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

            function getConDetail(id) {
                mainFactory.containerDetail().get({
                    'containerId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        // $scope.podData = response.result;
                        response.result.container['id'] = id;
                        $scope.displayContainerInfo.push(response.result.container);

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

            function createContainer() {

                $scope.showloading = true;
                mainFactory.runAcontainer().post({
                    'action': $scope.selectContainer.value,
                    'args': {
                        'environment_id': $scope.uuid,
                    }
                }).$promise.then(function(response) {
                    $scope.showloading = false;
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create container success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        setTimeout(function() {
                            getItemIdDetail();
                        }, 10000);
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'Wrong',
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

            function openChooseContainnerDialog() {
                ngDialog.open({
                    template: 'views/modal/chooseContainer.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 500,
                    showClose: true,
                    closeByDocument: false
                })
            }

            function chooseResult(name) {
                $scope.selectContainer = name;
            }
            $scope.goBack = function goBack() {
                $state.go('app.projectList');
            }

            $scope.openDeleteEnv = function openDeleteEnv(id, name) {
                $scope.deleteName = name;
                $scope.deleteId = id;
                ngDialog.open({
                    template: 'views/modal/deleteConfirm.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 500,
                    showClose: true,
                    closeByDocument: false
                })

            }

            $scope.deleteContainer = function deleteContainer() {
                mainFactory.deleteContainer().delete({ 'containerId': $scope.deleteId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete container success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getItemIdDetail();

                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'Wrong',
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



        }
    ]);
