'use strict';

angular.module('yardStickGui2App')
    .controller('TestcaseController', ['$scope', '$state', '$stateParams', 'mainFactory', 'Upload', 'toaster', 'ngDialog', '$loading',
        function($scope, $state, $stateParams, mainFactory, Upload, toaster, ngDialog, $loading) {


            init();
            $scope.loadingOPENrc = false;


            function init() {
                $scope.testcaselist = [];
                getTestcaseList();
                $scope.gotoDetail = gotoDetail;
                $scope.uploadFiles = uploadFiles;


            }

            function getTestcaseList() {
                $loading.start('key');
                mainFactory.getTestcaselist().get({

                }).$promise.then(function(response) {
                    $loading.finish('key');
                    if (response.status == 1) {
                        $scope.testcaselist = response.result;


                    }
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

            function gotoDetail(name) {
                $state.go('app.testcasedetail', { name: name });
            }


            function uploadFiles($file, $invalidFiles) {
                $scope.loadingOPENrc = true;

                $scope.displayOpenrcFile = $file;
                timeConstruct($scope.displayOpenrcFile.lastModified);
                Upload.upload({
                    url: Base_URL + '/api/v2/yardstick/testcases',
                    data: { file: $file, 'action': 'upload_case' }
                }).then(function(response) {

                    $scope.loadingOPENrc = false;
                    if (response.data.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'upload success',
                            body: 'you can go next step',
                            timeout: 3000
                        });



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

            $scope.deleteTestCase = function deleteTestCase() {
                mainFactory.deleteTestCase().delete({ 'caseName': $scope.deleteId }).$promise.then(function(response) {
                    if (response.status == 1) {
                        toaster.pop({
                            type: 'success',
                            title: 'delete Test Case success',
                            body: 'you can go next step',
                            timeout: 3000
                        });
                        ngDialog.close();
                        getTestcaseList();
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