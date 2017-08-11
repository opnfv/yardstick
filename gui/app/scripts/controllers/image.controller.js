'use strict';

angular.module('yardStickGui2App')
    .controller('ImageController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', '$interval', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, $interval, ngDialog) {


            init();

            function init() {
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


                $scope.uuid = $stateParams.uuid;
                $scope.showloading = false;
                $scope.url = null;
                $scope.environmentInfo = null;

                getYardstickImageList();
                getCustomImageList(function(image, image_id){});
            }

            function getYardstickImageList(){
                mainFactory.ImageList().get({}).$promise.then(function(response){
                    if(response.status == 1){
                        angular.forEach($scope.yardstickImage, function(ele, index){
                            if(typeof(response.result.images[ele.name]) != 'undefined'){
                                $scope.yardstickImage[index] = response.result.images[ele.name];
                            }
                        });
                    }else{
                        mainFactory.errorHandler1(response);
                    }
                }, function(response){
                    mainFactory.errorHandler2(response);
                });
            }

            function getCustomImageList(func){
                mainFactory.ItemDetail().get({
                    'envId': $stateParams.uuid
                }).$promise.then(function(response) {
                    if(response.status == 1){
                        $scope.environmentInfo = response.result.environment;
                        $scope.customImage = [];
                        angular.forEach(response.result.environment.image_id, function(ele){
                            mainFactory.getImage().get({'imageId': ele}).$promise.then(function(responseData){
                                if(responseData.status == 1){
                                    $scope.customImage.push(responseData.result.image);
                                    func(responseData.result.image, ele);
                                }else{
                                    mainFactory.errorHandler1(responseData);
                                }
                            }, function(errorData){
                                mainFactory.errorHandler2(errorData);
                            });
                        });
                    }else{
                        mainFactory.errorHandler1(response);
                    }
                }, function(response){
                    mainFactory.errorHandler2(response);
                });
            }

            $scope.loadYardstickImage = function(image_name){

                var updateImageTask = $interval(updateYardstickImage, 10000);

                function updateYardstickImage(){
                    mainFactory.ImageList().get({}).$promise.then(function(responseData){
                        if(responseData.status == 1){
                            if(typeof(responseData.result.images[image_name]) != 'undefined' && responseData.result.images[image_name].status == 'ACTIVE'){
                                angular.forEach($scope.yardstickImage, function(ele, index){
                                    if(ele.name == image_name){
                                        $scope.yardstickImage[index] = responseData.result.images[ele.name];
                                    }
                                });
                                $interval.cancel(updateImageTask);
                            }
                        }else{
                            mainFactory.errorHandler1(responseData);
                        }
                    },function(errorData){
                        mainFactory.errorHandler2(errorData);
                    });
                }

                mainFactory.uploadImage().post({'action': 'load_image', 'args': {'name': image_name}}).$promise.then(function(response){
                },function(response){
                    mainFactory.errorHandler2(response);
                });
            }

            $scope.deleteYardstickImage = function(image_name){

                var updateImageTask = $interval(updateYardstickImage, 10000);

                function updateYardstickImage(){
                    mainFactory.ImageList().get({}).$promise.then(function(response){
                        if(response.status == 1){
                            if(typeof(response.result.images[image_name]) == 'undefined'){
                                angular.forEach($scope.yardstickImage, function(ele, index){
                                    if(ele.name == image_name){
                                        $scope.yardstickImage[index].size = 'N/A';
                                        $scope.yardstickImage[index].status = 'N/A';
                                        $scope.yardstickImage[index].time = 'N/A';
                                    }
                                });
                                $interval.cancel(updateImageTask);
                            }
                        }else{
                            mainFactory.errorHandler1(response);
                        }
                    },function(response){
                        mainFactory.errorHandler2(response);
                    });
                }

                mainFactory.uploadImage().post({'action': 'delete_image', 'args': {'name': image_name}}).$promise.then(function(response){
                },function(response){
                    mainFactory.errorHandler2(response);
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
                    if(response.status == 1){
                        var updateImageTask = $interval(getCustomImageList, 30000, 10, true, function(image, image_id){
                            if(image_id == response.result.uuid && image.status == 'ACTIVE'){
                                $interval.cancel(updateImageTask);
                            }
                        });
                        ngDialog.close();
                    }else{
                        mainFactory.errorHandler1(response);
                    }
                }, function(response){
                    mainFactory.errorHandler2(response);
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

                        var updateImageTask = $interval(getCustomImageList, 10000, 10, true, function(image, image_id){
                            if(image_id == response.data.result.uuid && image.status == 'ACTIVE'){
                                $interval.cancel(updateImageTask);
                            }
                        });
                    }else{
                        mainFactory.errorHandler1(response);
                    }

                }, function(response) {
                    $scope.uploadfile = null;
                    mainFactory.errorHandler2(response);
                })
            }

            $scope.deleteCustomImage = function(image_id){
                mainFactory.deleteImage().delete({'imageId': image_id}).$promise.then(function(response){
                    if(response.status == 1){
                        $interval(getCustomImageList, 10000, 5, true, function(image, image_id){
                        });
                    }else{
                        mainFactory.errorHandler2(response);
                    }
                }, function(response){
                    mainFactory.errorHandler2(response);
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
                $state.go('app.projectList');
            }

            $scope.goNext = function goNext() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.podUpload', { uuid: $scope.uuid });
            }

        }
    ]);
