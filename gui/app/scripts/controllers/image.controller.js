'use strict';

angular.module('yardStickGui2App')
    .controller('ImageController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', '$interval', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, $interval, ngDialog) {


            init();
            $scope.showloading = false;
            $scope.ifshowStatus = 0;

            $scope.yardstickImage = [
                {
                    'name': 'yardstick-image',
                    'description': '',
                    'size': 'N/A',
                    'status': 'N/A',
                    'time': 'N/A'
                },
                {
                    'name': 'Ubuntu-16.04',
                    'description': '',
                    'size': 'N/A',
                    'status': 'N/A',
                    'time': 'N/A'
                },
                {
                    'name': 'cirros-0.3.5',
                    'description': '',
                    'size': 'N/A',
                    'status': 'N/A',
                    'time': 'N/A'
                }
            ];

            $scope.customImage = [];

            function init() {


                $scope.uuid = $stateParams.uuid;
                $scope.uploadImage = uploadImage;
                $scope.showloading = false;
                $scope.url = null;
                getYardstickImageList();
                getCustomImageList();
            }

            $scope.loadImage = function(image_name){

                function updateYardstickImage(){
                    mainFactory.ImageList().get({}).$promise.then(function(responseData){
                        if(typeof(responseData.result.images[image_name]) != 'undefined' && responseData.result.images[image_name].status == 'ACTIVE'){
                            angular.forEach($scope.yardstickImage, function(ele, index){
                                if(ele.name == image_name){
                                    $scope.yardstickImage[index].size = responseData.result.images[ele.name].size / 1024 / 1024;
                                    $scope.yardstickImage[index].status = responseData.result.images[ele.name].status;
                                    $scope.yardstickImage[index].time = responseData.result.images[ele.name].time;
                                }
                            });
                            $interval.cancel($scope.getImageTask);
                        }
                    },function(errorData){
                    });
                }

                mainFactory.uploadImage().post({'action': 'load_image', 'args': {'name': image_name}}).$promise.then(function(response){
                },function(error){
                });

                $scope.getImageTask = $interval(updateYardstickImage, 10000);
            }

            $scope.deleteYardstickImage = function(image_name){

                function updateYardstickImage(){
                    mainFactory.ImageList().get({}).$promise.then(function(responseData){
                        if(typeof(responseData.result.images[image_name]) == 'undefined'){
                            angular.forEach($scope.yardstickImage, function(ele, index){
                                if(ele.name == image_name){
                                    $scope.yardstickImage[index].size = 'N/A';
                                    $scope.yardstickImage[index].status = 'N/A';
                                    $scope.yardstickImage[index].time = 'N/A';
                                }
                            });
                            $interval.cancel($scope.getImageTask);
                        }
                    },function(errorData){
                    });
                }

                mainFactory.uploadImage().post({'action': 'delete_image', 'args': {'name': image_name}}).$promise.then(function(response){
                },function(error){
                });

                $scope.getImageTask = $interval(updateYardstickImage, 10000);
            }

            $scope.deleteCustomImage = function(image_id){
                mainFactory.deleteImage().delete({'imageId': image_id}).$promise.then(function(response){
                    getCustomImageList();
                }, function(error){
                });
            }

            function getYardstickImageList(){
                mainFactory.ImageList().get({}).$promise.then(function(response){
                    angular.forEach($scope.yardstickImage, function(ele, index){
                        if(typeof(response.result.images[ele.name]) != 'undefined'){
                            $scope.yardstickImage[index].size = response.result.images[ele.name].size / 1024 / 1024;
                            $scope.yardstickImage[index].status = response.result.images[ele.name].status;
                            $scope.yardstickImage[index].time = response.result.images[ele.name].time;
                        }
                    });
                }, function(error){
                });
            }

            function getCustomImageList(){
                mainFactory.ItemDetail().get({
                    'envId': $stateParams.uuid
                }).$promise.then(function(response) {
                    $scope.customImage = [];
                    angular.forEach(response.result.environment.image_id, function(ele){
                        mainFactory.getImage().get({'imageId': ele}).$promise.then(function(responseData){
                            $scope.customImage.push(responseData.result.image);
                        }, function(errorData){
                        });
                    });
                }, function(error){
                });
            }

            $scope.openImageDialog = function(){
                $scope.url = null;
                ngDialog.open({
                    preCloseCallback: function(value) {
                    },
                    template: 'views/modal/imageDialog.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 950,
                    showClose: true,
                    closeByDocument: false
                })
            }

            $scope.uploadImageByUrl = function(url){
                mainFactory.uploadImageByUrl().post({
                    'action': 'upload_image_by_url',
                    'args': {
                        'environment_id': $stateParams.uuid,
                        'url': url
                    }
                }).$promise.then(function(response){
                    getCustomImageList();
                    ngDialog.close();
                }, function(error){
                });
            }

            function uploadImage($file, $invalidFiles) {
                $scope.showloading = true;

                $scope.displayImageFile = $file;
                Upload.upload({
                    url: Base_URL + '/api/v2/yardstick/images',
                    data: { file: $file, 'environment_id': $scope.uuid, 'action': 'upload_image' }
                }).then(function(response) {

                    $scope.showloading = false;
                    if (response.data.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'upload success',
                            body: 'you can go next step',
                            timeout: 3000
                        });

                        // $scope.podData = response.data.result;

                        // getItemIdDetail();


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
