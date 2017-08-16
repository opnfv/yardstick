'use strict';

angular.module('yardStickGui2App')
    .controller('PodController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, ngDialog) {


            init();
            $scope.showloading = false;
            $scope.loadingOPENrc = false;

            function init() {


                $scope.uuid = $stateParams.uuid;
                $scope.uploadFiles = uploadFiles;
                getItemIdDetail();

            }

            function getItemIdDetail() {
                mainFactory.ItemDetail().get({
                    'envId': $scope.uuid
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.name = response.result.environment.name;
                        $scope.podId = response.result.environment.pod_id;
                        if ($scope.podId != null) {
                            getPodDetail($scope.podId);
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

            function getPodDetail(id) {
                mainFactory.getPodDetail().get({
                    'podId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.podData = response.result;

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

            //upload pod file
            function uploadFiles($file, $invalidFiles) {
                $scope.loadingOPENrc = true;

                $scope.displayOpenrcFile = $file;
                timeConstruct($scope.displayOpenrcFile.lastModified);
                Upload.upload({
                    url: Base_URL + '/api/v2/yardstick/pods',
                    data: { file: $file, 'environment_id': $scope.uuid, 'action': 'upload_pod_file' }
                }).then(function(response) {

                    $scope.loadingOPENrc = false;
                    if (response.data.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'upload success',
                            body: 'you can go next step',
                            timeout: 3000
                        });

                        $scope.podData = response.data.result;

                        getItemIdDetail();


                    } else {

                    }

                }, function(error) {
                    $scope.uploadfile = null;
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            function timeConstruct(array) {
                var date = new Date(1398250549490);
                var Y = date.getFullYear() + '-';
                var M = (date.getMonth() + 1 < 10 ? '0' + (date.getMonth() + 1) : date.getMonth() + 1) + '-';
                var D = date.getDate() + ' ';
                var h = date.getHours() + ':';
                var m = date.getMinutes() + ':';
                var s = date.getSeconds();
                $scope.filelastModified = Y + M + D + h + m + s;

            }
            $scope.goBack = function goBack() {
                $state.go('app.projectList');
            }


            $scope.goNext = function goNext() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.container', { uuid: $scope.uuid });
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

            $scope.deletePod = function deletePod() {
                mainFactory.deletePod().delete({ 'podId': $scope.podId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete pod success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        $scope.uuid = $stateParams.uuid;
                        $scope.uploadFiles = uploadFiles;
                        $scope.displayOpenrcFile = null;
                        getItemIdDetail();
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'Wrong',
                            body: response.result,
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