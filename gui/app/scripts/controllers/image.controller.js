'use strict';

angular.module('yardStickGui2App')
    .controller('ImageController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location) {


            init();
            $scope.showloading = false;

            function init() {


                $scope.uuid = $stateParams.uuid;
                $scope.uploadImage = uploadImage;
                getItemIdDetail();
                getImageList();
            }

            function getItemIdDetail() {
                mainFactory.ItemDetail().get({
                    'envId': $stateParams.uuid
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        //存储基础id数据
                        $scope.baseElementInfo = response.result.environment;


                    } else {
                        alert('Something Wrong!');
                    }
                }, function(error) {
                    alert('Something Wrong!');
                })
            }

            function getImageList() {
                mainFactory.ImageList().get({}).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.imageListData = response.result.images;
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'get data failed',
                            body: 'please retry',
                            timeout: 3000
                        });
                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'get data failed',
                        body: 'please retry',
                        timeout: 3000
                    });
                })
            }

            function uploadImage() {
                $scope.showloading = true;
                mainFactory.uploadImage().post({
                    'action': 'load_image',
                    'args': {
                        'environment_id': $scope.uuid

                    }
                }).$promise.then(function(response) {
                    $scope.showloading = false;
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'failed',
                            body: 'something wrong',
                            timeout: 3000
                        });

                    }
                }, function(error) {
                    toaster.pop({
                        type: 'error',
                        title: 'failed',
                        body: 'something wrong',
                        timeout: 3000
                    });
                })
            }

            $scope.goBack = function goBack() {
                $state.go('app2.projectList');
            }

            $scope.goNext = function goNext() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.podUpload', { uuid: $scope.uuid });
            }





        }
    ]);