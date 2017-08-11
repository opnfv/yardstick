'use strict';

angular.module('yardStickGui2App')
    .controller('MainCtrl', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog', '$localStorage', '$loading', '$interval',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog, $localStorage, $loading, $interval) {


            init();
            $scope.project = 0;
            $scope.showloading = false;
            $scope.showEnvrionment = false;
            $scope.loadingOPENrc = false;
            $scope.uuidEnv = null;
            $scope.showPod = null;
            $scope.showImage = null;
            $scope.showContainer = null;
            $scope.showNextOpenRc = null;
            $scope.showNextPod = 1;
            $scope.displayContainerInfo = [];
            $scope.containerList = [{ value: 'create_influxdb', name: "InfluxDB" }, { value: 'create_grafana', name: "Grafana" }]

            $scope.$on('$destroy', function() {
                $interval.cancel($scope.intervalImgae)
            });
            $scope.showImageStatus = 0;






            function init() {


                $scope.gotoProject = gotoProject;
                $scope.gotoEnvironment = gotoEnvironment;
                $scope.gotoTask = gotoTask;
                $scope.gotoExcute = gotoExcute;
                $scope.gotoReport = gotoReport;
                $scope.deleteEnvItem = deleteEnvItem;
                $scope.addInfo = addInfo;
                $scope.submitOpenRcFile = submitOpenRcFile;
                $scope.uploadFilesPod = uploadFilesPod;
                $scope.uploadFiles = uploadFiles;
                $scope.showEnvriomentStatus = showEnvriomentStatus;
                $scope.openEnvironmentDialog = openEnvironmentDialog;
                $scope.getEnvironmentList = getEnvironmentList;
                $scope.gotoDetail = gotoDetail;
                $scope.addEnvironment = addEnvironment;
                $scope.createContainer = createContainer;
                $scope.chooseResult = chooseResult;

                getEnvironmentList();

            }

            function gotoProject() {
                $scope.project = 1;
            }

            function gotoEnvironment() {
                $scope.project = 0;
            }

            function gotoTask() {
                $scope.project = 2;
            }

            function gotoExcute() {
                $scope.project = 3;

            }

            function gotoReport() {
                $scope.project = 4;
            }
            $scope.skipPod = function skipPod() {
                $scope.showContainer = 1;

            }
            $scope.skipContainer = function skipContainer() {
                getEnvironmentList();
                ngDialog.close();
            }

            $scope.goToImage = function goToImage() {
                getImageList();
                $scope.showImage = 1;
            }
            $scope.goToPod = function goToPod() {
                $scope.showPod = 1;
            }
            $scope.goToPodPrev = function goToPodPrev() {
                $scope.showImage = null;

            }
            $scope.skipPodPrev = function skipPodPrev() {
                $scope.showImage = 1;
                $scope.showPod = null;

            }
            $scope.skipContainerPrev = function skipContainerPrev() {
                $scope.showPod = 1;
                $scope.showContainer = null;
            }

            $scope.envInfo = [
                { name: 'OS_USERNAME', value: '' },
                { name: 'OS_PASSWORD', value: '' },
                { name: 'OS_TENANT_NAME', value: '' },
                { name: 'EXTERNAL_NETWORK', value: '' }
            ];


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
                postData.args["openrc"] = $scope.postEnvInfo;
                postData.args['environment_id'] = $scope.uuidEnv;
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
                        // $scope.showImage = response.status;
                        $scope.showNextOpenRc = 1;
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

            function uploadFiles($file, $invalidFiles) {
                $scope.openrcInfo = {};
                $scope.loadingOPENrc = true;
                $scope.displayOpenrcFile = $file;
                timeConstruct($scope.displayOpenrcFile.lastModified);
                Upload.upload({
                    url: Base_URL + '/api/v2/yardstick/openrcs',
                    data: { file: $file, 'environment_id': $scope.uuidEnv, 'action': 'upload_openrc' }
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

                        getItemIdDetailforOpenrc();
                        $scope.showNextOpenRc = 1;
                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'fail',
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

            //reconstruc EnvInfo
            function rebuildEnvInfo() {
                $scope.postEnvInfo = {};
                for (var i = 0; i < $scope.envInfo.length; i++) {
                    $scope.postEnvInfo[$scope.envInfo[i].name] = $scope.envInfo[i].value;
                }

            }
            function uploadFilesPod($file, $invalidFiles) {
                $scope.loadingOPENrc = true;

                $scope.displayPodFile = $file;
                timeConstruct($scope.displayPodFile.lastModified);
                Upload.upload({
                    url: Base_URL + '/api/v2/yardstick/pods',
                    data: { file: $file, 'environment_id': $scope.uuidEnv, 'action': 'upload_pod_file' }
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


                    } else {
                        toaster.pop({
                            type: 'error',
                            title: 'fail',
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

            //display environment
            function showEnvriomentStatus() {
                $scope.showEnvironment = true;
            }

            //open Environment dialog
            function openEnvironmentDialog() {
                $scope.showEnvrionment = false;
                $scope.loadingOPENrc = false;
                $scope.uuidEnv = null;
                $scope.showPod = null;
                $scope.showImage = null;
                $scope.showContainer = null;
                $scope.showNextOpenRc = null;
                $scope.showNextPod = 1;
                $scope.displayContainerInfo = [];

                $scope.displayPodFile = null;
                $scope.name = null;
                $scope.openrcInfo = null;
                $scope.envInfo = [
                    { name: 'OS_USERNAME', value: '' },
                    { name: 'OS_PASSWORD', value: '' },
                    { name: 'OS_TENANT_NAME', value: '' },
                    { name: 'EXTERNAL_NETWORK', value: '' }
                ];
                $scope.displayOpenrcFile = null;
                $scope.podData = null;
                $scope.displayContainerInfo = null;
                ngDialog.open({
                    preCloseCallback: function(value) {
                        getEnvironmentList();
                    },
                    template: 'views/modal/environmentDialog.html',
                    scope: $scope,
                    className: 'ngdialog-theme-default',
                    width: 950,
                    showClose: true,
                    closeByDocument: false
                })
            }

            function getEnvironmentList() {
                $loading.start('key');

                mainFactory.getEnvironmentList().get().$promise.then(function(response) {
                    $scope.environmentList = response.result.environments;
                    $loading.finish('key');

                }, function(error) {
                    $loading.finish('key');
                    toaster.pop({
                        type: 'error',
                        title: 'fail',
                        body: 'unknow error',
                        timeout: 3000
                    });

                })
            }

            //go to detail page
            function gotoDetail(ifNew, uuid) {

                $state.go('app.environmentDetail', { uuid: uuid, ifNew: ifNew });
            }


            function addEnvironment(name) {
                mainFactory.addEnvName().post({
                    'action': 'create_environment',
                    args: {
                        'name': name
                    }
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'create name success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        $scope.uuidEnv = response.result.uuid;
                        $scope.name = name;

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
                    $state.go('app.projectList');
                }
            $scope.displayContainerInfo = [];

            function createContainer(selectContainer) {

                $scope.showloading = true;
                mainFactory.runAcontainer().post({
                    'action': selectContainer.value,
                    'args': {
                        'environment_id': $scope.uuidEnv,
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
                        $scope.ifskipOrClose = 1;
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

            function getConDetail(id) {
                mainFactory.containerDetail().get({
                    'containerId': id
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        // $scope.podData = response.result;
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

            function chooseResult(name) {
                $scope.selectContainer = name;
            }

            function getItemIdDetail() {
                $scope.displayContainerInfo = [];
                mainFactory.ItemDetail().get({
                    'envId': $scope.uuidEnv
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

            $scope.yardstickImage = {
                'yardstick-image': {
                    'name': 'yardstick-image',
                    'description': '',
                    'status': 'N/A'
                },
                'Ubuntu-16.04': {
                    'name': 'Ubuntu-16.04',
                    'description': '',
                    'status': 'N/A'
                },
                'cirros-0.3.5': {
                    'name': 'cirros-0.3.5',
                    'description': '',
                    'status': 'N/A'
                }
            };

            $scope.selectImageList = [];

            $scope.selectImage = function(name){
                $scope.selectImageList.push(name);
            }

            $scope.unselectImage = function(name){
                var index = $scope.selectImageList.indexOf(name);
                $scope.selectImageList.splice(index, 1);
            }

            $scope.uploadImage = function() {
                $scope.imageStatus = 0;
                $scope.showImageStatus = 1;
                $scope.showloading = true;

                var updateImageTask = $interval(function(){
                    mainFactory.ImageList().get({}).$promise.then(function(response){
                        if(response.status == 1){
                            var isOk = true;
                            angular.forEach($scope.selectImageList, function(ele){
                                if(typeof(response.result.images[ele]) != 'undefined' && response.result.images[ele].status == 'ACTIVE'){
                                    $scope.yardstickImage[ele] = response.result.images[ele];
                                }else{
                                    isOk = false;
                                }
                            });
                            if(isOk){
                                $interval.cancel(updateImageTask);
                                $scope.imageStatus = 1;
                            }
                        }else{
                            mainFactory.errorHandler1(response);
                        }
                    }, function(response){
                        mainFactory.errorHandler2(response);
                    });
                }, 10000);

                angular.forEach($scope.selectImageList, function(ele){
                    mainFactory.uploadImage().post({
                        'action': 'load_image',
                        'args': {
                            'name': ele
                        }
                    }).$promise.then(function(response) {
                        if(response.status == 1){
                            $scope.showloading = false;
                            $scope.showNextPod = 1;
                        }else{
                            mainFactory.errorHandler1(response);
                        }
                    }, function(response) {
                        mainFactory.errorHandler2(response);
                    })
                });
            }

            function getImageList() {

                mainFactory.ImageList().get({}).$promise.then(function(response) {
                    if (response.status == 1) {
                        angular.forEach($scope.yardstickImage, function(value, key){
                            if(typeof(response.result.images[key]) != 'undefined'){
                                $scope.yardstickImage[key] = response.result.images[key];
                            }
                        });
                        $scope.imageStatus = response.result.status;
                    }else{
                        mainFactory.errorHandler1(response);
                    }
                }, function(response) {
                    mainFactory.errorHandler2(response);
                })
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

            $scope.deleteEnv = function deleteEnv() {
                mainFactory.deleteEnv().delete({ 'env_id': $scope.deleteId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete environment success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getEnvironmentList();
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






            function getItemIdDetailforOpenrc() {

                mainFactory.ItemDetail().get({
                    'envId': $scope.uuidEnv
                }).$promise.then(function(response) {
                    if (response.status == 1) {
                        $scope.baseElementInfo = response.result.environment;


                        if ($scope.ifNew != 'true') {
                            $scope.baseElementInfo = response.result.environment;
                            if ($scope.baseElementInfo.openrc_id != null) {
                                getOpenrcDetailForOpenrc($scope.baseElementInfo.openrc_id);
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
            function getOpenrcDetailForOpenrc(openrcId) {
                mainFactory.getEnvironmentDetail().get({
                    'openrc_id': openrcId
                }).$promise.then(function(response) {
                    $scope.openrcInfo = response.result;
                    buildToEnvInfoOpenrc($scope.openrcInfo.openrc)
                }, function(response) {
                    toaster.pop({
                        type: 'error',
                        title: 'error',
                        body: 'unknow error',
                        timeout: 3000
                    });
                })
            }

            //buildtoEnvInfo
            function buildToEnvInfoOpenrc(object) {
                var tempKeyArray = Object.keys(object);
                $scope.envInfo = [];


                for (var i = 0; i < tempKeyArray.length; i++) {
                    var tempkey = tempKeyArray[i];
                    var tempValue = object[tempKeyArray[i]];
                    var temp = {
                        name: tempkey,
                        value: tempValue
                    };
                    $scope.envInfo.push(temp);
                }
            }














        }
    ]);
