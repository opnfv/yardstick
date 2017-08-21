'use strict';

angular.module('yardStickGui2App')
    .controller('DetailController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', '$location', 'ngDialog',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, $location, ngDialog) {




            init();
            $scope.showEnvironment = false;
            $scope.envInfo = [];

            function init() {
                $scope.showEnvironments = showEnvironments;
                // $scope.openrcID = $stateParams.uuid;
                $scope.deleteEnvItem = deleteEnvItem;
                $scope.addInfo = addInfo;
                $scope.submitOpenRcFile = submitOpenRcFile;
                $scope.uploadFiles = uploadFiles;
                $scope.addEnvironment = addEnvironment;

                $scope.uuid = $stateParams.uuid;
                $scope.openrcID = $stateParams.opercId;
                $scope.imageID = $stateParams.imageId;
                $scope.podID = $stateParams.podId;
                $scope.containerId = $stateParams.containerId;
                $scope.ifNew = $stateParams.ifNew;


                getItemIdDetail();
            }



            function showEnvironments() {
                $scope.showEnvironment = true;
            }


            function deleteEnvItem(index) {
                $scope.envInfo.splice(index, 1);
            }

            function addInfo() {
                var tempKey = null;
                var tempValue = null;
                var temp = {
                    name: tempKey,
                    value: tempValue
                }
                $scope.envInfo.push(temp);

            }

            function submitOpenRcFile() {
                $scope.showloading = true;

                var postData = {};
                postData['action'] = 'update_openrc';
                rebuildEnvInfo();
                postData['args'] = {};
                postData['args']['openrc'] = $scope.postEnvInfo;
                postData['args']['environment_id'] = $scope.uuid;


                mainFactory.postEnvironmentVariable().post(postData).$promise.then(function(response) {
                    $scope.showloading = false;

                    if (response.status == 1) {

                        $scope.openrcInfo = response.result;
                        toaster.pop({
                            type: 'success',
                            title: 'create success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.showEnvrionment = true;
                        getItemIdDetail();
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'faile',
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

            //reconstruc EnvInfo
            function rebuildEnvInfo() {
                $scope.postEnvInfo = {};
                for (var i = 0; i < $scope.envInfo.length; i++) {
                    $scope.postEnvInfo[$scope.envInfo[i].name] = $scope.envInfo[i].value;
                }

            }

            //buildtoEnvInfo
            function buildToEnvInfo(object) {
                $scope.envInfo=[];
                var tempKeyArray = Object.keys(object);

                for (var i = 0; i < tempKeyArray.length; i++) {
                    var tempkey = tempKeyArray[i];
                    var tempValue = object[tempKeyArray[i]];
                    var temp = {
                        name: tempkey,
                        value: tempValue
                    };
                    $scope.envInfo.push(temp);

                }

                console.log($scope.envInfo);
                console.log($scope.openrcInfo);
            }

            function uploadFiles($file, $invalidFiles) {
                $scope.openrcInfo = {};
                $scope.loadingOPENrc = true;

                $scope.displayOpenrcFile = $file;
                timeConstruct($scope.displayOpenrcFile.lastModified);
                Upload.upload({
                    url: Base_URL + '/api/v2/yardstick/openrcs',
                    data: { file: $file, 'environment_id': $scope.uuid, 'action': 'upload_openrc' }
                }).then(function(response) {

                    $scope.loadingOPENrc = false;
                    if (response.data.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'upload success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.openrcInfo = response.data.result;
                        getItemIdDetail();

                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'faile',
                            body: response.error_msg,
                            timeout: 3000
                        });
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

            function addEnvironment() {
                mainFactory.addEnvName().post({
                    'action': 'create_environment',
                    args: {
                        'name': $scope.baseElementInfo.name
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create name success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.uuid = response.result.uuid;
                        var path = $location.path();
                        path = path + $scope.uuid;
                        $location.url(path);
                        getItemIdDetail();
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

            function getItemIdDetail() {

                mainFactory.ItemDetail().get({
                    'envId': $scope.uuid
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.baseElementInfo = response.result.environment;


                        if ($scope.ifNew != 'true') {
                            $scope.baseElementInfo = response.result.environment;
                            if ($scope.baseElementInfo.openrc_id != null) {
                                getOpenrcDetail($scope.baseElementInfo.openrc_id);
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
                    $scope.openrcInfo = response.result;
                    buildToEnvInfo($scope.openrcInfo.openrc)
                }, function(response) {

                })
            }


            //getImgDetail
            function getImageDetail() {
                mainFactory.ImageDetail().get({
                    'image_id': $scope.baseElementInfo.image_id
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
            function getPodDetail() {
                mainFactory.podDeatil().get({
                    'podId': $scope.baseElementInfo.pod_id
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
            function getPodDetail(containerId) {
                mainFactory.containerDetail().get({
                    'containerId': containerId
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.podDetail = response.result.pod;
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

            $scope.goNext = function goNext() {
                $scope.path = $location.path();
                $scope.uuid = $scope.path.split('/').pop();
                $state.go('app.uploadImage', { uuid: $scope.uuid });
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

            $scope.deleteOpenRc = function deleteOpenRc() {
                mainFactory.deleteOpenrc().delete({ 'openrc': $scope.baseElementInfo.openrc_id }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete openrc success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getItemIdDetail();
                        $scope.openrcInfo = null;
                        $scope.envInfo = [];
                        $scope.displayOpenrcFile = null;
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
