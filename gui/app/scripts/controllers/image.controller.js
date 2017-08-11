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
                $scope.showloading = false;
                $scope.url = null;
                $scope.environmentInfo = null;

                getYardstickImageList();
                getCustomImageList(function(image, image_id){});
            }

            function getYardstickImageList(){
                mainFactory.ImageList().get({}).$promise.then(function(response){
                    angular.forEach($scope.yardstickImage, function(ele, index){
                        if(typeof(response.result.images[ele.name]) != 'undefined'){
                            $scope.yardstickImage[index] = response.result.images[ele.name];
                        }
                    });
                }, function(error){
                });
            }

            function getCustomImageList(func){
                mainFactory.ItemDetail().get({
                    'envId': $stateParams.uuid
                }).$promise.then(function(response) {
                    $scope.environmentInfo = response.result.environment;
                    $scope.customImage = [];
                    angular.forEach(response.result.environment.image_id, function(ele){
                        mainFactory.getImage().get({'imageId': ele}).$promise.then(function(responseData){
                            $scope.customImage.push(responseData.result.image);
                            func(responseData.result.image, ele);
                        }, function(errorData){
                        });
                    });
                }, function(error){
                });
            }

            $scope.loadYardstickImage = function(image_name){

                var updateImageTask = $interval(updateYardstickImage, 10000);

                function updateYardstickImage(){
                    mainFactory.ImageList().get({}).$promise.then(function(responseData){
                        if(typeof(responseData.result.images[image_name]) != 'undefined' && responseData.result.images[image_name].status == 'ACTIVE'){
                            angular.forEach($scope.yardstickImage, function(ele, index){
                                if(ele.name == image_name){
                                    $scope.yardstickImage[index] = responseData.result.images[ele.name];
                                }
                            });
                            $interval.cancel(updateImageTask);
                        }
                    },function(errorData){
                    });
                }

                mainFactory.uploadImage().post({'action': 'load_image', 'args': {'name': image_name}}).$promise.then(function(response){
                },function(error){
                });
            }

            $scope.deleteYardstickImage = function(image_name){

                var updateImageTask = $interval(updateYardstickImage, 10000);

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
                            $interval.cancel(updateImageTask);
                        }
                    },function(errorData){
                    });
                }

                mainFactory.uploadImage().post({'action': 'delete_image', 'args': {'name': image_name}}).$promise.then(function(response){
                },function(error){
                });
            }

            $scope.uploadCustomImageByUrl = function(url){
                mainFactory.uploadImageByUrl().post({
                    'action': 'upload_image_by_url',
                    'args': {
                        'environment_id': $stateParams.uuid,
                        'url': url
                    }
                }).$promise.then(function(response){
                    var updateImageTask = $interval(getCustomImageList, 30000, 10, true, function(image, image_id){
                        if(image_id == response.result.uuid && image.status == 'ACTIVE'){
                            $interval.cancel(updateImageTask);
                        }
                    });
                    ngDialog.close();
                }, function(error){
                });
            }

            $scope.uploadCustomImage = function($file, $invalidFiles) {
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
                    } else {

                    }
                    var updateImageTask = $interval(getCustomImageList, 10000, 10, true, function(image, image_id){
                        if(image_id == response.data.result.uuid && image.status == 'ACTIVE'){
                            $interval.cancel(updateImageTask);
                        }
                    });

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

            $scope.deleteCustomImage = function(image_id){
                mainFactory.deleteImage().delete({'imageId': image_id}).$promise.then(function(response){
                    $interval(getCustomImageList, 10000, 5, true, function(image, image_id){
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
