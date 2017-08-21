'use strict';

angular.module('yardStickGui2App')
    .controller('ImageController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', '$interval',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, $interval) {


            init();
            $scope.showloading = false;
            $scope.ifshowStatus = 0;

            function init() {


                $scope.uuid = $stateParams.uuid;
                $scope.uploadImage = uploadImage;
                getItemIdDetail();
                getImageListSimple();
            }

            function getItemIdDetail() {
                mainFactory.ItemDetail().get({
                    'envId': $stateParams.uuid
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.baseElementInfo = response.result.environment;


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

            function getImageListSimple() {

                mainFactory.ImageList().get({}).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.imageListData = response.result.images;
                        // $scope.imageStatus = response.result.status;

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


            function getImageList() {
                if ($scope.intervalImgae != undefined) {
                    $interval.cancel($scope.intervalImgae);
                }
                mainFactory.ImageList().get({}).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.imageListData = response.result.images;
                        $scope.imageStatus = response.result.status;

                        if ($scope.imageStatus == 0) {
                            $scope.intervalImgae = $interval(function() {
                                getImageList();
                            }, 5000);
                        } else if ($scope.intervalImgae != undefined) {
                            $interval.cancel($scope.intervalImgae);
                        }

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
                $scope.imageStatus = 0;
                $interval.cancel($scope.intervalImgae);
                $scope.ifshowStatus = 1;
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
                        setTimeout(function() {
                            getImageList();
                        }, 10000);

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
                $state.go('app.projectList');
            }

            $scope.goNext = function goNext() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.podUpload', { uuid: $scope.uuid });
            }





        }
    ]);
